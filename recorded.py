import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://app.alpaca.markets/account/login")
    page.get_by_role("textbox", name="me@example.com").dblclick()
    page.get_by_role("textbox", name="me@example.com").fill("joja5627@gmail.com")
    page.get_by_role("textbox", name="••••••••••••••••").dblclick()
    page.get_by_role("textbox", name="••••••••••••••••").fill("Cu112145@buffs")
    page.get_by_role("button", name="Continue").click()
    page.goto("https://app.alpaca.markets/dashboard/overview")

    # ---------------------
    context.storage_state(path="auth_state.json")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
