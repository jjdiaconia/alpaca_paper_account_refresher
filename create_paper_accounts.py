#!/usr/bin/env python3
# create_and_validate_dummy_paper_accounts.py

import json
import logging
import os
import re
import sys
from pathlib import Path

import requests
from alpaca.trading.client import TradingClient

# ─── Configuration ───────────────────────────────────────────────────────────────
STATE_FILE      = Path("auth_state.json")
DASHBOARD_URL   = "https://app.alpaca.markets/dashboard/overview"
API_BASE        = "https://app.alpaca.markets"
CREATE_PATH     = "/internal/paper_accounts"
ACCESS_KEYS_FMT = "/internal/paper_accounts/{acct_id}/access_keys"

NUM_DUMMY       = int(os.getenv("NUM_DUMMY_ACCOUNTS", "2"))
STARTING_CASH   = int(os.getenv("STARTING_CASH", "1_000_000"))

# ─── Logging Setup ───────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def load_cookies(state_file: Path):
    if not state_file.exists():
        logger.error("Auth state file not found: %s", state_file)
        sys.exit(1)
    with open(state_file, "r") as f:
        st = json.load(f)
    return {c["name"]: c["value"] for c in st.get("cookies", [])}


def extract_csrf(session: requests.Session) -> str | None:
    resp = session.get(DASHBOARD_URL)
    if not resp.ok:
        logger.error("Failed to GET dashboard for CSRF: %d %s", resp.status_code, resp.text[:200])
        sys.exit(1)

    m = re.search(r"<meta\s+name=[\"']csrf-token[\"']\s+content=[\"']([^\"']+)[\"']", resp.text)
    if m:
        token = m.group(1)
        logger.debug("CSRF token extracted: %s", token)
        return token
    logger.warning("No <meta name=\"csrf-token\"> found in dashboard HTML")
    return None


def main():
    logger.info("Starting dummy paper-account creation (n=%d)", NUM_DUMMY)

    # load cookies & set up session
    cookies = load_cookies(STATE_FILE)
    session = requests.Session()
    session.cookies.update(cookies)

    # extract CSRF token and prepare headers
    csrf = extract_csrf(session)
    headers = {"Accept": "application/json, text/plain, */*"}
    if csrf:
        headers["X-CSRF-Token"] = csrf

    created_keys: list[tuple[str,str,str]] = []

    # 1) create each paper account + its access key
    for i in range(1, NUM_DUMMY + 1):
        name = f"DUMMY_PAPER_{i}"
        payload = {"name": name, "cash": STARTING_CASH}
        logger.info("Creating paper account %r", name)
        resp = session.post(API_BASE + CREATE_PATH, headers=headers, json=payload)
        if not resp.ok:
            logger.error("Account creation failed: %d %s", resp.status_code, resp.text[:200])
            continue

        acct = resp.json()
        acct_id = acct["paper_account_id"]
        logger.info("  → paper_account_id=%s", acct_id)

        # create access key
        ak_path = ACCESS_KEYS_FMT.format(acct_id=acct_id)
        logger.info("Creating access key for account %s", acct_id)
        ak_resp = session.post(API_BASE + ak_path, headers=headers)
        if not ak_resp.ok:
            logger.error("Access‐key creation failed: %d %s", ak_resp.status_code, ak_resp.text[:200])
            continue

        key = ak_resp.json()
        key_id     = key["id"]
        secret_key = key["secret"]
        logger.info("  → key_id=%s", key_id)

        created_keys.append((acct_id, key_id, secret_key))

    # 2) validate each via alpaca-py TradingClient
    logger.info("Validating %d key(s) with Alpaca SDK", len(created_keys))
    for acct_id, key_id, secret_key in created_keys:
        logger.info("Testing credentials for %s", acct_id)
        try:
            client = TradingClient(
                key_id,
                secret_key,
                paper=True
            )
            account = client.get_account()
            logger.info(
                "  ✓ validation succeeded: buying_power=%s, cash=%s",
                account.buying_power,
                account.cash
            )
        except Exception as e:
            logger.error("  ✗ validation failed for %s: %s", acct_id, e)

    logger.info("Done.")

if __name__ == "__main__":
    main()
