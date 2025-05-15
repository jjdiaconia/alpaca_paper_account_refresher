#!/usr/bin/env python3
# refresh_three_paper_accounts.py

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
LIST_PATH       = "/internal/paper_accounts"
CREATE_PATH     = "/internal/paper_accounts"
DELETE_PATH     = "/internal/paper_accounts/{acct_id}"
ACCESS_KEYS_FMT = "/internal/paper_accounts/{acct_id}/access_keys"

NUM_SLOTS       = int(os.getenv("NUM_SLOTS", "3"))
STARTING_CASH   = int(os.getenv("STARTING_CASH", "1_000_000"))

# ─── Logging Setup ───────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def load_cookies(state_file: Path) -> dict:
    if not state_file.exists():
        logger.error("Auth state file not found: %s", state_file)
        sys.exit(1)
    with open(state_file, "r") as f:
        st = json.load(f)
    return {c["name"]: c["value"] for c in st.get("cookies", [])}


def extract_csrf(session: requests.Session) -> str | None:
    r = session.get(DASHBOARD_URL)
    if not r.ok:
        logger.error("Dashboard GET failed: %d %s", r.status_code, r.text[:200])
        sys.exit(1)
    m = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']', r.text)
    if m:
        logger.debug("Extracted CSRF token")
        return m.group(1)
    logger.warning("No CSRF token meta-tag found")
    return None


def list_accounts(session: requests.Session, headers: dict) -> list[dict]:
    r = session.get(API_BASE + LIST_PATH, headers=headers)
    r.raise_for_status()
    return r.json()


def delete_account(session: requests.Session, headers: dict, acct_id: str) -> None:
    url = API_BASE + DELETE_PATH.format(acct_id=acct_id)
    r = session.delete(url, headers=headers)
    if r.ok:
        logger.info("Deleted %s", acct_id)
    else:
        logger.error("Failed delete %s: %d %s", acct_id, r.status_code, r.text[:200])


def create_account(session: requests.Session, headers: dict, name: str) -> str:
    r = session.post(API_BASE + CREATE_PATH, headers=headers,
                     json={"name": name, "cash": STARTING_CASH})
    r.raise_for_status()
    acct_id = r.json()["paper_account_id"]
    logger.info("Created %s → %s", name, acct_id)
    return acct_id


def create_access_key(session: requests.Session, headers: dict, acct_id: str) -> tuple[str,str]:
    url = API_BASE + ACCESS_KEYS_FMT.format(acct_id=acct_id)
    r = session.post(url, headers=headers)
    r.raise_for_status()
    key = r.json()
    logger.info("  ↳ key_id=%s", key["id"])
    return key["id"], key["secret"]


def validate_key(key_id: str, secret: str) -> None:
    client = TradingClient(key_id, secret, paper=True)
    acct = client.get_account()
    logger.info("    ✔ validation succeeded: cash=%s buying_power=%s",
                acct.cash, acct.buying_power)


def main():
    logger.info("Refreshing %d paper accounts…", NUM_SLOTS)

    # prepare session + headers
    cookies = load_cookies(STATE_FILE)
    session = requests.Session()
    session.cookies.update(cookies)
    csrf = extract_csrf(session)
    headers = {"Accept": "application/json, text/plain, */*"}
    if csrf:
        headers["X-CSRF-Token"] = csrf

    existing = list_accounts(session, headers)

    # we'll collect (slot, key_id, secret) here
    results: list[tuple[int,str,str]] = []

    for i in range(1, NUM_SLOTS+1):
        name = f"DUMMY_PAPER_{i}"
        # delete old
        for acct in existing:
            if acct.get("name") == name and acct.get("deleted_at") is None:
                delete_account(session, headers, acct["paper_account_id"])
                break

        # recreate + key + validate
        acct_id = create_account(session, headers, name)
        key_id, secret = create_access_key(session, headers, acct_id)
        try:
            validate_key(key_id, secret)
        except Exception as e:
            logger.error("    ✗ validation failed: %s", e)

        results.append((i, key_id, secret))

    # --- finally, emit your constants block ---
    print("\n# ─── Copy these into your constants.py ──────────────────────────────")
    for slot, key, secret in results:
        print(f'PAPER{slot}_API_KEY    = "{key}"')
        print(f'PAPER{slot}_API_SECRET = "{secret}"')
        print()

    logger.info("Done.")


if __name__ == "__main__":
    main()
