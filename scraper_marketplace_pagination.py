"""
Phygitals Marketplace Scraper with PAGINATION
Goes through all pages to get ALL 24,254+ cards
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re

class PaginationMarketplaceScraper:
    def __init__(self, start_page=1, max_pages=None):
        self.marketplace_url = "https://www.phygitals.com/marketplace"
        self.all_listings = []
        self.driver = None
        self.start_page = start_page
        self.max_pages = max_pages  # None = scrape all pages
        
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
        """Scrape all marketplace pages with pagination"""
        try:
            self.setup_selenium()
            
            print(f"Loading marketplace: {self.marketplace_url}")
            self.driver.get(self.marketplace_url)
            time.sleep(8)
            
            # Get total number of pages
            total_pages = self.get_total_pages()
            print(f"\n{'='*70}")
            print(f"Total pages detected: {total_pages}")
            print(f"{'='*70}\n")
            
            # Determine how many pages to scrape
            if self.max_pages:
                pages_to_scrape = min(self.max_pages, total_pages)
                print(f"Will scrape {pages_to_scrape} pages (limited by max_pages setting)")
            else:
                pages_to_scrape = total_pages
                print(f"Will scrape ALL {pages_to_scrape} pages")
            
            print(f"Starting from page {self.start_page}\n")
            
            # Scrape each page
            current_page = self.start_page
            
            while current_page <= pages_to_scrape:
                print(f"\n{'='*70}")
                print(f"PAGE {current_page}/{pages_to_scrape}")
                print(f"{'='*70}")
                
                # Get card URLs from current page
                card_urls = self.get_cards_from_current_page()
                
                if card_urls:
                    print(f"Found {len(card_urls)} cards on this page")
                    
                    # Scrape each card
                    for i, card_url in enumerate(card_urls, 1):
                        print(f"  [{i}/{len(card_urls)}] Scraping {card_url[:70]}...")
                        
                        card_data = self.scrape_card_page(card_url)
                        if card_data:
                            self.all_listings.append(card_data)
                            print(f"    ✓ {card_data.get('grader', 'N/A')} {card_data.get('grade', '')} - {card_data.get('current_price', 'N/A')}")
                        
                        time.sleep(0.3)  # Be respectful to the server
                    
                    print(f"\nTotal cards collected so far: {len(self.all_listings)}")
                else:
                    print("No cards found on this page")
                
                # Save progress every 10 pages
                if current_page % 10 == 0:
                    self.save_progress(current_page)
                
                # Go to next page
                if current_page < pages_to_scrape:
                    if not self.go_to_next_page():
                        print("\n⚠️  Could not go to next page. Stopping.")
                        break
                    time.sleep(3)
                
                current_page += 1
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Stopped by user!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
    
    def get_total_pages(self):
        """Extract total number of pages from pagination"""
        try:
            # Look for text like "Showing 1 - 16 of 24254 results"
            page_text = self.driver.page_source
            
            # Try to find total results
            result_match = re.search(r'of\s+([\d,]+)\s+results', page_text, re.IGNORECASE)
            if result_match:
                total_results = int(result_match.group(1).replace(',', ''))
                print(f"Total results: {total_results:,}")
                
                # Try to find items per page
                per_page_match = re.search(r'(\d+)\s+per\s+page', page_text, re.IGNORECASE)
                if per_page_match:
                    per_page = int(per_page_match.group(1))
                else:
                    per_page = 16  # Default based on screenshot
                
                total_pages = (total_results + per_page - 1) // per_page
                print(f"Items per page: {per_page}")
                return total_pages
            
            # Fallback: Look for pagination buttons
            try:
                # Find all page number buttons
                page_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(@class, 'page') or contains(@aria-label, 'page')]")
                
                page_numbers = []
                for btn in page_buttons:
                    try:
                        text = btn.text.strip()
                        if text.isdigit():
                            page_numbers.append(int(text))
                    except:
                        pass
                
                if page_numbers:
                    return max(page_numbers)
            except:
                pass
            
            # Default fallback
            print("⚠️  Could not determine total pages, defaulting to 1516")
            return 1516
            
        except Exception as e:
            print(f"Error getting total pages: {e}")
            return 1516
    
    def get_cards_from_current_page(self):
        """Get all card URLs from the current page"""
        card_urls = set()
        
        # Wait for cards to load
        time.sleep(3)
        
        # Scroll to load any lazy-loaded content
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Method 1: XPath
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
        
        # Method 2: CSS Selector
        try:
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/card/"]')
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/card/' in href:
                        card_urls.add(href)
                except:
                    pass
        except:
            pass
        
        return list(card_urls)
    
    def go_to_next_page(self):
        """Click the 'Next' button to go to next page"""
        try:
            # Strategy 1: Find "Next" button and use JavaScript click
            try:
                next_button = self.driver.find_element(By.XPATH, 
                    "//button[contains(text(), 'Next')]")
                if next_button.is_enabled():
                    # Scroll to element first
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.5)
                    
                    # Use JavaScript click to bypass overlays
                    self.driver.execute_script("arguments[0].click();", next_button)
                    print("  ✓ Clicked 'Next' button (JavaScript)")
                    return True
            except Exception as e:
                pass
            
            # Strategy 2: Find next page button by number and use JavaScript click
            try:
                # Get current page - look for button with bg-neutral-900 or dark mode equivalent
                current_page_elements = self.driver.find_elements(By.XPATH, 
                    "//button[contains(@class, 'bg-neutral-900') or contains(@class, 'bg-white')]")
                
                current_page = 1
                for elem in current_page_elements:
                    try:
                        text = elem.text.strip()
                        if text.isdigit():
                            current_page = int(text)
                            break
                    except:
                        pass
                
                # Find and click next page number button
                next_page_num = current_page + 1
                next_page_button = self.driver.find_element(By.XPATH, 
                    f"//button[text()='{next_page_num}']")
                
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_button)
                time.sleep(0.5)
                
                # JavaScript click
                self.driver.execute_script("arguments[0].click();", next_page_button)
                print(f"  ✓ Clicked page {next_page_num} button (JavaScript)")
                return True
            except Exception as e:
                pass
            
            print("  ❌ Could not find 'Next' button")
            return False
            
        except Exception as e:
            print(f"  ❌ Error going to next page: {e}")
            return False
    
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
                    
                    # Extract Pokemon name from title
                    title_parts = card['full_listing_name'].split()
                    if len(title_parts) > 2:
                        card['pokemon_name'] = ' '.join(title_parts[2:8])
            except:
                pass
            
            # Get all text
            page_text = soup.get_text()
            
            # Extract grader
            grader_match = re.search(r'\b(PSA|CGC|BGS|Beckett)\b', page_text, re.IGNORECASE)
            if grader_match:
                card['grader'] = grader_match.group(1).upper()
            
            # Extract grade
            grade_match = re.search(r'(?:PSA|CGC|BGS)\s*(\d+(?:\.\d+)?)', page_text, re.IGNORECASE)
            if grade_match:
                card['grade'] = grade_match.group(1)
            
            # Extract prices
            prices = re.findall(r'\$[\d,]+\.?\d*', page_text)
            if prices:
                card['current_price'] = prices[0]
                if len(prices) > 1:
                    card['fmv'] = prices[1]
            
            # Extract card number
            card_num_match = re.search(r'#(\d+)', card['full_listing_name'])
            if card_num_match:
                card['card_number'] = card_num_match.group(1)
            
            return card
            
        except Exception as e:
            return None
    
    def save_progress(self, page_num):
        """Save progress checkpoint"""
        if self.all_listings:
            filename = f'marketplace_pagination_progress_page{page_num}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
            print(f"\n*** Progress saved: {filename} ({len(self.all_listings)} cards) ***\n")
    
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
            # Graders
            graders = df['grader'].value_counts()
            print("\nGraders:")
            for grader, count in graders.head(10).items():
                if grader:
                    print(f"  {grader}: {count:,}")
            
            # Grades
            grades = df['grade'].value_counts().head(10)
            print("\nTop Grades:")
            for grade, count in grades.items():
                if grade:
                    print(f"  Grade {grade}: {count:,}")
        
        print("\n" + "="*70)


def main():
    print("""
    ==============================================================
       Phygitals Marketplace Scraper - PAGINATION VERSION
       Scrapes ALL pages to get ALL 24,000+ cards
    ==============================================================
    """)
    
    # TEST MODE: Start with just 3 pages to verify pagination works
    print("\n🧪 TEST MODE: Scraping 3 pages first (~48 cards)")
    print("   This will verify pagination is working correctly")
    print("   If successful, edit max_pages=None to scrape ALL pages")
    
    max_pages = 3  # Change to None for ALL pages
    
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    scraper = PaginationMarketplaceScraper(start_page=1, max_pages=max_pages)
    
    try:
        scraper.scrape_all_pages()
    except KeyboardInterrupt:
        print("\nStopped by user!")
    
    scraper.save_final()
    print("\n✅ DONE!")


if __name__ == "__main__":
    main()

