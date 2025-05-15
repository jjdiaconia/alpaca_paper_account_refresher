# example.py
import os
import time
from playwright.sync_api import sync_playwright

# ⚠️ Put your Alpaca creds in env vars (DON’T hard-code in real code!)
ALPACA_EMAIL    = os.getenv("ALPACA_EMAIL", "joja5627@gmail.com")
ALPACA_PASSWORD = os.getenv("ALPACA_PASSWORD", "Cu112145@buffs")


def login(page):
    page.goto("https://app.alpaca.markets/login")
    page.fill('input[name="username"]', ALPACA_EMAIL)
    page.fill('input[name="password"]', ALPACA_PASSWORD)
    page.click('button[type="submit"]')
    # wait for redirect to dashboard
    page.wait_for_url("https://app.alpaca.markets/dashboard/overview")
    print("✅ Logged in")


def create_paper_account(page) -> str:
    # click the “New Paper Account” button
    page.click("text=New Paper Account")
    # once it navigates, grab the new account ID from URL
    page.wait_for_url("**/dashboard/overview/*")
    new_url = page.url
    account_id = new_url.rstrip("/").split("/")[-1]
    print(f"✅ Created paper account: {account_id}")
    return account_id


def delete_paper_account(page, account_id: str):
    # navigate into that account’s detail page
    page.goto(f"https://app.alpaca.markets/dashboard/overview/{account_id}")
    # click Delete → Confirm
    page.click("text=Delete Account")
    page.click("text=Confirm")
    # give it a moment to disappear / refresh
    time.sleep(2)
    print(f"✅ Deleted paper account: {account_id}")


def main():
    with sync_playwright() as p:
        # launch non-headless so you can watch it; set headless=True to hide UI
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        login(page)
        acct = create_paper_account(page)
        # optional: wait or verify it's listed
        delete_paper_account(page, acct)

        browser.close()


if __name__ == "__main__":
    main()
