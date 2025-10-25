"""
Complete Card Listings Scraper
Scrapes individual card listing pages with full details:
- Listing URL (https://www.phygitals.com/card/...)
- Grader (PSA, CGC, etc.)
- Grade
- FMV
- Current Price
- Full listing name
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re

class CardListingsScraper:
    def __init__(self, start_pokemon=1, end_pokemon=151):
        self.base_pokemon_url = "https://www.phygitals.com/pokemon/"
        self.start_pokemon = start_pokemon
        self.end_pokemon = end_pokemon
        self.all_card_listings = []
        self.driver = None
        
    def setup_selenium(self):
        """Setup Chrome WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        print("Setting up Chrome...")
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Commented for debugging
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("Chrome ready!\n")
    
    def scrape_all_pokemon(self):
        """Main scraping function"""
        try:
            self.setup_selenium()
            
            for pokemon_id in range(self.start_pokemon, self.end_pokemon + 1):
                print(f"\n{'='*70}")
                print(f"POKEMON {pokemon_id}/{self.end_pokemon}")
                print(f"{'='*70}")
                
                # Restart browser every 25 Pokemon to prevent crashes
                if (pokemon_id - self.start_pokemon) % 25 == 0 and pokemon_id != self.start_pokemon:
                    print("Refreshing browser...")
                    self.setup_selenium()
                
                pokemon_url = f"{self.base_pokemon_url}{pokemon_id}"
                print(f"Pokemon Page: {pokemon_url}")
                
                try:
                    # Step 1: Get all card URLs from Pokemon page
                    card_urls = self.get_card_urls_from_pokemon_page(pokemon_url, pokemon_id)
                    
                    if not card_urls:
                        print("No card listings found")
                        continue
                    
                    print(f"Found {len(card_urls)} card listings\n")
                    
                    # Step 2: Visit each card listing page and extract details
                    for i, card_url_data in enumerate(card_urls, 1):
                        print(f"  [{i}/{len(card_urls)}] {card_url_data['card_url']}")
                        
                        card_details = self.scrape_card_listing_page(card_url_data)
                        
                        if card_details:
                            self.all_card_listings.append(card_details)
                            print(f"      Grader: {card_details.get('grader', 'N/A')}, "
                                  f"Grade: {card_details.get('grade', 'N/A')}, "
                                  f"Price: {card_details.get('current_price', 'N/A')}")
                        
                        time.sleep(0.5)  # Small delay between cards
                    
                    # Save progress
                    if pokemon_id % 10 == 0:
                        self.save_progress(pokemon_id)
                    
                    time.sleep(1)  # Delay between Pokemon pages
                    
                except KeyboardInterrupt:
                    print("\n\nStopped by user!")
                    raise
                except Exception as e:
                    print(f"Error with Pokemon {pokemon_id}: {e}")
                    continue
                    
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
    
    def get_card_urls_from_pokemon_page(self, pokemon_url, pokemon_id):
        """Extract all card listing URLs from a Pokemon page"""
        try:
            self.driver.get(pokemon_url)
            
            # Get Pokemon name
            try:
                pokemon_name = self.driver.find_element(By.TAG_NAME, 'h1').text
                print(f"Pokemon: {pokemon_name}")
            except:
                pokemon_name = f"Pokemon_{pokemon_id}"
            
            # IMPORTANT: Wait for card listings to load
            print("Waiting for card listings to load...")
            time.sleep(5)
            
            # Scroll multiple times to trigger lazy loading
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                print(f"  Scroll {i+1}/5...")
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Try multiple strategies to find card links
            card_urls = []
            
            # Strategy 1: Find by XPath - any link with /card/ in href
            try:
                print("Searching for card links...")
                xpath_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
                print(f"  Found {len(xpath_links)} potential card links via XPath")
                
                for link in xpath_links:
                    try:
                        href = link.get_attribute('href')
                        card_name = link.text.strip() or link.get_attribute('aria-label') or ''
                        
                        if href and '/card/' in href:
                            card_urls.append({
                                'card_url': href,
                                'pokemon_name': pokemon_name,
                                'pokemon_id': pokemon_id,
                                'pokemon_url': pokemon_url,
                                'preview_name': card_name[:100]  # Limit length
                            })
                    except:
                        continue
            except Exception as e:
                print(f"  XPath strategy error: {e}")
            
            # Strategy 2: Find by CSS selector
            try:
                css_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/card/"]')
                print(f"  Found {len(css_links)} potential card links via CSS")
                
                for link in css_links:
                    try:
                        href = link.get_attribute('href')
                        card_name = link.text.strip()
                        
                        if href and '/card/' in href:
                            card_urls.append({
                                'card_url': href,
                                'pokemon_name': pokemon_name,
                                'pokemon_id': pokemon_id,
                                'pokemon_url': pokemon_url,
                                'preview_name': card_name[:100]
                            })
                    except:
                        continue
            except Exception as e:
                print(f"  CSS strategy error: {e}")
            
            # Strategy 3: Check page source for /card/ URLs
            if not card_urls:
                print("  Trying page source analysis...")
                page_source = self.driver.page_source
                
                # Find all /card/ URLs in page source
                import re
                card_url_pattern = r'(?:href="|href\\"=\\")([^"]*?/card/[^"]*?)(?:"|\\)'
                matches = re.findall(card_url_pattern, page_source)
                
                print(f"  Found {len(matches)} URLs in page source")
                
                for match in matches:
                    # Clean up the URL
                    url = match.replace('\\', '')
                    if not url.startswith('http'):
                        url = 'https://www.phygitals.com' + url
                    
                    card_urls.append({
                        'card_url': url,
                        'pokemon_name': pokemon_name,
                        'pokemon_id': pokemon_id,
                        'pokemon_url': pokemon_url,
                        'preview_name': ''
                    })
            
            # Save debug HTML
            debug_file = f'debug_cards_pokemon_{pokemon_id}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"  Saved debug: {debug_file}")
            
            # Remove duplicates based on URL
            seen = set()
            unique_cards = []
            for card in card_urls:
                if card['card_url'] not in seen:
                    seen.add(card['card_url'])
                    unique_cards.append(card)
            
            return unique_cards
            
        except Exception as e:
            print(f"Error getting card URLs: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def scrape_card_listing_page(self, card_url_data):
        """Scrape details from individual card listing page"""
        try:
            self.driver.get(card_url_data['card_url'])
            time.sleep(3)  # Wait for page to load
            
            # Parse page source
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract card details
            card_details = {
                'listing_url': card_url_data['card_url'],
                'pokemon_name': card_url_data['pokemon_name'],
                'pokemon_id': card_url_data['pokemon_id'],
                'pokemon_url': card_url_data['pokemon_url'],
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
            
            # Get full listing name from h1 or title
            try:
                title_elem = soup.find('h1')
                if title_elem:
                    card_details['full_listing_name'] = title_elem.get_text(strip=True)
                else:
                    # Try meta title
                    meta_title = soup.find('meta', property='og:title')
                    if meta_title:
                        card_details['full_listing_name'] = meta_title.get('content', '')
            except:
                pass
            
            # Extract all text content for parsing
            page_text = soup.get_text()
            
            # Extract grader (PSA, CGC, BGS, etc.)
            grader_match = re.search(r'\b(PSA|CGC|BGS|Beckett|Raw|Ungraded)\b', page_text, re.IGNORECASE)
            if grader_match:
                card_details['grader'] = grader_match.group(1).upper()
            
            # Extract grade number (e.g., "PSA 10", "CGC 9.5")
            grade_match = re.search(r'(?:PSA|CGC|BGS)\s*(\d+(?:\.\d+)?)', page_text, re.IGNORECASE)
            if grade_match:
                card_details['grade'] = grade_match.group(1)
            
            # Extract prices
            # Look for price elements
            price_elements = soup.find_all(string=re.compile(r'\$[\d,]+\.?\d*'))
            prices = []
            for elem in price_elements:
                price_matches = re.findall(r'\$[\d,]+\.?\d*', elem)
                prices.extend(price_matches)
            
            # Deduplicate prices
            unique_prices = list(dict.fromkeys(prices))
            
            if unique_prices:
                # First price is usually current price
                card_details['current_price'] = unique_prices[0]
                
                # Look for FMV specifically
                fmv_match = re.search(r'(?:FMV|Fair Market Value|Market Price)[:\s]*(\$[\d,]+\.?\d*)', page_text, re.IGNORECASE)
                if fmv_match:
                    card_details['fmv'] = fmv_match.group(1)
                elif len(unique_prices) > 1:
                    card_details['fmv'] = unique_prices[1]
            
            # Extract card set and number
            set_match = re.search(r'([A-Za-z\s]+)\s+#(\d+)', card_details['full_listing_name'])
            if set_match:
                card_details['card_set'] = set_match.group(1).strip()
                card_details['card_number'] = set_match.group(2)
            
            # Use Selenium to find specific elements
            try:
                # Try to find price with common class names or data attributes
                price_selectors = [
                    "[class*='price']",
                    "[data-price]",
                    "[class*='cost']",
                    "span[class*='amount']"
                ]
                
                for selector in price_selectors:
                    try:
                        price_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        text = price_elem.text
                        if '$' in text and not card_details['current_price']:
                            card_details['current_price'] = text.strip()
                            break
                    except:
                        continue
            except:
                pass
            
            return card_details if card_details['full_listing_name'] else None
            
        except Exception as e:
            print(f"      Error: {e}")
            return None
    
    def scroll_page(self):
        """Scroll page to load all content"""
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
    
    def save_progress(self, pokemon_id):
        """Save progress"""
        filename = f"card_listings_progress_{pokemon_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_card_listings, f, indent=2, ensure_ascii=False)
        print(f"\n*** Progress saved: {filename} ({len(self.all_card_listings)} cards) ***\n")
    
    def save_final(self):
        """Save final results"""
        print("\n" + "="*70)
        print("SAVING FINAL DATA")
        print("="*70)
        
        # JSON
        with open('phygitals_card_listings_complete.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_card_listings, f, indent=2, ensure_ascii=False)
        print("Saved: phygitals_card_listings_complete.json")
        
        # Excel
        df = pd.DataFrame(self.all_card_listings)
        
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
            'pokemon_id',
            'pokemon_url',
            'seller'
        ]
        
        existing_cols = [col for col in columns_order if col in df.columns]
        df = df[existing_cols]
        
        df.to_excel('phygitals_card_listings_complete.xlsx', index=False)
        print("Saved: phygitals_card_listings_complete.xlsx")
        
        # CSV
        df.to_csv('phygitals_card_listings_complete.csv', index=False, encoding='utf-8')
        print("Saved: phygitals_card_listings_complete.csv")
        
        print(f"\nTotal card listings: {len(self.all_card_listings)}")
        print("="*70)


def main():
    print("""
    ==============================================================
       Card Listings Scraper - Complete Details
       Extracts individual card listings with all details
    ==============================================================
    """)
    
    print("\nOptions:")
    print("1. First 10 Pokemon (testing)")
    print("2. First 50 Pokemon")
    print("3. Generation 1 (Pokemon 1-151)")
    print("4. Custom range")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        scraper = CardListingsScraper(start_pokemon=1, end_pokemon=10)
    elif choice == "2":
        scraper = CardListingsScraper(start_pokemon=1, end_pokemon=50)
    elif choice == "3":
        scraper = CardListingsScraper(start_pokemon=1, end_pokemon=151)
    else:
        start = int(input("Start from Pokemon ID: "))
        end = int(input("End at Pokemon ID: "))
        scraper = CardListingsScraper(start_pokemon=start, end_pokemon=end)
    
    print("\nStarting scraper...")
    print("TIP: Press Ctrl+C to stop (progress auto-saves every 10 Pokemon)\n")
    
    try:
        scraper.scrape_all_pokemon()
    except KeyboardInterrupt:
        print("\n\nStopped by user!")
    
    scraper.save_final()
    print("\nDONE!")


if __name__ == "__main__":
    main()

