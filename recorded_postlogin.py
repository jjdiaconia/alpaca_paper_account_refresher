import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="auth_state.json")
    page = context.new_page()
    page.goto("https://app.alpaca.markets/dashboard/overview")
    page.get_by_role("button", name="PAPER 2 PA3ELRSS8CXD").click()
    page.get_by_text("PAPER 2$2.72PA3ELRSS8CXD0.00%").click()
    page.get_by_role("button", name="Delete Account").click()
    page.get_by_role("button", name="Delete", exact=True).click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
