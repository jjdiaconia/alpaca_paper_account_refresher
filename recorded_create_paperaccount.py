import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="auth_state.json")
    page = context.new_page()
    page.goto("https://app.alpaca.markets/dashboard/overview")
    page.get_by_role("button", name="PAPER 2 PA3BYCSSI3BI").click()
    page.get_by_text("Open New Paper Account").click()
    page.locator("input[name=\"name\"]").click()
    page.locator("input[name=\"name\"]").fill("PAPER_ACCOUNT")
    page.get_by_role("textbox", name="$1 - $").click()
    page.get_by_role("textbox", name="$1 - $").fill("1000000")
    page.get_by_role("button", name="Submit").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
