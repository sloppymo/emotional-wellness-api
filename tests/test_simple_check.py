"""
Simple test to verify the Shadowrun Interface testing environment.
"""

import pytest


def test_simple():
    """Simple test to verify pytest is working."""
    assert True


def test_dependencies():
    """Test that required dependencies are available."""
    try:
        import playwright
        import numpy
        import PIL
        print("✅ All dependencies are available!")
        assert True
    except ImportError as e:
        pytest.fail(f"Missing dependency: {e}")


def test_directories():
    """Test that test artifact directories exist."""
    import os
    from pathlib import Path
    
    artifacts_dir = Path("test_artifacts")
    screenshots_dir = artifacts_dir / "screenshots"
    reports_dir = artifacts_dir / "reports"
    
    assert artifacts_dir.exists(), "test_artifacts directory should exist"
    assert screenshots_dir.exists(), "screenshots directory should exist"
    assert reports_dir.exists(), "reports directory should exist"
    
    print(f"✅ Test directories are set up correctly at {artifacts_dir.absolute()}")


@pytest.mark.asyncio
async def test_playwright_basic():
    """Test that Playwright can launch a browser."""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to a simple page
        await page.goto("data:text/html,<html><body><h1>Test Page</h1></body></html>")
        
        # Check title
        title = await page.title()
        assert title == ""  # Data URLs don't have titles
        
        # Check that we can find elements
        h1 = await page.query_selector("h1")
        assert h1 is not None
        
        text = await h1.inner_text()
        assert text == "Test Page"
        
        await browser.close()
        
    print("✅ Playwright is working correctly!") 