# test_automation_imports.py
"""Test script to verify all automation components import correctly."""

import sys
import traceback


def test_imports():
    """Test all automation component imports."""

    print("Testing automation component imports...")

    try:
        # Test core automation imports
        print("✓ Testing browser automation...")
        from app.workers.automation.browser_automation import BrowserAutomation

        print("✓ Testing popup handler...")
        from app.workers.automation.popup_handler import PopupHandler

        print("✓ Testing adaptive field mapper...")
        from app.workers.automation.adaptive_field_mapper import AdaptiveFieldMapper

        print("✓ Testing form components...")
        from app.workers.automation.form_detector import FormDetector
        from app.workers.automation.form_filler import FormFiller
        from app.workers.automation.form_submitter import FormSubmitter

        print("✓ Testing other components...")
        from app.workers.automation.page_navigator import PageNavigator
        from app.workers.automation.email_extractor import EmailExtractor
        from app.workers.automation.success_detector import SuccessDetector
        from app.workers.automation.captcha_handler import CaptchaHandler

        print("✓ Testing automation controller...")
        from app.workers.automation import AutomationController

        print("✅ All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"Missing module: {e.name if hasattr(e, 'name') else 'unknown'}")
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return False


def test_basic_initialization():
    """Test basic component initialization."""

    try:
        print("\n🔧 Testing component initialization...")

        # Test AutomationController initialization
        from app.workers.automation import AutomationController

        controller = AutomationController(user_id="test", campaign_id="test")
        print("✓ AutomationController initialized")

        # Test PopupHandler initialization
        from app.workers.automation.popup_handler import PopupHandler

        popup_handler = PopupHandler(user_id="test", campaign_id="test")
        print("✓ PopupHandler initialized")

        # Test AdaptiveFieldMapper initialization
        from app.workers.automation.adaptive_field_mapper import AdaptiveFieldMapper

        field_mapper = AdaptiveFieldMapper(user_id="test", campaign_id="test")
        print("✓ AdaptiveFieldMapper initialized")

        print("✅ All components initialized successfully!")
        return True

    except Exception as e:
        print(f"❌ Initialization error: {e}")
        traceback.print_exc()
        return False


def test_playwright_availability():
    """Test if Playwright is available."""

    try:
        print("\n🎭 Testing Playwright availability...")

        from playwright.async_api import async_playwright

        print("✓ Playwright import successful")

        # Test if browsers are installed
        import subprocess

        result = subprocess.run(
            ["playwright", "install", "--dry-run"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✓ Playwright browsers available")
        else:
            print("⚠️  Playwright browsers may need installation")
            print("Run: playwright install chromium")

        return True

    except ImportError:
        print("❌ Playwright not installed")
        print("Install with: pip install playwright")
        return False

    except Exception as e:
        print(f"❌ Playwright error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Automation Components Test Suite")
    print("=" * 50)

    success = True

    # Run tests
    success &= test_imports()
    success &= test_basic_initialization()
    success &= test_playwright_availability()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Automation system should work.")
    else:
        print("💥 Some tests failed. Check the errors above.")
        sys.exit(1)
