#!/usr/bin/env python3
"""
Live GUI Test for Shadowrun Interface
"""
import pytest
from playwright.sync_api import sync_playwright
import time

def test_shadowrun_interface_basic():
    """Basic GUI test for Shadowrun Interface."""
    
    print("🎮 Testing Shadowrun Interface GUI...")
    
    with sync_playwright() as p:
        # Launch browser (visible for demonstration)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        try:
            # Navigate to app
            print("🌐 Loading Shadowrun Interface...")
            page.goto("http://localhost:3000")
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Take screenshot
            page.screenshot(path="shadowrun_test.png")
            print("📸 Screenshot saved: shadowrun_test.png")
            
            # Check title
            title = page.title()
            print(f"📋 Page title: {title}")
            
            # Count elements
            buttons = page.query_selector_all("button")
            links = page.query_selector_all("a")
            inputs = page.query_selector_all("input")
            
            print(f"🔢 Found {len(buttons)} buttons, {len(links)} links, {len(inputs)} inputs")
            
            # Test responsiveness
            page.set_viewport_size({"width": 375, "height": 667})
            page.screenshot(path="shadowrun_mobile.png")
            print("📱 Mobile view captured")
            
            page.set_viewport_size({"width": 1200, "height": 800})
            page.screenshot(path="shadowrun_desktop.png")
            print("🖥️ Desktop view captured")
            
            print("✅ Basic GUI test completed successfully!")
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            page.screenshot(path="shadowrun_error.png")
            raise
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_shadowrun_interface_basic() 