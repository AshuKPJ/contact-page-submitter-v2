# test_playwright.py - Save this as a separate file and run it
import asyncio
import sys


async def test_basic_browser():
    """Test if Playwright can launch a visible browser at all"""

    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")

    try:
        from playwright.async_api import async_playwright

        print("Playwright import successful")
    except ImportError as e:
        print(f"Playwright import failed: {e}")
        return

    # Set Windows event loop if needed
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        print("Set ProactorEventLoop for Windows")

    playwright = None
    browser = None

    try:
        print("Starting Playwright...")
        playwright = await async_playwright().start()
        print("Playwright started successfully")

        print("Launching browser in VISIBLE mode...")
        browser = await playwright.chromium.launch(
            headless=False,  # MUST be False for visible browser
            slow_mo=2000,  # 2 second delays
            args=["--start-maximized", "--no-sandbox", "--disable-dev-shm-usage"],
        )
        print("Browser should be launching now...")

        print("Creating new page...")
        page = await browser.new_page()

        print("Navigating to Google...")
        await page.goto("https://www.google.com")

        print("SUCCESS: If you can see a Google page, Playwright is working!")
        print("The browser window should be visible and maximized")
        print("Waiting 10 seconds before closing...")

        await asyncio.sleep(10)

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if browser:
            print("Closing browser...")
            await browser.close()
        if playwright:
            print("Stopping Playwright...")
            await playwright.stop()
        print("Test completed")


if __name__ == "__main__":
    asyncio.run(test_basic_browser())
