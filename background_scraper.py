#!/usr/bin/env python3
"""
Background Scraper for Phygitals Marketplace
Continuously scrapes data in the background and updates the dashboard
"""

import time
import json
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import pandas as pd

class BackgroundScraper:
    def __init__(self):
        self.driver = None
        self.all_cards = []
        self.current_page = 1
        self.max_pages = None
        self.start_time = datetime.now()
        self.last_save_time = datetime.now()
        self.save_interval = 300  # Save every 5 minutes
        self.scrape_interval = 3600  # Run full scrape every hour
        
    def setup_driver(self):
        """Setup Chrome driver with optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("Chrome driver initialized")
            return True
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return False
    
    def scrape_page(self, page_num):
        """Scrape a single page"""
        url = f"https://www.phygitals.com/marketplace?page={page_num}"
        print(f"Scraping page {page_num}: {url}")
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for cards to load
            time.sleep(3)
            
            # Find all card links
            card_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/card/"]')
            cards_found = 0
            
            for link in card_links:
                try:
                    card_url = link.get_attribute('href')
                    if card_url and '/card/' in card_url:
                        # Extract card data
                        card_data = self.extract_card_data(link)
                        if card_data:
                            self.all_cards.append(card_data)
                            cards_found += 1
                except Exception as e:
                    continue
            
            print(f"  Found {cards_found} cards on page {page_num}")
            return cards_found > 0
            
        except TimeoutException:
            print(f"  Timeout on page {page_num}")
            return False
        except Exception as e:
            print(f"  Error on page {page_num}: {e}")
            return False
    
    def extract_card_data(self, link_element):
        """Extract card data from a link element"""
        try:
            card_url = link_element.get_attribute('href')
            
            # Try to get card name from various selectors
            card_name = ""
            try:
                name_element = link_element.find_element(By.CSS_SELECTOR, 'h3, .card-title, [class*="title"]')
                card_name = name_element.text.strip()
            except:
                try:
                    card_name = link_element.text.strip()
                except:
                    card_name = "Unknown Card"
            
            # Try to get price
            price = ""
            try:
                price_element = link_element.find_element(By.CSS_SELECTOR, '[class*="price"], .price, [class*="cost"]')
                price = price_element.text.strip()
            except:
                pass
            
            # Try to get grader and grade
            grader = ""
            grade = ""
            try:
                grader_element = link_element.find_element(By.CSS_SELECTOR, '[class*="grader"], [class*="grade"]')
                grader_text = grader_element.text.strip()
                if 'CGC' in grader_text:
                    grader = 'CGC'
                elif 'PSA' in grader_text:
                    grader = 'PSA'
                elif 'BGS' in grader_text:
                    grader = 'BGS'
                
                # Extract grade number
                import re
                grade_match = re.search(r'(\d+(?:\.\d+)?)', grader_text)
                if grade_match:
                    grade = grade_match.group(1)
            except:
                pass
            
            return {
                'listing_url': card_url,
                'full_listing_name': card_name,
                'pokemon_name': card_name,
                'grader': grader,
                'grade': grade,
                'price': price,
                'fmv': '',
                'set': '',
                'number': '',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return None
    
    def save_data(self, force=False):
        """Save data to files"""
        current_time = datetime.now()
        
        # Save if forced or if enough time has passed
        if force or (current_time - self.last_save_time).seconds >= self.save_interval:
            try:
                # Save JSON
                with open('phygitals_marketplace_complete.json', 'w', encoding='utf-8') as f:
                    json.dump(self.all_cards, f, indent=2, ensure_ascii=False)
                
                # Save CSV
                if self.all_cards:
                    df = pd.DataFrame(self.all_cards)
                    df.to_csv('phygitals_marketplace_complete.csv', index=False)
                    
                    # Save Excel
                    df.to_excel('phygitals_marketplace_complete.xlsx', index=False)
                
                self.last_save_time = current_time
                print(f"Saved {len(self.all_cards)} cards to files")
                return True
                
            except Exception as e:
                print(f"Error saving data: {e}")
                return False
        
        return True
    
    def load_existing_data(self):
        """Load existing data if available"""
        try:
            if os.path.exists('phygitals_marketplace_complete.json'):
                with open('phygitals_marketplace_complete.json', 'r', encoding='utf-8') as f:
                    self.all_cards = json.load(f)
                print(f"Loaded {len(self.all_cards)} existing cards")
                return True
        except Exception as e:
            print(f"Could not load existing data: {e}")
        
        return False
    
    def run_continuous_scrape(self):
        """Run continuous scraping in background"""
        print("Starting Background Scraper")
        print("=" * 50)
        
        if not self.setup_driver():
            return False
        
        # Load existing data
        self.load_existing_data()
        
        page = 1
        consecutive_failures = 0
        max_failures = 5
        
        try:
            while True:
                print(f"\nStarting scrape cycle at {datetime.now().strftime('%H:%M:%S')}")
                
                # Scrape pages until we hit failures or no more data
                while consecutive_failures < max_failures:
                    success = self.scrape_page(page)
                    
                    if success:
                        consecutive_failures = 0
                        page += 1
                        
                        # Save data periodically
                        self.save_data()
                        
                        # Small delay between pages
                        time.sleep(2)
                    else:
                        consecutive_failures += 1
                        print(f"  Failed to scrape page {page} ({consecutive_failures}/{max_failures})")
                        
                        # Try next page
                        page += 1
                        time.sleep(5)
                
                # Reset for next cycle
                consecutive_failures = 0
                page = 1
                
                # Final save
                self.save_data(force=True)
                
                print(f"Waiting {self.scrape_interval} seconds before next cycle...")
                time.sleep(self.scrape_interval)
                
        except KeyboardInterrupt:
            print("\nScraper stopped by user")
        except Exception as e:
            print(f"\nScraper error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            self.save_data(force=True)
            print("Background scraper finished")

def main():
    scraper = BackgroundScraper()
    scraper.run_continuous_scrape()

if __name__ == "__main__":
    main()
