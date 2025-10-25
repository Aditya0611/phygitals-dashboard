"""
Phygitals Marketplace Scraper - CORRECT VERSION
Scrapes from /marketplace, not /pokemon pages
Gets actual card listings with individual URLs
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re

class MarketplaceScraper:
    def __init__(self):
        self.marketplace_url = "https://www.phygitals.com/marketplace"
        self.all_listings = []
        self.driver = None
        
    def setup_selenium(self):
        """Setup Chrome"""
        print("Setting up Chrome...")
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("Chrome ready!\n")
    
    def scrape_marketplace(self):
        """Scrape marketplace listings"""
        try:
            self.setup_selenium()
            
            print(f"Loading marketplace: {self.marketplace_url}")
            self.driver.get(self.marketplace_url)
            
            print("Waiting for listings to load...")
            time.sleep(5)
            
            # Scroll to load all listings
            print("Scrolling to load all listings...")
            for i in range(20):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                print(f"  Scroll {i+1}/20...")
            
            # Get all card listing links
            print("\nSearching for card listings...")
            card_urls = self.find_card_links()
            
            if not card_urls:
                print("No card listings found!")
                # Save debug HTML
                with open('debug_marketplace.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("Saved debug_marketplace.html")
                return
            
            print(f"\nFound {len(card_urls)} card listings!")
            print(f"\nScraping details from each card...")
            
            for i, card_url in enumerate(card_urls, 1):
                print(f"\n[{i}/{len(card_urls)}] {card_url}")
                
                listing = self.scrape_card_page(card_url)
                if listing:
                    self.all_listings.append(listing)
                    print(f"  OK {listing.get('pokemon_name', 'N/A')} - {listing.get('current_price', 'N/A')}")
                
                time.sleep(1)
                
                # Save progress every 20 cards
                if i % 20 == 0:
                    self.save_progress(i)
                
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
    
    def find_card_links(self):
        """Find all card listing URLs"""
        card_urls = []
        
        # Strategy 1: XPath
        try:
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
            print(f"Found {len(links)} links via XPath")
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/card/' in href:
                        card_urls.append(href)
                except:
                    pass
        except Exception as e:
            print(f"XPath error: {e}")
        
        # Strategy 2: CSS Selector
        try:
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/card/"]')
            print(f"Found {len(links)} links via CSS")
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href:
                        card_urls.append(href)
                except:
                    pass
        except Exception as e:
            print(f"CSS error: {e}")
        
        # Strategy 3: Parse page source
        if not card_urls:
            print("Parsing page source for URLs...")
            page_source = self.driver.page_source
            pattern = r'href="(/card/[^"]+)"'
            matches = re.findall(pattern, page_source)
            card_urls = [f"https://www.phygitals.com{m}" for m in matches]
            print(f"Found {len(matches)} URLs in source")
        
        # Remove duplicates
        card_urls = list(set(card_urls))
        
        return card_urls
    
    def scrape_card_page(self, card_url):
        """Scrape individual card listing page"""
        try:
            self.driver.get(card_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            listing = {
                'listing_url': card_url,
                'full_listing_name': '',
                'pokemon_name': '',
                'grader': '',
                'grade': '',
                'current_price': '',
                'fmv': '',
                'card_set': '',
                'card_number': '',
                'condition': '',
                'seller': '',
            }
            
            # Get title
            try:
                h1 = soup.find('h1')
                if h1:
                    listing['full_listing_name'] = h1.get_text(strip=True)
            except:
                pass
            
            # Get all text
            page_text = soup.get_text()
            
            # Extract grader
            grader_match = re.search(r'\b(PSA|CGC|BGS|Beckett)\b', page_text, re.IGNORECASE)
            if grader_match:
                listing['grader'] = grader_match.group(1).upper()
            
            # Extract grade
            grade_match = re.search(r'(?:PSA|CGC|BGS)\s*(\d+(?:\.\d+)?)', page_text, re.IGNORECASE)
            if grade_match:
                listing['grade'] = grade_match.group(1)
            
            # Extract prices
            prices = re.findall(r'\$[\d,]+\.?\d*', page_text)
            if prices:
                listing['current_price'] = prices[0]
                if len(prices) > 1:
                    listing['fmv'] = prices[1]
            
            # Extract Pokemon name from title
            pokemon_match = re.search(r'([\w\s-]+?)(?:\s+PSA|\s+CGC|\s+BGS|\s+#|\s+-|$)', listing['full_listing_name'])
            if pokemon_match:
                listing['pokemon_name'] = pokemon_match.group(1).strip()
            
            return listing
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def save_progress(self, count):
        """Save progress"""
        filename = f"marketplace_listings_{count}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print(f"\n*** Saved progress: {filename} ({len(self.all_listings)} listings) ***")
    
    def save_final(self):
        """Save final results"""
        print("\n" + "="*70)
        print("SAVING FINAL DATA")
        print("="*70)
        
        # JSON
        with open('marketplace_card_listings.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print("Saved: marketplace_card_listings.json")
        
        # Excel
        if self.all_listings:
            df = pd.DataFrame(self.all_listings)
            df.to_excel('marketplace_card_listings.xlsx', index=False)
            print("Saved: marketplace_card_listings.xlsx")
            
            # CSV
            df.to_csv('marketplace_card_listings.csv', index=False, encoding='utf-8')
            print("Saved: marketplace_card_listings.csv")
            
            print(f"\nTotal listings: {len(self.all_listings)}")
            
            # Show sample
            print("\nSample listings:")
            for listing in self.all_listings[:10]:
                print(f"  - {listing['pokemon_name']}: {listing['current_price']} ({listing['listing_url']})")
        
        print("="*70)


def main():
    print("""
    ==============================================================
       Phygitals Marketplace Scraper
       Scrapes actual card listings from /marketplace
    ==============================================================
    """)
    
    scraper = MarketplaceScraper()
    scraper.scrape_marketplace()
    scraper.save_final()
    
    print("\nDONE!")


if __name__ == "__main__":
    main()

