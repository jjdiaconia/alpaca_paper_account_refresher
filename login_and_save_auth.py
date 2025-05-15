#!/usr/bin/env python3
# record_auth_state.py

import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError

LOGIN_URL     = "https://app.alpaca.markets/login"
DASHBOARD_URL = "https://app.alpaca.markets/dashboard/overview"
OUTPUT_FILE   = Path("auth_state.json")
WAIT_SECONDS  = 300   # max time to wait for you to log in

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

def main():
    with sync_playwright() as pw:
        log.info("Starting Chromium (headed)...")
        browser = pw.chromium.launch(headless=False)
        ctx     = browser.new_context()
        page    = ctx.new_page()

        log.info(f"→ go to login page: {LOGIN_URL}")
        page.goto(LOGIN_URL)

        log.info("Please complete the login **manually** in the opened browser.")
        log.info(f"Waiting up to {WAIT_SECONDS}s for navigation to dashboard…")
        try:
            # block until the URL starts with DASHBOARD_URL
            page.wait_for_url(f"{DASHBOARD_URL}*", timeout=WAIT_SECONDS * 1000)
        except TimeoutError:
            log.error("Timed out waiting for dashboard URL. Exiting without saving.")
            browser.close()
            return

        log.info("Dashboard reached! Saving storage state to %s", OUTPUT_FILE)
        ctx.storage_state(path=str(OUTPUT_FILE))

        log.info("✅ auth_state.json written—now you can re-use it in your scripts.")
        browser.close()

if __name__ == "__main__":
    main()
