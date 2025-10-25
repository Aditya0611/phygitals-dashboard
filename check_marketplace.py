"""
Quick diagnostic to check marketplace page structure
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re

def check_marketplace():
    print("Checking marketplace page structure...\n")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
    try:
        url = "https://www.phygitals.com/marketplace"
        print(f"Loading: {url}")
        driver.get(url)
        time.sleep(8)
        
        # Get page info
        print(f"Page title: {driver.title}")
        print(f"Page height: {driver.execute_script('return document.body.scrollHeight')}")
        
        # Check for card links
        print("\n" + "="*70)
        print("CHECKING CARD LINKS")
        print("="*70)
        
        # Method 1: XPath
        xpath_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
        print(f"\nXPath found: {len(xpath_links)} links with '/card/'")
        
        # Method 2: CSS
        css_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/card/"]')
        print(f"CSS found: {len(css_links)} links with '/card/'")
        
        # Method 3: All links
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        card_links = [l for l in all_links if l.get_attribute('href') and '/card/' in l.get_attribute('href')]
        print(f"All links scan: {len(card_links)} card links")
        
        # Show first 5 URLs
        print("\nFirst 5 card URLs:")
        unique_urls = set()
        for link in card_links[:20]:
            url = link.get_attribute('href')
            if url and url not in unique_urls:
                unique_urls.add(url)
                if len(unique_urls) <= 5:
                    print(f"  {len(unique_urls)}. {url}")
        
        print(f"\nTotal unique URLs found: {len(unique_urls)}")
        
        # Check for pagination elements
        print("\n" + "="*70)
        print("CHECKING PAGINATION/FILTERS")
        print("="*70)
        
        # Look for buttons
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        print(f"\nFound {len(buttons)} buttons on page")
        button_texts = []
        for btn in buttons[:20]:
            try:
                text = btn.text.strip()
                if text and len(text) < 50:
                    button_texts.append(text)
            except:
                pass
        if button_texts:
            print("Button texts:", ', '.join(button_texts[:10]))
        
        # Look for select/dropdown elements
        selects = driver.find_elements(By.TAG_NAME, 'select')
        print(f"\nFound {len(selects)} select/dropdown elements")
        
        # Look for input fields (filters)
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f"Found {len(inputs)} input fields")
        
        # Check for "Load More" or similar text
        page_text = driver.page_source.lower()
        if 'load more' in page_text:
            print("\n✓ Found 'load more' in page")
        if 'show more' in page_text:
            print("✓ Found 'show more' in page")
        if 'pagination' in page_text:
            print("✓ Found 'pagination' in page")
        
        # Check for API endpoints in page source
        print("\n" + "="*70)
        print("CHECKING FOR API CALLS")
        print("="*70)
        
        api_patterns = [
            r'/api/[^"\']+',
            r'graphql',
            r'/marketplace/[^"\']+',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, driver.page_source)
            if matches:
                unique_matches = set(matches[:5])
                print(f"\nPattern '{pattern}':")
                for match in unique_matches:
                    print(f"  {match}")
        
        # Try aggressive scrolling
        print("\n" + "="*70)
        print("TESTING AGGRESSIVE SCROLL")
        print("="*70)
        
        initial_cards = len(unique_urls)
        print(f"\nInitial cards: {initial_cards}")
        
        for i in range(20):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Check for new cards
            current_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
            current_urls = set([l.get_attribute('href') for l in current_links if l.get_attribute('href')])
            
            if len(current_urls) > len(unique_urls):
                new_count = len(current_urls) - len(unique_urls)
                print(f"  Scroll {i+1}: +{new_count} cards (Total: {len(current_urls)})")
                unique_urls = current_urls
            else:
                print(f"  Scroll {i+1}: No new cards (Total: {len(unique_urls)})")
            
            # Check page height
            current_height = driver.execute_script("return document.body.scrollHeight")
            if i == 0:
                print(f"    Page height: {current_height}")
        
        print(f"\nFinal unique card count: {len(unique_urls)}")
        
        # Save page for inspection
        with open('debug_marketplace.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("\nSaved page source to debug_marketplace.html")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    check_marketplace()

