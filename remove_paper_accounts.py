#!/usr/bin/env python3
# remove_all_but_one_paper_account_requests.py

import json
import logging
import os
import re
import sys
from pathlib import Path

import requests

# ─── Configuration ─────────────────────────────────────────────────────────────
STATE_FILE     = Path("auth_state.json")
DASHBOARD_URL  = "https://app.alpaca.markets/dashboard/overview"
API_BASE       = "https://app.alpaca.markets"
LIST_PATH      = "/internal/paper_accounts"
DELETE_PATH    = "/internal/paper_accounts/{acct_id}"

# ─── Logging Setup ──────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def load_cookies(state_file: Path):
    """
    Load cookies from a Playwright storage_state.json.
    """
    if not state_file.exists():
        logger.error("Cannot find auth state file: %s", state_file)
        sys.exit(1)

    with open(state_file, "r") as f:
        state = json.load(f)

    cookies = {c["name"]: c["value"] for c in state.get("cookies", [])}
    return cookies


def main():
    logger.info("Starting paper-account cleanup via requests")

    # 1) load cookies
    cookies = load_cookies(STATE_FILE)
    session = requests.Session()
    session.cookies.update(cookies)

    # 2) fetch dashboard HTML to extract CSRF token
    logger.info("Fetching dashboard to extract CSRF token")
    dash_resp = session.get(DASHBOARD_URL)
    if not dash_resp.ok:
        logger.error("Dashboard GET failed: %d %s",
                     dash_resp.status_code, dash_resp.text[:200])
        sys.exit(1)

    match = re.search(
        r"<meta\s+name=[\"']csrf-token[\"']\s+content=[\"']([^\"']+)[\"']", 
        dash_resp.text
    )
    headers = {"Accept": "application/json, text/plain, */*"}
    if match:
        csrf = match.group(1)
        headers["X-CSRF-Token"] = csrf
        logger.debug("Extracted CSRF token: %s", csrf)
    else:
        logger.warning("No <meta name=\"csrf-token\"> found in dashboard")

    # 3) list all paper accounts
    list_url = API_BASE + LIST_PATH
    logger.info("GET %s", list_url)
    resp = session.get(list_url, headers=headers)
    if not resp.ok:
        logger.error("Failed to list paper accounts: %d %s",
                     resp.status_code, resp.text[:200])
        sys.exit(1)

    all_accounts = resp.json()
    active = [a for a in all_accounts if a.get("deleted_at") is None]
    logger.info("Found %d active paper account(s)", len(active))

    # 4) delete all but one
    if len(active) <= 1:
        logger.info("One or zero active accounts; nothing to delete.")
    else:
        to_delete = active[:-1]
        logger.info("Deleting %d account(s), preserving one", len(to_delete))
        for acct in to_delete:
            acct_id = acct["paper_account_id"]
            delete_url = API_BASE + DELETE_PATH.format(acct_id=acct_id)
            logger.info("DELETE %s", delete_url)
            d = session.delete(delete_url, headers=headers)
            if d.ok:
                logger.info("→ Successfully deleted %s", acct_id)
            else:
                logger.error(
                    "→ Failed to delete %s: %d %s",
                    acct_id, d.status_code, d.text[:200]
                )

    logger.info("Paper-account cleanup complete.")


if __name__ == "__main__":
    main()
