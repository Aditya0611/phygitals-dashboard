"""
COMPLETE Phygitals Card Scraper
Scrapes ALL cards from ALL Pokemon pages with full details
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
from datetime import datetime

class CompleteCardScraper:
    def __init__(self, start_pokemon=1, end_pokemon=1025):
        self.base_pokemon_url = "https://www.phygitals.com/pokemon/"
        self.start_pokemon = start_pokemon
        self.end_pokemon = end_pokemon
        self.all_cards = []
        self.driver = None
        self.stats = {
            'pokemon_processed': 0,
            'cards_found': 0,
            'cards_scraped': 0,
            'start_time': None
        }
        
    def setup_selenium(self):
        """Setup Chrome"""
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
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("Chrome ready!")
        
    def load_existing_progress(self):
        """Load existing progress if available"""
        try:
            with open('all_cards_progress.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.all_cards = data.get('cards', [])
                self.stats = data.get('stats', self.stats)
                print(f"\nLoaded existing progress:")
                print(f"  Pokemon processed: {self.stats['pokemon_processed']}")
                print(f"  Cards scraped: {len(self.all_cards)}")
                
                # Resume from where we left off
                if self.stats['pokemon_processed'] > 0:
                    self.start_pokemon = self.stats['pokemon_processed'] + 1
                    print(f"  Resuming from Pokemon #{self.start_pokemon}")
        except FileNotFoundError:
            print("\nNo existing progress found. Starting fresh.")
        except Exception as e:
            print(f"\nError loading progress: {e}")
    
    def scrape_all_pokemon(self):
        """Main scraping function"""
        self.stats['start_time'] = datetime.now().isoformat()
        
        try:
            self.setup_selenium()
            
            for pokemon_id in range(self.start_pokemon, self.end_pokemon + 1):
                # Restart browser every 50 Pokemon to prevent memory issues
                if (pokemon_id - self.start_pokemon) % 50 == 0 and pokemon_id != self.start_pokemon:
                    print("\nRefreshing browser...")
                    self.setup_selenium()
                
                print(f"\n{'='*70}")
                print(f"Pokemon {pokemon_id}/{self.end_pokemon}")
                print(f"{'='*70}")
                
                try:
                    # Get card URLs from Pokemon page
                    card_urls = self.get_card_urls_from_pokemon(pokemon_id)
                    
                    if card_urls:
                        print(f"Found {len(card_urls)} cards")
                        self.stats['cards_found'] += len(card_urls)
                        
                        # Scrape each card
                        for i, card_data in enumerate(card_urls, 1):
                            print(f"  [{i}/{len(card_urls)}] Scraping card...")
                            
                            card_details = self.scrape_card_page(card_data)
                            if card_details:
                                self.all_cards.append(card_details)
                                self.stats['cards_scraped'] += 1
                                print(f"    OK - {card_details.get('grader', 'N/A')} {card_details.get('grade', '')} - {card_details.get('current_price', 'N/A')}")
                            
                            time.sleep(0.5)
                    else:
                        print("No cards found")
                    
                    self.stats['pokemon_processed'] = pokemon_id
                    
                    # Save progress every 10 Pokemon
                    if pokemon_id % 10 == 0:
                        self.save_progress()
                        self.print_stats()
                    
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    print("\n\nStopped by user!")
                    raise
                except Exception as e:
                    print(f"Error with Pokemon {pokemon_id}: {e}")
                    continue
                    
        except KeyboardInterrupt:
            print("\n\nInterrupted! Saving progress...")
        finally:
            if self.driver:
                self.driver.quit()
            
            self.save_progress()
            print("\nBrowser closed")
    
    def get_card_urls_from_pokemon(self, pokemon_id):
        """Get all card listing URLs from a Pokemon page"""
        pokemon_url = f"{self.base_pokemon_url}{pokemon_id}"
        card_urls = []
        
        try:
            self.driver.get(pokemon_url)
            time.sleep(3)
            
            # Get Pokemon name
            try:
                pokemon_name = self.driver.find_element(By.TAG_NAME, 'h1').text
                print(f"Pokemon: {pokemon_name}")
            except:
                pokemon_name = f"Pokemon_{pokemon_id}"
            
            # Scroll to load cards
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            # Find all card links
            card_links = set()
            
            # Method 1: XPath
            try:
                links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/card/' in href:
                        card_links.add(href)
            except:
                pass
            
            # Method 2: CSS
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/card/"]')
                for link in links:
                    href = link.get_attribute('href')
                    if href:
                        card_links.add(href)
            except:
                pass
            
            # Method 3: Parse source
            if not card_links:
                page_source = self.driver.page_source
                pattern = r'href="(/card/[^"]+)"'
                matches = re.findall(pattern, page_source)
                for m in matches:
                    card_links.add(f"https://www.phygitals.com{m}")
            
            # Create card data objects
            for url in card_links:
                card_urls.append({
                    'card_url': url,
                    'pokemon_name': pokemon_name,
                    'pokemon_id': pokemon_id,
                    'pokemon_url': pokemon_url
                })
            
            return card_urls
            
        except Exception as e:
            print(f"Error getting cards: {e}")
            return []
    
    def scrape_card_page(self, card_data):
        """Scrape individual card listing page"""
        try:
            self.driver.get(card_data['card_url'])
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            card = {
                'listing_url': card_data['card_url'],
                'pokemon_name': card_data['pokemon_name'],
                'pokemon_id': card_data['pokemon_id'],
                'pokemon_url': card_data['pokemon_url'],
                'full_listing_name': '',
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
            
            # Extract set from title
            if card['full_listing_name']:
                # Try to extract set name
                set_match = re.search(r'Pokemon\s+([A-Za-z\s]+?)(?:\s+#|\s+\d{4})', card['full_listing_name'], re.IGNORECASE)
                if set_match:
                    card['card_set'] = set_match.group(1).strip()
            
            return card
            
        except Exception as e:
            return None
    
    def save_progress(self):
        """Save progress"""
        progress_data = {
            'cards': self.all_cards,
            'stats': self.stats,
            'last_updated': datetime.now().isoformat()
        }
        
        with open('all_cards_progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n*** Progress saved: {len(self.all_cards)} cards ***")
    
    def print_stats(self):
        """Print statistics"""
        print("\n" + "="*70)
        print("PROGRESS STATS")
        print("="*70)
        print(f"Pokemon processed: {self.stats['pokemon_processed']}/{self.end_pokemon}")
        print(f"Card links found: {self.stats['cards_found']}")
        print(f"Cards scraped: {self.stats['cards_scraped']}")
        
        if self.stats['start_time']:
            start = datetime.fromisoformat(self.stats['start_time'])
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed > 0:
                rate = self.stats['pokemon_processed'] / (elapsed / 60)
                remaining = (self.end_pokemon - self.stats['pokemon_processed']) / rate if rate > 0 else 0
                print(f"Rate: {rate:.1f} Pokemon/min")
                print(f"Estimated time remaining: {remaining:.0f} minutes")
        
        print("="*70)
    
    def save_final(self):
        """Save final results"""
        print("\n" + "="*70)
        print("SAVING FINAL DATA")
        print("="*70)
        
        if not self.all_cards:
            print("No cards to save!")
            return
        
        # JSON
        with open('phygitals_all_cards_complete.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_cards, f, indent=2, ensure_ascii=False)
        print("Saved: phygitals_all_cards_complete.json")
        
        # Excel
        df = pd.DataFrame(self.all_cards)
        
        # Reorder columns
        columns_order = [
            'listing_url',
            'full_listing_name',
            'pokemon_name',
            'pokemon_id',
            'grader',
            'grade',
            'current_price',
            'fmv',
            'card_set',
            'card_number',
            'pokemon_url',
            'condition',
            'seller'
        ]
        
        existing_cols = [col for col in columns_order if col in df.columns]
        df = df[existing_cols]
        
        df.to_excel('phygitals_all_cards_complete.xlsx', index=False)
        print("Saved: phygitals_all_cards_complete.xlsx")
        
        # CSV
        df.to_csv('phygitals_all_cards_complete.csv', index=False, encoding='utf-8')
        print("Saved: phygitals_all_cards_complete.csv")
        
        # Stats
        print("\n" + "="*70)
        print("FINAL STATISTICS")
        print("="*70)
        print(f"Total cards: {len(self.all_cards)}")
        print(f"Pokemon processed: {self.stats['pokemon_processed']}")
        
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
            
            # Pokemon
            top_pokemon = df['pokemon_name'].value_counts().head(10)
            print("\nTop 10 Pokemon by card count:")
            for pokemon, count in top_pokemon.items():
                print(f"  {pokemon}: {count} cards")
        
        print("="*70)


def main():
    print("""
    ==============================================================
       COMPLETE Phygitals Card Scraper
       Scrapes ALL cards from ALL Pokemon with full details
    ==============================================================
    """)
    
    print("\nThis will scrape:")
    print("  - All Pokemon (1-1025)")
    print("  - All card listings from each Pokemon")
    print("  - Complete details for every card")
    print("\nEstimated time: 2-4 hours")
    print("Progress auto-saves every 10 Pokemon")
    print("You can stop anytime with Ctrl+C\n")
    
    # Check for existing progress
    scraper = CompleteCardScraper(start_pokemon=1, end_pokemon=1025)
    scraper.load_existing_progress()
    
    print("\nStarting in 5 seconds...")
    time.sleep(5)
    
    try:
        scraper.scrape_all_pokemon()
    except KeyboardInterrupt:
        print("\nStopped by user!")
    
    scraper.save_final()
    scraper.print_stats()
    
    print("\nDONE!")


if __name__ == "__main__":
    main()


