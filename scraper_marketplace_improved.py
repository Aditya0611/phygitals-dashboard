"""
Phygitals Complete Marketplace Scraper - IMPROVED
Scrapes ALL cards from marketplace with aggressive infinite scroll
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re

class ImprovedMarketplaceScraper:
    def __init__(self):
        self.marketplace_url = "https://www.phygitals.com/marketplace"
        self.all_listings = []
        self.driver = None
        
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
    
    def scrape_all_marketplace(self):
        """Scrape ALL marketplace listings with aggressive infinite scroll"""
        try:
            self.setup_selenium()
            
            print(f"Loading marketplace: {self.marketplace_url}")
            self.driver.get(self.marketplace_url)
            
            print("Waiting for initial load...")
            time.sleep(10)  # Longer initial wait
            
            # Infinite scroll until no new cards load
            print("\nScrolling AGGRESSIVELY to load ALL listings...")
            print("(This will take a while - be patient!)")
            print("Stopping only after 15 consecutive scrolls with no new cards\n")
            
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
        """Scroll infinitely with AGGRESSIVE strategy until no new cards appear"""
        all_card_urls = set()
        no_new_cards_count = 0
        scroll_iteration = 0
        max_no_change = 15  # INCREASED: Stop after 15 scrolls with no new cards
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while no_new_cards_count < max_no_change:
            scroll_iteration += 1
            
            # Strategy 1: Scroll to absolute bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)  # INCREASED wait time
            
            # Strategy 2: Scroll in increments (helps trigger lazy loading)
            if scroll_iteration % 3 == 0:
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                # Scroll through the page in chunks
                for position in range(0, current_height, 500):
                    self.driver.execute_script(f"window.scrollTo(0, {position});")
                    time.sleep(0.3)
            
            # Strategy 3: Check for "Load More" button or similar
            try:
                load_more_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Load') or contains(text(), 'More') or contains(text(), 'Show')]")
                for button in load_more_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            print(f"  Clicked 'Load More' button")
                            time.sleep(3)
                    except:
                        pass
            except:
                pass
            
            # Find all card links
            current_urls = self.find_card_links()
            new_urls = current_urls - all_card_urls
            
            # Check if page height changed
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            height_changed = new_height != last_height
            last_height = new_height
            
            if new_urls:
                print(f"  Scroll {scroll_iteration}: Found {len(new_urls)} new cards (Total: {len(current_urls)}) {'[Height changed]' if height_changed else ''}")
                all_card_urls.update(new_urls)
                no_new_cards_count = 0  # Reset counter
            else:
                no_new_cards_count += 1
                print(f"  Scroll {scroll_iteration}: No new cards ({no_new_cards_count}/{max_no_change}) {f'[Height: {new_height}]' if height_changed else ''}")
            
            # Strategy 4: Scroll back up occasionally to trigger lazy loading
            if scroll_iteration % 5 == 0:
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
        
        print(f"\nScrolling complete! Total unique cards found: {len(all_card_urls)}")
        return list(all_card_urls)
    
    def find_card_links(self):
        """Find all card listing URLs on current page - IMPROVED"""
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
        
        # Strategy 3: Parse page source with regex
        try:
            page_source = self.driver.page_source
            pattern = r'href="(/card/[^"]+)"'
            matches = re.findall(pattern, page_source)
            for match in matches:
                full_url = f"https://www.phygitals.com{match}"
                card_urls.add(full_url)
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
                    
                    # Extract Pokemon name from title
                    title_parts = listing['full_listing_name'].split()
                    if len(title_parts) > 2:
                        listing['pokemon_name'] = ' '.join(title_parts[2:8])  # Take middle portion
            except:
                pass
            
            # Get all text for pattern matching
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
            
            # Extract card number
            card_num_match = re.search(r'#(\d+)', listing['full_listing_name'])
            if card_num_match:
                listing['card_number'] = card_num_match.group(1)
            
            return listing
            
        except Exception as e:
            return None
    
    def save_progress(self, card_count):
        """Save progress checkpoint"""
        if self.all_listings:
            filename = f'marketplace_progress_{card_count}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
            print(f"\n*** Progress saved: {filename} ({len(self.all_listings)} listings) ***\n")
    
    def save_final(self):
        """Save final results to multiple formats"""
        if not self.all_listings:
            print("\nNo data to save!")
            return
        
        print("\n" + "="*70)
        print("SAVING FINAL DATA")
        print("="*70)
        
        # JSON
        with open('phygitals_all_marketplace_listings.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print("Saved: phygitals_all_marketplace_listings.json")
        
        # Excel and CSV
        df = pd.DataFrame(self.all_listings)
        df.to_excel('phygitals_all_marketplace_listings.xlsx', index=False)
        print("Saved: phygitals_all_marketplace_listings.xlsx")
        
        df.to_csv('phygitals_all_marketplace_listings.csv', index=False, encoding='utf-8')
        print("Saved: phygitals_all_marketplace_listings.csv")
        
        # Statistics
        print("\nTotal listings:", len(self.all_listings))
        
        print("\n" + "="*70)
        print("STATISTICS")
        print("="*70)
        
        if len(df) > 0:
            # Graders
            graders = df['grader'].value_counts()
            print("\nGraders:")
            for grader, count in graders.items():
                if grader:
                    print(f"  {grader}: {count}")
            
            # Grades
            grades = df['grade'].value_counts().head(10)
            print("\nTop Grades:")
            for grade, count in grades.items():
                if grade:
                    print(f"  Grade {grade}: {count}")
            
            # Prices
            try:
                prices = df['current_price'].str.replace('$', '').str.replace(',', '').astype(float)
                print("\nPrice Range:")
                print(f"  Min: ${prices.min():.2f}")
                print(f"  Max: ${prices.max():.2f}")
                print(f"  Average: ${prices.mean():.2f}")
            except:
                pass
        
        print("\n" + "="*70)
        print("SAMPLE LISTINGS (first 10):")
        print("="*70)
        for i, listing in enumerate(self.all_listings[:10], 1):
            name_short = listing['pokemon_name'][:45] if listing['pokemon_name'] else 'N/A'
            print(f"{i}. {name_short} - {listing['grader']} {listing['grade']} - {listing['current_price']}")
        
        print("\n" + "="*70)


def main():
    print("""
    ==============================================================
       Phygitals IMPROVED Marketplace Scraper
       AGGRESSIVE scrolling to capture ALL cards
    ==============================================================
    """)
    
    print("\nThis scraper will:")
    print("  1. Load the marketplace page")
    print("  2. Scroll AGGRESSIVELY with multiple strategies")
    print("  3. Only stop after 15 consecutive scrolls with no new cards")
    print("  4. Visit each card listing page")
    print("  5. Extract complete details")
    print("  6. Save to Excel/CSV/JSON")
    print("\nEstimated time: 30-90 minutes")
    print("Progress saves every 50 cards")
    print("Press Ctrl+C at any time to stop\n")
    
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    scraper = ImprovedMarketplaceScraper()
    
    try:
        scraper.scrape_all_marketplace()
    except KeyboardInterrupt:
        print("\nStopped by user!")
    
    scraper.save_final()
    print("\nDONE!")


if __name__ == "__main__":
    main()

