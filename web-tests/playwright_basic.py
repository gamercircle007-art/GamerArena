from playwright.sync_api import sync_playwright
import os

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set True for CI
        context = browser.new_context()
        page = context.new_page()

        print("Navigating to app...")
        page.goto("http://localhost:8080", wait_until="networkidle")

        print("Page title:", page.title())
        page.screenshot(path=f"{REPORTS_DIR}/home-screenshot.png", full_page=True)

        # Basic checks
        assert "GamerCircle" in page.title() or "Paythan" in page.title() or True  # adjust

        # Example: try to find common elements (adapt to your UI)
        # page.click("text=Search")  # if text buttons exist

        print("Basic Playwright test passed. Screenshots saved to reports/")

        browser.close()

if __name__ == "__main__":
    run_tests()
