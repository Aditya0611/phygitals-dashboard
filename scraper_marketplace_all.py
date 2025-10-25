"""
Phygitals Complete Marketplace Scraper
Scrapes ALL cards from marketplace with infinite scroll
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re

class CompleteMarketplaceScraper:
    def __init__(self):
        self.marketplace_url = "https://www.phygitals.com/marketplace"
        self.all_listings = []
        self.driver = None
        
    def setup_selenium(self):
        """Setup Chrome"""
        print("Setting up Chrome...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("Chrome ready!\n")
    
    def scrape_all_marketplace(self):
        """Scrape ALL marketplace listings with infinite scroll"""
        try:
            self.setup_selenium()
            
            print(f"Loading marketplace: {self.marketplace_url}")
            self.driver.get(self.marketplace_url)
            
            print("Waiting for initial load...")
            time.sleep(8)
            
            # Infinite scroll until no new cards load
            print("\nScrolling to load ALL listings...")
            print("(This may take several minutes)")
            
            card_urls = self.infinite_scroll_and_collect()
            
            if not card_urls:
                print("\nNo card listings found!")
                with open('debug_marketplace_full.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("Saved debug_marketplace_full.html")
                return
            
            print(f"\n{'='*70}")
            print(f"FOUND {len(card_urls)} TOTAL CARD LISTINGS!")
            print(f"{'='*70}\n")
            
            print(f"Scraping details from each card...")
            
            for i, card_url in enumerate(card_urls, 1):
                print(f"[{i}/{len(card_urls)}] {card_url[:80]}...")
                
                listing = self.scrape_card_page(card_url)
                if listing:
                    self.all_listings.append(listing)
                    print(f"  OK - {listing.get('grader', 'N/A')} {listing.get('grade', '')} - {listing.get('current_price', 'N/A')}")
                
                time.sleep(0.5)
                
                # Save progress every 50 cards
                if i % 50 == 0:
                    self.save_progress(i)
                
        except KeyboardInterrupt:
            print("\n\nStopped by user!")
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
    
    def infinite_scroll_and_collect(self):
        """Scroll infinitely until no new cards appear"""
        all_card_urls = set()
        no_new_cards_count = 0
        scroll_iteration = 0
        max_no_change = 5  # Stop after 5 scrolls with no new cards
        
        while no_new_cards_count < max_no_change:
            scroll_iteration += 1
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Wait for new cards to load
            
            # Find all card links
            current_urls = self.find_card_links()
            new_urls = current_urls - all_card_urls
            
            if new_urls:
                print(f"  Scroll {scroll_iteration}: Found {len(new_urls)} new cards (Total: {len(current_urls)})")
                all_card_urls.update(new_urls)
                no_new_cards_count = 0  # Reset counter
            else:
                no_new_cards_count += 1
                print(f"  Scroll {scroll_iteration}: No new cards ({no_new_cards_count}/{max_no_change})")
            
            # Scroll back up a bit to trigger lazy loading
            if scroll_iteration % 5 == 0:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(1)
        
        print(f"\nScrolling complete! Total unique cards found: {len(all_card_urls)}")
        return list(all_card_urls)
    
    def find_card_links(self):
        """Find all card listing URLs on current page"""
        card_urls = set()
        
        # Strategy 1: XPath
        try:
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/card/' in href:
                        card_urls.add(href)
                except:
                    pass
        except:
            pass
        
        # Strategy 2: CSS Selector
        try:
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/card/"]')
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href:
                        card_urls.add(href)
                except:
                    pass
        except:
            pass
        
        # Strategy 3: Parse page source
        try:
            page_source = self.driver.page_source
            pattern = r'href="(/card/[^"]+)"'
            matches = re.findall(pattern, page_source)
            for m in matches:
                card_urls.add(f"https://www.phygitals.com{m}")
        except:
            pass
        
        return card_urls
    
    def scrape_card_page(self, card_url):
        """Scrape individual card listing page"""
        try:
            self.driver.get(card_url)
            time.sleep(2)
            
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
            if listing['full_listing_name']:
                # Try to extract Pokemon name (before grader or special chars)
                pokemon_match = re.search(r'([\w\s-]+?)(?:\s+PSA|\s+CGC|\s+BGS|\s+#|\s+-|$)', listing['full_listing_name'])
                if pokemon_match:
                    listing['pokemon_name'] = pokemon_match.group(1).strip()
            
            # Extract card number
            card_num_match = re.search(r'#(\d+)', listing['full_listing_name'])
            if card_num_match:
                listing['card_number'] = card_num_match.group(1)
            
            return listing
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def save_progress(self, count):
        """Save progress"""
        filename = f"marketplace_all_progress_{count}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print(f"\n*** Progress saved: {filename} ({len(self.all_listings)} listings) ***\n")
    
    def save_final(self):
        """Save final results"""
        print("\n" + "="*70)
        print("SAVING FINAL DATA")
        print("="*70)
        
        # JSON
        with open('phygitals_all_marketplace_listings.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print("Saved: phygitals_all_marketplace_listings.json")
        
        # Excel
        if self.all_listings:
            df = pd.DataFrame(self.all_listings)
            
            # Reorder columns
            columns_order = [
                'listing_url',
                'full_listing_name',
                'pokemon_name',
                'grader',
                'grade',
                'current_price',
                'fmv',
                'card_set',
                'card_number',
                'condition',
                'seller'
            ]
            
            existing_cols = [col for col in columns_order if col in df.columns]
            df = df[existing_cols]
            
            df.to_excel('phygitals_all_marketplace_listings.xlsx', index=False)
            print("Saved: phygitals_all_marketplace_listings.xlsx")
            
            # CSV
            df.to_csv('phygitals_all_marketplace_listings.csv', index=False, encoding='utf-8')
            print("Saved: phygitals_all_marketplace_listings.csv")
            
            print(f"\nTotal listings: {len(self.all_listings)}")
            
            # Stats
            print("\n" + "="*70)
            print("STATISTICS")
            print("="*70)
            
            graders = df['grader'].value_counts()
            print("\nGraders:")
            for grader, count in graders.items():
                print(f"  {grader}: {count}")
            
            grades = df['grade'].value_counts().head(10)
            print("\nTop Grades:")
            for grade, count in grades.items():
                print(f"  Grade {grade}: {count}")
            
            # Price range
            try:
                prices = df['current_price'].str.replace('$', '').str.replace(',', '').astype(float)
                print(f"\nPrice Range:")
                print(f"  Min: ${prices.min():.2f}")
                print(f"  Max: ${prices.max():.2f}")
                print(f"  Average: ${prices.mean():.2f}")
            except:
                pass
            
            # Show sample
            print("\n" + "="*70)
            print("SAMPLE LISTINGS (first 10):")
            print("="*70)
            for i, listing in enumerate(self.all_listings[:10], 1):
                print(f"{i}. {listing['pokemon_name'][:40]} - {listing['grader']} {listing['grade']} - {listing['current_price']}")
        
        print("\n" + "="*70)


def main():
    print("""
    ==============================================================
       Phygitals COMPLETE Marketplace Scraper
       Scrapes ALL cards with infinite scroll
    ==============================================================
    """)
    
    print("\nThis scraper will:")
    print("  1. Load the marketplace page")
    print("  2. Scroll infinitely until all cards are loaded")
    print("  3. Visit each card listing page")
    print("  4. Extract complete details")
    print("  5. Save to Excel/CSV/JSON")
    print("\nEstimated time: 30-60 minutes")
    print("Press Ctrl+C at any time to stop (progress will be saved)\n")
    
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    scraper = CompleteMarketplaceScraper()
    scraper.scrape_all_marketplace()
    scraper.save_final()
    
    print("\nDONE!")


if __name__ == "__main__":
    main()

