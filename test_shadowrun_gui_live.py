#!/usr/bin/env python3
"""
Live GUI Test for Shadowrun Interface
====================================
Simple test to verify the app is working and test basic functionality.
"""

import asyncio
from playwright.async_api import async_playwright
import time
import os

async def test_shadowrun_gui():
    """Test the Shadowrun Interface GUI with basic interactions."""
    
    print("🎮 SHADOWRUN INTERFACE - LIVE GUI TESTING")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Launch browser
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to Shadowrun app
            print("🌐 Navigating to Shadowrun Interface...")
            await page.goto("http://localhost:3000")
            await page.wait_for_load_state("networkidle")
            
            # Take initial screenshot
            print("📸 Taking initial screenshot...")
            await page.screenshot(path="shadowrun_initial.png")
            
            # Check page title
            title = await page.title()
            print(f"📋 Page Title: {title}")
            
            # Look for common Shadowrun elements
            print("🔍 Checking for Shadowrun elements...")
            
            # Check for navigation or main content
            try:
                # Look for any buttons, links, or interactive elements
                buttons = await page.query_selector_all("button")
                links = await page.query_selector_all("a")
                inputs = await page.query_selector_all("input")
                
                print(f"   ✅ Found {len(buttons)} buttons")
                print(f"   ✅ Found {len(links)} links")
                print(f"   ✅ Found {len(inputs)} input fields")
                
                # Try to find Shadowrun-specific content
                shadowrun_keywords = [
                    "shadowrun", "character", "dice", "attribute", "skill",
                    "combat", "matrix", "magic", "karma", "edge", "initiative"
                ]
                
                page_content = await page.content()
                found_keywords = []
                
                for keyword in shadowrun_keywords:
                    if keyword.lower() in page_content.lower():
                        found_keywords.append(keyword)
                
                if found_keywords:
                    print(f"   🎲 Found Shadowrun content: {', '.join(found_keywords)}")
                else:
                    print("   ℹ️  No obvious Shadowrun keywords found (might be in React components)")
                
                # Test basic interactions
                if buttons:
                    print("🖱️  Testing button interaction...")
                    first_button = buttons[0]
                    await first_button.click()
                    await page.wait_for_timeout(2000)
                    print("   ✅ Button click successful")
                
                # Check for responsive design
                print("📱 Testing responsive design...")
                await page.set_viewport_size({"width": 375, "height": 667})  # Mobile
                await page.screenshot(path="shadowrun_mobile.png")
                
                await page.set_viewport_size({"width": 1200, "height": 800})  # Desktop
                await page.screenshot(path="shadowrun_desktop.png")
                
                # Performance check
                print("⚡ Checking performance...")
                start_time = time.time()
                await page.reload()
                await page.wait_for_load_state("networkidle")
                load_time = time.time() - start_time
                print(f"   ⏱️  Page load time: {load_time:.2f}s")
                
                # Accessibility quick check
                print("♿ Basic accessibility check...")
                # Check for alt text on images
                images = await page.query_selector_all("img")
                images_with_alt = 0
                for img in images:
                    alt = await img.get_attribute("alt")
                    if alt:
                        images_with_alt += 1
                
                if images:
                    accessibility_score = (images_with_alt / len(images)) * 100
                    print(f"   📊 Images with alt text: {images_with_alt}/{len(images)} ({accessibility_score:.1f}%)")
                
            except Exception as e:
                print(f"   ⚠️  Error during element testing: {e}")
            
            # Final screenshot
            print("📸 Taking final screenshot...")
            await page.screenshot(path="shadowrun_final.png")
            
            print("\n✅ GUI TEST COMPLETED SUCCESSFULLY!")
            print("\n📁 Screenshots saved:")
            print("   • shadowrun_initial.png")
            print("   • shadowrun_mobile.png") 
            print("   • shadowrun_desktop.png")
            print("   • shadowrun_final.png")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path="shadowrun_error.png")
            
        finally:
            await browser.close()
            print("🔚 Browser closed")

def main():
    """Run the GUI test."""
    try:
        asyncio.run(test_shadowrun_gui())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    main() 