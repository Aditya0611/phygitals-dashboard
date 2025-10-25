"""
Explore ALL sections of Phygitals to find card listings
Tries: marketplace filters, search, browse pages, categories
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re

class PhygitalsExplorer:
    def __init__(self):
        self.driver = None
        self.all_cards = []
        
    def setup_selenium(self):
        """Setup Chrome"""
        print("Setting up Chrome...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("Chrome ready!\n")
    
    def explore_all(self):
        """Try different URLs and methods to find cards"""
        try:
            self.setup_selenium()
            
            urls_to_try = [
                ("Marketplace", "https://www.phygitals.com/marketplace"),
                ("Browse", "https://www.phygitals.com/browse"),
                ("Cards", "https://www.phygitals.com/cards"),
                ("Shop", "https://www.phygitals.com/shop"),
                ("Pokemon Cards", "https://www.phygitals.com/pokemon-cards"),
                ("Listings", "https://www.phygitals.com/listings"),
                ("Marketplace PSA", "https://www.phygitals.com/marketplace?grader=PSA"),
                ("Marketplace CGC", "https://www.phygitals.com/marketplace?grader=CGC"),
                ("Marketplace Sort Price", "https://www.phygitals.com/marketplace?sort=price"),
                ("Marketplace All", "https://www.phygitals.com/marketplace?page=all"),
            ]
            
            all_found_urls = {}
            
            for name, url in urls_to_try:
                print(f"\n{'='*70}")
                print(f"Trying: {name}")
                print(f"URL: {url}")
                print(f"{'='*70}")
                
                try:
                    self.driver.get(url)
                    time.sleep(5)
                    
                    # Check if page exists
                    if "404" in self.driver.title.lower() or "not found" in self.driver.page_source.lower():
                        print("❌ Page not found (404)")
                        continue
                    
                    print(f"✓ Page loaded: {self.driver.title}")
                    
                    # Try to find cards
                    card_urls = self.find_cards_on_page()
                    
                    if card_urls:
                        print(f"✓ Found {len(card_urls)} card links!")
                        all_found_urls[name] = card_urls
                        
                        # Show sample URLs
                        for i, curl in enumerate(list(card_urls)[:3], 1):
                            print(f"  {i}. {curl}")
                    else:
                        print("❌ No card links found")
                    
                    # Save page source for analysis
                    filename = f"debug_{name.replace(' ', '_').lower()}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    print(f"Saved: {filename}")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                
                time.sleep(2)
            
            # Try search functionality
            print(f"\n{'='*70}")
            print("Trying SEARCH functionality")
            print(f"{'='*70}")
            
            search_cards = self.try_search()
            if search_cards:
                all_found_urls["Search"] = search_cards
                print(f"✓ Search found {len(search_cards)} cards")
            
            # Summary
            print(f"\n{'='*70}")
            print("SUMMARY OF FINDINGS")
            print(f"{'='*70}")
            
            total_unique = set()
            for name, urls in all_found_urls.items():
                total_unique.update(urls)
                print(f"{name}: {len(urls)} cards")
            
            print(f"\nTotal unique card URLs found: {len(total_unique)}")
            
            # Save all found URLs
            with open('all_found_card_urls.json', 'w') as f:
                json.dump({
                    'total_unique': len(total_unique),
                    'by_source': {k: list(v) for k, v in all_found_urls.items()},
                    'all_unique_urls': list(total_unique)
                }, f, indent=2)
            
            print("\nSaved: all_found_card_urls.json")
            
            return list(total_unique)
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def find_cards_on_page(self):
        """Find card URLs on current page with scrolling"""
        card_urls = set()
        
        # Scroll to load all content
        for i in range(10):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # Method 1: XPath
        try:
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
            for link in links:
                href = link.get_attribute('href')
                if href and '/card/' in href:
                    card_urls.add(href)
        except:
            pass
        
        # Method 2: CSS
        try:
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/card/"]')
            for link in links:
                href = link.get_attribute('href')
                if href:
                    card_urls.add(href)
        except:
            pass
        
        # Method 3: Regex in page source
        try:
            pattern = r'href="(/card/[^"]+)"'
            matches = re.findall(pattern, self.driver.page_source)
            for match in matches:
                card_urls.add(f"https://www.phygitals.com{match}")
        except:
            pass
        
        return card_urls
    
    def try_search(self):
        """Try to use search functionality"""
        try:
            self.driver.get("https://www.phygitals.com/marketplace")
            time.sleep(5)
            
            # Look for search input
            search_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]')
            
            if search_inputs:
                print("✓ Found search input!")
                search_box = search_inputs[0]
                
                # Try searching for "Pikachu"
                search_box.clear()
                search_box.send_keys("Pikachu")
                search_box.send_keys(Keys.RETURN)
                
                time.sleep(5)
                
                cards = self.find_cards_on_page()
                print(f"Search for 'Pikachu' found: {len(cards)} cards")
                
                return cards
            else:
                print("❌ No search input found")
                return set()
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            return set()


def main():
    print("""
    ==============================================================
       Phygitals Complete Explorer
       Finding ALL possible card sources
    ==============================================================
    """)
    
    explorer = PhygitalsExplorer()
    found_urls = explorer.explore_all()
    
    print(f"\n{'='*70}")
    print(f"EXPLORATION COMPLETE!")
    print(f"Found {len(found_urls)} unique card URLs")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

