#!/usr/bin/env python3
"""
Shadowrun Interface GUI Test
"""
from playwright.sync_api import sync_playwright

def main():
    print("🎮 SHADOWRUN INTERFACE GUI TEST")
    print("=" * 40)
    
    with sync_playwright() as playwright:
        # Launch browser with visible window
        browser = playwright.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            print("🌐 Navigating to http://localhost:3000...")
            page.goto("http://localhost:3000", timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # Get page info
            title = page.title()
            print(f"📋 Page Title: {title}")
            
            # Count elements
            buttons = page.query_selector_all("button")
            links = page.query_selector_all("a") 
            inputs = page.query_selector_all("input")
            divs = page.query_selector_all("div")
            
            print(f"🔢 Element Count:")
            print(f"   • {len(buttons)} buttons")
            print(f"   • {len(links)} links")
            print(f"   • {len(inputs)} inputs")
            print(f"   • {len(divs)} divs")
            
            # Take screenshots
            page.screenshot(path="shadowrun_desktop.png")
            print("📸 Desktop screenshot saved: shadowrun_desktop.png")
            
            # Test mobile view
            page.set_viewport_size({"width": 375, "height": 667})
            page.screenshot(path="shadowrun_mobile.png")
            print("📱 Mobile screenshot saved: shadowrun_mobile.png")
            
            # Look for Shadowrun-specific content
            content = page.content()
            shadowrun_terms = ["shadowrun", "character", "dice", "attribute", "skill", "initiative"]
            found_terms = [term for term in shadowrun_terms if term.lower() in content.lower()]
            
            if found_terms:
                print(f"🎲 Found Shadowrun content: {', '.join(found_terms)}")
            else:
                print("ℹ️  No Shadowrun-specific terms found in page content")
            
            # Test basic interaction
            if buttons:
                print("🖱️  Testing button interaction...")
                buttons[0].click()
                page.wait_for_timeout(2000)
                print("✅ Button click successful")
            
            print("✅ GUI test completed successfully!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(path="shadowrun_error.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    main() 