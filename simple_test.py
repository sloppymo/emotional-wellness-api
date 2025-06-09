from playwright.sync_api import sync_playwright
import time

print("🎮 SHADOWRUN GUI TEST - STARTING...")

with sync_playwright() as p:
    print("🚀 Launching browser (you should see a window open)...")
    browser = p.chromium.launch(headless=False, slow_mo=2000)
    page = browser.new_page()
    
    print("🌐 Loading your Shadowrun Interface...")
    page.goto("http://localhost:3000")
    page.wait_for_load_state("networkidle")
    
    title = page.title()
    print(f"📋 Page loaded successfully: {title}")
    
    buttons = len(page.query_selector_all("button"))
    print(f"🔘 Found {buttons} interactive buttons")
    
    print("📸 Taking screenshot...")
    page.screenshot(path="shadowrun_demo.png")
    
    print("⏰ Keeping browser open for 10 seconds so you can see it...")
    time.sleep(10)
    
    browser.close()
    print("✅ Test completed! Browser closed.") 