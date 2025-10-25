"""
Resume Marketplace Scraper - Continue from where we left off
Includes crash recovery and session refresh
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re

class ResumeMarketplaceScraper:
    def __init__(self, start_from=151, end_at=None):
        self.base_url = "https://www.phygitals.com/pokemon/"
        self.start_from = start_from  # Resume from this Pokemon ID
        self.end_at = end_at or 1025  # End at this Pokemon ID
        self.all_listings = []
        self.driver = None
        self.load_existing_data()
        
    def load_existing_data(self):
        """Load existing progress"""
        try:
            with open('marketplace_progress_150.json', 'r', encoding='utf-8') as f:
                self.all_listings = json.load(f)
            print(f"Loaded {len(self.all_listings)} existing listings")
        except:
            print("No existing data found, starting fresh")
    
    def setup_selenium(self):
        """Setup Selenium with recovery"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        print("Setting up Chrome...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("Chrome ready!")
    
    def scrape_remaining_pokemon(self):
        """Scrape from start_from to end_at with crash recovery"""
        pokemon_id = self.start_from
        
        while pokemon_id <= self.end_at:
            try:
                # Restart browser every 50 Pokemon to avoid crashes
                if (pokemon_id - self.start_from) % 50 == 0:
                    print(f"\nRefreshing browser session...")
                    self.setup_selenium()
                
                url = f"{self.base_url}{pokemon_id}"
                print(f"\n[{pokemon_id}/{self.end_at}] Scraping Pokemon ID {pokemon_id}")
                print(f"   URL: {url}")
                
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Get Pokemon name from page
                    try:
                        pokemon_name = self.driver.find_element(By.TAG_NAME, 'h1').text
                    except:
                        pokemon_name = f"Pokemon_{pokemon_id}"
                    
                    print(f"   Pokemon: {pokemon_name}")
                    
                    # Scroll and parse
                    self.scroll_to_bottom()
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Extract listings
                    listings = self.extract_listings(soup, pokemon_name, url, pokemon_id)
                    
                    if listings:
                        print(f"   Found {len(listings)} listings")
                        self.all_listings.extend(listings)
                    else:
                        print(f"   No listings found")
                    
                except WebDriverException as e:
                    print(f"   Browser error, restarting...")
                    self.setup_selenium()
                    continue  # Retry same Pokemon
                
                # Save progress every 10 Pokemon
                if pokemon_id % 10 == 0:
                    self.save_progress(pokemon_id)
                
                time.sleep(1)  # Rate limiting
                pokemon_id += 1
                
            except KeyboardInterrupt:
                print("\n\nStopped by user!")
                break
            except Exception as e:
                print(f"   Error: {e}")
                pokemon_id += 1  # Skip and continue
        
        # Final cleanup
        if self.driver:
            self.driver.quit()
        
        return self.all_listings
    
    def extract_listings(self, soup, pokemon_name, url, pokemon_id):
        """Extract listings from page"""
        listings = []
        
        # Find item divs
        items = soup.select('div[class*="item"]')
        
        for item in items:
            text = item.get_text(strip=True)
            
            # Look for price
            if '$' not in text:
                continue
            
            listing = {
                'pokemon_name': pokemon_name,
                'pokemon_url': url,
                'pokemon_id': pokemon_id,
                'generation': self.guess_generation(pokemon_id),
                'listing_name': '',
                'listing_price': '',
                'fmv': '',
                'condition': '',
                'seller': '',
                'full_text': text
            }
            
            # Extract listing name
            lines = text.split('\n')
            if lines:
                listing['listing_name'] = lines[0]
            
            # Extract price
            prices = re.findall(r'\$[\d,]+\.?\d*', text)
            if prices:
                listing['listing_price'] = prices[0]
                if len(prices) > 1:
                    listing['fmv'] = prices[1]
            
            # Extract condition
            condition_match = re.search(r'(PSA|BGS|CGC|Raw|Graded)\s*\d*', text, re.IGNORECASE)
            if condition_match:
                listing['condition'] = condition_match.group(0)
            
            if listing['listing_price']:
                listings.append(listing)
        
        # Remove duplicates
        seen = set()
        unique = []
        for listing in listings:
            key = (listing['listing_name'], listing['listing_price'])
            if key not in seen:
                seen.add(key)
                unique.append(listing)
        
        return unique
    
    def guess_generation(self, pokemon_id):
        """Guess generation based on Pokemon ID"""
        if pokemon_id <= 151: return 1
        if pokemon_id <= 251: return 2
        if pokemon_id <= 386: return 3
        if pokemon_id <= 493: return 4
        if pokemon_id <= 649: return 5
        if pokemon_id <= 721: return 6
        if pokemon_id <= 809: return 7
        if pokemon_id <= 905: return 8
        return 9
    
    def scroll_to_bottom(self):
        """Quick scroll"""
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
    
    def save_progress(self, current_id):
        """Save progress"""
        filename = f"marketplace_progress_{current_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print(f"   Progress saved: {filename} ({len(self.all_listings)} listings)")
    
    def save_final(self):
        """Save final results"""
        # Save JSON
        with open('phygitals_all_listings.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print(f"Saved JSON: phygitals_all_listings.json")
        
        # Save Excel
        df = pd.DataFrame(self.all_listings)
        df.to_excel('phygitals_all_listings.xlsx', index=False)
        print(f"Saved Excel: phygitals_all_listings.xlsx")
        
        # Save CSV
        df.to_csv('phygitals_all_listings.csv', index=False, encoding='utf-8')
        print(f"Saved CSV: phygitals_all_listings.csv")
        
        print(f"\nTotal listings: {len(self.all_listings)}")


def main():
    print("""
    ==============================================================
       Resume Marketplace Scraper
       Continue from Pokemon 151 onwards
    ==============================================================
    """)
    
    print("\nOptions:")
    print("1. Continue from Pokemon 151 to 1025 (all remaining)")
    print("2. Scrape Gen 2 only (Pokemon 152-251)")
    print("3. Scrape next 100 Pokemon (151-250)")
    print("4. Scrape next 50 Pokemon (151-200)")
    print("5. Custom range")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        scraper = ResumeMarketplaceScraper(start_from=151, end_at=1025)
    elif choice == "2":
        scraper = ResumeMarketplaceScraper(start_from=152, end_at=251)
    elif choice == "3":
        scraper = ResumeMarketplaceScraper(start_from=151, end_at=250)
    elif choice == "4":
        scraper = ResumeMarketplaceScraper(start_from=151, end_at=200)
    else:
        start = int(input("Start from Pokemon ID: "))
        end = int(input("End at Pokemon ID: "))
        scraper = ResumeMarketplaceScraper(start_from=start, end_at=end)
    
    print("\nStarting scraper...")
    print("TIP: Press Ctrl+C to stop anytime (progress will be saved)")
    print()
    
    scraper.scrape_remaining_pokemon()
    
    print("\n" + "="*70)
    print("SAVING FINAL DATA...")
    print("="*70)
    scraper.save_final()
    
    print("\nDONE!")


if __name__ == "__main__":
    main()

