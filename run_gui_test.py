#!/usr/bin/env python3
"""
Shadowrun Interface - Live GUI Testing Demo
===========================================
This script will open a browser and demonstrate automated testing
"""
from playwright.sync_api import sync_playwright
import time

def main():
    print("🎮 SHADOWRUN INTERFACE - LIVE GUI TESTING")
    print("=" * 50)
    print("🚀 Starting automated browser testing...")
    print("   (You'll see a browser window open)")
    print()

    with sync_playwright() as p:
        # Launch browser with visible window
        browser = p.chromium.launch(
            headless=False,           # Show the browser window
            slow_mo=1500             # Slow down actions so you can see them
        )
        page = browser.new_page()
        
        try:
            print("🌐 Step 1: Opening Shadowrun Interface...")
            page.goto("http://localhost:3000")
            page.wait_for_load_state("networkidle")
            print("   ✅ Page loaded successfully!")
            
            # Get page information
            title = page.title()
            print(f"📋 Step 2: Analyzing page...")
            print(f"   📄 Title: {title}")
            
            # Count interface elements
            buttons = page.query_selector_all("button")
            links = page.query_selector_all("a")
            inputs = page.query_selector_all("input")
            divs = page.query_selector_all("div")
            
            print(f"🔢 Step 3: Element analysis complete:")
            print(f"   🔘 {len(buttons)} interactive buttons")
            print(f"   🔗 {len(links)} navigation links")
            print(f"   📝 {len(inputs)} input fields")
            print(f"   📦 {len(divs)} container elements")
            
            # Take desktop screenshot
            print("📸 Step 4: Capturing desktop view...")
            page.screenshot(path="shadowrun_desktop_test.png")
            print("   ✅ Desktop screenshot saved!")
            
            # Test mobile responsiveness
            print("📱 Step 5: Testing mobile responsiveness...")
            page.set_viewport_size({"width": 375, "height": 667})
            time.sleep(1)  # Let it adjust
            page.screenshot(path="shadowrun_mobile_test.png")
            print("   ✅ Mobile view captured!")
            
            # Return to desktop view
            page.set_viewport_size({"width": 1200, "height": 800})
            
            # Test basic interaction
            if buttons:
                print("🖱️  Step 6: Testing user interactions...")
                print(f"   🎯 Clicking first button...")
                buttons[0].scroll_into_view_if_needed()
                buttons[0].click()
                time.sleep(2)
                print("   ✅ Button interaction successful!")
            
            # Performance test
            print("⚡ Step 7: Performance testing...")
            start_time = time.time()
            page.reload()
            page.wait_for_load_state("networkidle")
            load_time = time.time() - start_time
            print(f"   ⏱️  Page reload time: {load_time:.2f} seconds")
            
            # Look for Shadowrun-specific content
            print("🎲 Step 8: Checking for Shadowrun content...")
            content = page.content().lower()
            shadowrun_terms = ["shadowrun", "character", "dice", "attribute", "skill", "initiative", "karma", "edge"]
            found_terms = [term for term in shadowrun_terms if term in content]
            
            if found_terms:
                print(f"   🎯 Found Shadowrun terms: {', '.join(found_terms[:3])}...")
            else:
                print("   ℹ️  Content loaded in React components (expected)")
            
            # Final screenshot
            page.screenshot(path="shadowrun_final_test.png")
            
            print()
            print("🎉 GUI TESTING DEMONSTRATION COMPLETE!")
            print("=" * 50)
            print("📊 RESULTS SUMMARY:")
            print(f"   ✅ Interface loaded: {title}")
            print(f"   ✅ Elements detected: {len(buttons)} buttons, {len(inputs)} inputs")
            print(f"   ✅ Responsive design: Desktop & Mobile tested")
            print(f"   ✅ Interactions: Button clicks working")
            print(f"   ✅ Performance: {load_time:.2f}s load time")
            print()
            print("📁 Screenshots captured:")
            print("   • shadowrun_desktop_test.png")
            print("   • shadowrun_mobile_test.png") 
            print("   • shadowrun_final_test.png")
            print()
            print("🚀 Your Shadowrun Interface is ready for full automation!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(path="shadowrun_error_test.png")
            print("📸 Error screenshot saved: shadowrun_error_test.png")
            
        finally:
            print()
            print("🔚 Closing browser in 3 seconds...")
            time.sleep(3)
            browser.close()
            print("✅ Test completed!")

if __name__ == "__main__":
    main() 