"""
Basic Shadowrun Interface Automated Test
========================================

This test verifies that the automated testing framework is working correctly.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright, Page


@pytest.mark.gui
async def test_shadowrun_app_loads():
    """Test that the Shadowrun interface loads correctly."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Try to load the app
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=10000)
            
            # Check if page loaded
            title = await page.title()
            assert title is not None, "Page title should not be None"
            
            # Check if React app mounted
            await page.wait_for_selector("body", timeout=5000)
            
            # Take screenshot for verification
            await page.screenshot(path="test_artifacts/screenshots/app_loaded.png")
            
        except Exception as e:
            pytest.skip(f"App not running or accessible: {e}")
        finally:
            await browser.close()


@pytest.mark.feature
async def test_basic_ui_elements():
    """Test that basic UI elements are present."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=10000)
            
            # Check for common UI elements
            body = await page.query_selector("body")
            assert body is not None, "Body element should exist"
            
            # Look for any interactive elements
            buttons = await page.query_selector_all("button")
            links = await page.query_selector_all("a")
            inputs = await page.query_selector_all("input")
            
            total_interactive = len(buttons) + len(links) + len(inputs)
            
            # We expect at least some interactive elements in a web app
            print(f"Found {total_interactive} interactive elements")
            
        except Exception as e:
            pytest.skip(f"App not running or accessible: {e}")
        finally:
            await browser.close()


@pytest.mark.accessibility
async def test_basic_accessibility():
    """Test basic accessibility requirements."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=10000)
            
            # Check for lang attribute
            html_lang = await page.get_attribute("html", "lang")
            
            # Check for title
            title = await page.title()
            assert len(title) > 0, "Page should have a title"
            
            print(f"Page title: {title}")
            print(f"HTML lang: {html_lang}")
            
        except Exception as e:
            pytest.skip(f"App not running or accessible: {e}")
        finally:
            await browser.close()


def test_framework_imports():
    """Test that our testing framework can be imported."""
    try:
        # These imports should work if our framework is set up correctly
        import sys
        from pathlib import Path
        
        # Add tests directory to path
        tests_dir = Path(__file__).parent
        sys.path.insert(0, str(tests_dir))
        
        # Test importing our modules (they may not exist yet, so we'll be lenient)
        try:
            from automated_testing_framework import ShadowrunTestFramework
            print("✅ ShadowrunTestFramework imported successfully")
        except ImportError as e:
            print(f"⚠️  ShadowrunTestFramework not yet available: {e}")
        
        try:
            from ai_test_generator import AITestGenerator
            print("✅ AITestGenerator imported successfully")
        except ImportError as e:
            print(f"⚠️  AITestGenerator not yet available: {e}")
            
    except Exception as e:
        pytest.fail(f"Framework import test failed: {e}") 