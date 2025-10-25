"""
Debug script to examine pagination structure
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
# chrome_options.add_argument('--headless')  # Run with visible browser to see what's happening
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(10)

try:
    print("Loading marketplace...")
    driver.get("https://www.phygitals.com/marketplace")
    time.sleep(8)
    
    print("\n" + "="*70)
    print("EXAMINING PAGINATION ELEMENTS")
    print("="*70)
    
    # Strategy 1: Find ALL buttons
    print("\n1. ALL BUTTONS ON PAGE:")
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    print(f"   Total buttons found: {len(buttons)}")
    
    for i, btn in enumerate(buttons[:30], 1):  # Show first 30 buttons
        try:
            text = btn.text.strip()
            classes = btn.get_attribute('class')
            aria_label = btn.get_attribute('aria-label')
            is_displayed = btn.is_displayed()
            is_enabled = btn.is_enabled()
            
            if any(word in text.lower() for word in ['next', 'previous', 'page']) or \
               (aria_label and any(word in aria_label.lower() for word in ['next', 'previous', 'page'])) or \
               text.isdigit():
                print(f"   {i}. Text: '{text}' | Class: '{classes}' | Aria: '{aria_label}' | Visible: {is_displayed} | Enabled: {is_enabled}")
        except:
            pass
    
    # Strategy 2: Find navigation elements
    print("\n2. NAVIGATION ELEMENTS:")
    navs = driver.find_elements(By.TAG_NAME, 'nav')
    print(f"   Found {len(navs)} <nav> elements")
    
    for i, nav in enumerate(navs, 1):
        try:
            classes = nav.get_attribute('class')
            inner_html = nav.get_attribute('innerHTML')[:200]
            print(f"   Nav {i}: Class='{classes}'")
            if 'button' in inner_html.lower() or 'page' in inner_html.lower():
                print(f"      Contains: {inner_html[:100]}...")
        except:
            pass
    
    # Strategy 3: Search for elements containing pagination-related text
    print("\n3. ELEMENTS WITH 'NEXT' TEXT:")
    try:
        next_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Next') or contains(text(), 'next')]")
        print(f"   Found {len(next_elements)} elements with 'Next' text")
        for elem in next_elements[:5]:
            print(f"   - Tag: {elem.tag_name} | Text: '{elem.text}' | Displayed: {elem.is_displayed()}")
    except:
        pass
    
    # Strategy 4: Look for arrow symbols
    print("\n4. ELEMENTS WITH ARROW SYMBOLS:")
    try:
        arrow_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '→') or contains(text(), '>') or contains(text(), '»')]")
        print(f"   Found {len(arrow_elements)} elements with arrows")
        for elem in arrow_elements[:5]:
            print(f"   - Tag: {elem.tag_name} | Text: '{elem.text}' | Class: {elem.get_attribute('class')}")
    except:
        pass
    
    # Strategy 5: Look for pagination classes
    print("\n5. COMMON PAGINATION CLASSES:")
    pagination_classes = ['pagination', 'pager', 'page-nav', 'paginate']
    for cls in pagination_classes:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, f'[class*="{cls}"]')
            if elements:
                print(f"   Found {len(elements)} elements with class containing '{cls}'")
                for elem in elements[:2]:
                    print(f"      - {elem.tag_name} | Class: {elem.get_attribute('class')}")
        except:
            pass
    
    # Strategy 6: Save page source for manual inspection
    print("\n6. SAVING PAGE SOURCE:")
    with open('debug_pagination_page.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("   Saved to: debug_pagination_page.html")
    
    # Strategy 7: Try to click page 2 button
    print("\n7. ATTEMPTING TO FIND PAGE 2 BUTTON:")
    try:
        # Look for button with text "2"
        page2_buttons = driver.find_elements(By.XPATH, "//button[text()='2' or contains(text(), '2')]")
        print(f"   Found {len(page2_buttons)} buttons with '2'")
        
        for btn in page2_buttons:
            print(f"   - Text: '{btn.text}' | Class: '{btn.get_attribute('class')}' | Displayed: {btn.is_displayed()} | Enabled: {btn.is_enabled()}")
            
            if btn.is_displayed() and btn.is_enabled():
                print("\n   ✓ Found valid page 2 button! Attempting to click...")
                btn.click()
                time.sleep(5)
                print("   ✓ Successfully clicked page 2!")
                
                # Check if we're on page 2
                page_source = driver.page_source
                if "page" in page_source.lower():
                    print("   ✓ Page changed!")
                
                # Try to find cards again
                card_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
                print(f"   ✓ Found {len(card_links)} card links on page 2")
                break
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*70)
    print("Press Enter to close browser...")
    input()
    
except Exception as e:
    print(f"\nError: {e}")
finally:
    driver.quit()

