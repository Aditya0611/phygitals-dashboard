"""
Phygitals Marketplace Scraper - URL PAGINATION
Uses direct URL navigation instead of button clicking
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re

class URLMarketplaceScraper:
    def __init__(self, start_page=1, max_pages=None):
        self.marketplace_base_url = "https://www.phygitals.com/marketplace"
        self.all_listings = []
        self.driver = None
        self.start_page = start_page
        self.max_pages = max_pages
        
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
    
    def scrape_all_pages(self):
        """Scrape all marketplace pages using direct URL navigation"""
        try:
            self.setup_selenium()
            
            # Determine pages to scrape
            if self.max_pages:
                pages_to_scrape = self.max_pages
            else:
                pages_to_scrape = 1516  # Total pages from screenshot
            
            print(f"{'='*70}")
            print(f"SCRAPING {pages_to_scrape} PAGES")
            print(f"{'='*70}\n")
            
            for page_num in range(self.start_page, pages_to_scrape + 1):
                print(f"\n{'='*70}")
                print(f"PAGE {page_num}/{pages_to_scrape}")
                print(f"{'='*70}")
                
                # Try different URL patterns
                urls_to_try = [
                    f"{self.marketplace_base_url}?page={page_num}",
                    f"{self.marketplace_base_url}?p={page_num}",
                    f"{self.marketplace_base_url}/page/{page_num}",
                ]
                
                card_urls = None
                for url in urls_to_try:
                    print(f"Trying: {url}")
                    self.driver.get(url)
                    time.sleep(4)
                    
                    # Check if page loaded correctly
                    card_urls = self.get_cards_from_current_page()
                    
                    if card_urls and len(card_urls) > 0:
                        print(f"✓ Found {len(card_urls)} cards with this URL pattern!")
                        break
                    else:
                        print(f"✗ No cards found with this URL")
                
                if not card_urls or len(card_urls) == 0:
                    print("⚠️  No cards found on this page. Stopping.")
                    break
                
                # Scrape each card
                for i, card_url in enumerate(card_urls, 1):
                    print(f"  [{i}/{len(card_urls)}] {card_url[:70]}...")
                    
                    card_data = self.scrape_card_page(card_url)
                    if card_data:
                        self.all_listings.append(card_data)
                        print(f"    ✓ {card_data.get('grader', 'N/A')} {card_data.get('grade', '')} - {card_data.get('current_price', 'N/A')}")
                    
                    time.sleep(0.3)
                
                print(f"\nTotal cards collected: {len(self.all_listings):,}")
                
                # Save progress every 10 pages
                if page_num % 10 == 0:
                    self.save_progress(page_num)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Stopped by user!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
    
    def get_cards_from_current_page(self):
        """Get all card URLs from the current page"""
        card_urls = set()
        
        # Wait and scroll
        time.sleep(3)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Find card links
        try:
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/card/' in href and 'phygitals.com/card/' in href:
                        card_urls.add(href)
                except:
                    pass
        except:
            pass
        
        return list(card_urls)
    
    def scrape_card_page(self, card_url):
        """Scrape individual card listing page"""
        try:
            self.driver.get(card_url)
            time.sleep(1.5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            card = {
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
                    card['full_listing_name'] = h1.get_text(strip=True)
                    title_parts = card['full_listing_name'].split()
                    if len(title_parts) > 2:
                        card['pokemon_name'] = ' '.join(title_parts[2:8])
            except:
                pass
            
            # Get all text
            page_text = soup.get_text()
            
            # Extract data
            grader_match = re.search(r'\b(PSA|CGC|BGS|Beckett)\b', page_text, re.IGNORECASE)
            if grader_match:
                card['grader'] = grader_match.group(1).upper()
            
            grade_match = re.search(r'(?:PSA|CGC|BGS)\s*(\d+(?:\.\d+)?)', page_text, re.IGNORECASE)
            if grade_match:
                card['grade'] = grade_match.group(1)
            
            prices = re.findall(r'\$[\d,]+\.?\d*', page_text)
            if prices:
                card['current_price'] = prices[0]
                if len(prices) > 1:
                    card['fmv'] = prices[1]
            
            card_num_match = re.search(r'#(\d+)', card['full_listing_name'])
            if card_num_match:
                card['card_number'] = card_num_match.group(1)
            
            return card
            
        except Exception as e:
            return None
    
    def save_progress(self, page_num):
        """Save progress checkpoint"""
        if self.all_listings:
            filename = f'marketplace_url_progress_page{page_num}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
            print(f"\n*** Progress saved: {filename} ({len(self.all_listings):,} cards) ***\n")
    
    def save_final(self):
        """Save final results"""
        if not self.all_listings:
            print("\nNo data to save!")
            return
        
        print("\n" + "="*70)
        print("SAVING FINAL DATA")
        print("="*70)
        
        # JSON
        with open('phygitals_marketplace_complete.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print("Saved: phygitals_marketplace_complete.json")
        
        # Excel and CSV
        df = pd.DataFrame(self.all_listings)
        df.to_excel('phygitals_marketplace_complete.xlsx', index=False)
        print("Saved: phygitals_marketplace_complete.xlsx")
        
        df.to_csv('phygitals_marketplace_complete.csv', index=False, encoding='utf-8')
        print("Saved: phygitals_marketplace_complete.csv")
        
        print(f"\nTotal cards saved: {len(self.all_listings):,}")
        
        # Statistics
        print("\n" + "="*70)
        print("STATISTICS")
        print("="*70)
        
        if len(df) > 0:
            graders = df['grader'].value_counts()
            print("\nGraders:")
            for grader, count in graders.head(10).items():
                if grader:
                    print(f"  {grader}: {count:,}")
            
            grades = df['grade'].value_counts().head(10)
            print("\nTop Grades:")
            for grade, count in grades.items():
                if grade:
                    print(f"  Grade {grade}: {count:,}")
        
        print("\n" + "="*70)


def main():
    print("""
    ==============================================================
       Phygitals Marketplace Scraper - URL METHOD
       Navigates pages using direct URLs
    ==============================================================
    """)
    
    # FULL SCRAPE: Get all 1,516 pages = 24,254 cards
    print("\n🚀 FULL SCRAPE MODE: Getting ALL 1,516 pages (24,254 cards)")
    print("   Estimated time: 6-8 hours")
    print("   Progress auto-saves every 10 pages")
    print("   Press Ctrl+C anytime to stop safely")
    print("   URL pattern: https://www.phygitals.com/marketplace?page=N")
    
    max_pages = None  # None = all 1516 pages
    
    print("\nStarting in 5 seconds...")
    time.sleep(5)
    
    scraper = URLMarketplaceScraper(start_page=1, max_pages=max_pages)
    
    try:
        scraper.scrape_all_pages()
    except KeyboardInterrupt:
        print("\nStopped by user!")
    
    scraper.save_final()
    print("\n✅ DONE!")


if __name__ == "__main__":
    main()

