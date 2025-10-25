"""
Phygitals Marketplace Scraper
Scrapes Pokemon listings with prices, FMV, and full listing names
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
import re

class PhygitalsMarketplaceScraper:
    def __init__(self):
        self.base_url = "https://www.phygitals.com/pokemon/generation/"
        self.generations = range(1, 10)  # Gen 1-9
        self.all_listings = []
        self.driver = None
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome"""
        print("Setting up Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("Chrome WebDriver ready!")
        
    def scrape_all_generations(self):
        """Scrape all Pokemon and their listings from all generations"""
        try:
            self.setup_selenium()
            
            # First, collect all Pokemon URLs
            print("\n" + "="*70)
            print("PHASE 1: Collecting all Pokemon URLs")
            print("="*70)
            
            all_pokemon_urls = []
            
            for gen in self.generations:
                generation_url = f"{self.base_url}{gen}"
                print(f"\nGeneration {gen}: {generation_url}")
                
                pokemon_urls = self.get_pokemon_urls_from_generation(generation_url, gen)
                all_pokemon_urls.extend(pokemon_urls)
                
                print(f"Found {len(pokemon_urls)} Pokemon URLs")
                time.sleep(1)
            
            print(f"\nTotal Pokemon found: {len(all_pokemon_urls)}")
            
            # Now scrape each Pokemon's marketplace page
            print("\n" + "="*70)
            print("PHASE 2: Scraping marketplace listings from each Pokemon")
            print("="*70)
            
            for i, pokemon_data in enumerate(all_pokemon_urls, 1):
                print(f"\n[{i}/{len(all_pokemon_urls)}] Scraping: {pokemon_data['name']}")
                print(f"   URL: {pokemon_data['url']}")
                
                listings = self.scrape_pokemon_listings(pokemon_data)
                
                if listings:
                    print(f"   Found {len(listings)} listings")
                    self.all_listings.extend(listings)
                else:
                    print(f"   No listings found")
                
                # Rate limiting - be respectful
                time.sleep(2)
                
                # Save progress every 50 Pokemon
                if i % 50 == 0:
                    self.save_progress(i)
                
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
        
        return self.all_listings
    
    def get_pokemon_urls_from_generation(self, url, generation):
        """Get all Pokemon URLs from a generation page"""
        pokemon_urls = []
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Scroll to load all content
            self.scroll_to_bottom()
            
            # Parse page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all Pokemon links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                
                # Look for Pokemon detail pages (e.g., /pokemon/1, /pokemon/25)
                if re.match(r'^/pokemon/\d+$', href):
                    full_url = 'https://www.phygitals.com' + href
                    
                    # Get Pokemon name
                    img = link.find('img')
                    name = ''
                    if img:
                        name = img.get('alt', '')
                    
                    if not name:
                        name = link.get_text(strip=True)
                    
                    pokemon_urls.append({
                        'url': full_url,
                        'name': name,
                        'generation': generation,
                        'pokemon_id': href.split('/')[-1]
                    })
            
            # Remove duplicates
            seen = set()
            unique_pokemon = []
            for p in pokemon_urls:
                if p['url'] not in seen:
                    seen.add(p['url'])
                    unique_pokemon.append(p)
            
            return unique_pokemon
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []
    
    def scrape_pokemon_listings(self, pokemon_data):
        """Scrape marketplace listings for a specific Pokemon"""
        listings = []
        
        try:
            self.driver.get(pokemon_data['url'])
            time.sleep(3)
            
            # Scroll to load all listings
            self.scroll_to_bottom()
            
            # Get page source
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Save debug HTML for first few Pokemon
            if len(self.all_listings) < 5:
                debug_file = f"debug_pokemon_{pokemon_data['pokemon_id']}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"   Saved debug HTML: {debug_file}")
            
            # Try multiple strategies to find listings
            listings = self.extract_listings_multiple_strategies(soup, pokemon_data)
            
            # If no listings found, try Selenium direct extraction
            if not listings:
                listings = self.extract_listings_with_selenium(pokemon_data)
            
        except Exception as e:
            print(f"   ❌ Error scraping listings: {e}")
        
        return listings
    
    def extract_listings_multiple_strategies(self, soup, pokemon_data):
        """Try multiple strategies to extract marketplace listings"""
        listings = []
        
        # Strategy 1: Look for card listings with price patterns
        print("   Strategy 1: Looking for card/listing elements...")
        
        # Common selectors for marketplace listings
        selectors = [
            'div[class*="card"]',
            'div[class*="listing"]',
            'div[class*="item"]',
            'article',
            'li[class*="list"]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            
            for elem in elements:
                listing = self.parse_listing_element(elem, pokemon_data)
                if listing:
                    listings.append(listing)
            
            if listings:
                print(f"   Strategy 1 worked with selector: {selector}")
                break
        
        # Strategy 2: Look for price indicators
        if not listings:
            print("   Strategy 2: Looking for price elements...")
            
            # Find all elements with $ or price-like patterns
            price_elements = soup.find_all(string=re.compile(r'\$[\d,]+\.?\d*'))
            
            for price_elem in price_elements:
                parent = price_elem.find_parent()
                
                if parent:
                    # Get surrounding context
                    listing_container = parent.find_parent(['div', 'article', 'li'])
                    
                    if listing_container:
                        listing = self.parse_listing_element(listing_container, pokemon_data)
                        if listing:
                            listings.append(listing)
        
        # Remove duplicates
        listings = self.remove_duplicate_listings(listings)
        
        return listings
    
    def extract_listings_with_selenium(self, pokemon_data):
        """Extract listings using Selenium element finding"""
        listings = []
        
        try:
            print("   Strategy 3: Using Selenium element detection...")
            
            # Find all clickable/interactive elements
            elements = self.driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'cursor-pointer') or contains(@class, 'hover') or @role='button']")
            
            for elem in elements:
                try:
                    if not elem.is_displayed():
                        continue
                    
                    text = elem.text.strip()
                    
                    # Look for price indicators in text
                    if '$' in text or 'FMV' in text or 'price' in text.lower():
                        # Extract data
                        listing = {
                            'pokemon_name': pokemon_data['name'],
                            'pokemon_url': pokemon_data['url'],
                            'generation': pokemon_data['generation'],
                            'listing_name': '',
                            'listing_price': '',
                            'fmv': '',
                            'full_text': text
                        }
                        
                        # Try to parse price and FMV
                        price_matches = re.findall(r'\$[\d,]+\.?\d*', text)
                        if price_matches:
                            listing['listing_price'] = price_matches[0]
                            if len(price_matches) > 1:
                                listing['fmv'] = price_matches[1]
                        
                        # Get listing name (first line or heading)
                        lines = text.split('\n')
                        if lines:
                            listing['listing_name'] = lines[0]
                        
                        if listing['listing_price'] or listing['fmv']:
                            listings.append(listing)
                        
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"   ❌ Selenium extraction error: {e}")
        
        return listings
    
    def parse_listing_element(self, element, pokemon_data):
        """Parse a listing element to extract price and details"""
        try:
            text = element.get_text(strip=True)
            
            # Skip if no price indicator
            if '$' not in text and 'fmv' not in text.lower():
                return None
            
            listing = {
                'pokemon_name': pokemon_data['name'],
                'pokemon_url': pokemon_data['url'],
                'generation': pokemon_data['generation'],
                'listing_name': '',
                'listing_price': '',
                'fmv': '',
                'condition': '',
                'seller': '',
                'full_text': text
            }
            
            # Extract listing name/title
            heading = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                listing['listing_name'] = heading.get_text(strip=True)
            else:
                # Use first line of text
                lines = text.split('\n')
                if lines:
                    listing['listing_name'] = lines[0]
            
            # Extract prices
            price_matches = re.findall(r'\$[\d,]+\.?\d*', text)
            if price_matches:
                listing['listing_price'] = price_matches[0]
                
                # If multiple prices, check for FMV
                if len(price_matches) > 1:
                    # Check if "FMV" label exists near second price
                    if 'fmv' in text.lower():
                        listing['fmv'] = price_matches[1]
                    else:
                        # Assume second price might be FMV
                        listing['fmv'] = price_matches[1]
            
            # Look for explicit FMV label
            fmv_match = re.search(r'FMV[:\s]*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
            if fmv_match:
                listing['fmv'] = f"${fmv_match.group(1)}"
            
            # Look for condition (PSA, BGS, CGC, Raw, etc.)
            condition_match = re.search(r'(PSA|BGS|CGC|Raw|Graded|Ungraded)\s*\d*', text, re.IGNORECASE)
            if condition_match:
                listing['condition'] = condition_match.group(0)
            
            # Only return if we have a price
            if listing['listing_price']:
                return listing
            
        except Exception as e:
            pass
        
        return None
    
    def remove_duplicate_listings(self, listings):
        """Remove duplicate listings"""
        seen = set()
        unique = []
        
        for listing in listings:
            key = (listing['listing_name'], listing['listing_price'], listing['fmv'])
            if key not in seen:
                seen.add(key)
                unique.append(listing)
        
        return unique
    
    def scroll_to_bottom(self):
        """Scroll to bottom of page"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(5):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def save_progress(self, count):
        """Save progress periodically"""
        temp_file = f"marketplace_progress_{count}.json"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print(f"\nProgress saved: {temp_file} ({len(self.all_listings)} listings)")
    
    def save_to_excel(self, filename="phygitals_marketplace_listings.xlsx"):
        """Save scraped data to Excel"""
        if not self.all_listings:
            print("❌ No data to save")
            return
        
        df = pd.DataFrame(self.all_listings)
        
        # Reorder columns
        columns_order = [
            'pokemon_name',
            'listing_name',
            'listing_price',
            'fmv',
            'condition',
            'generation',
            'pokemon_url',
            'seller',
            'full_text'
        ]
        
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]
        
        # Save to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Marketplace Listings', index=False)
            
            # Auto-adjust columns
            worksheet = writer.sheets['Marketplace Listings']
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        print(f"\nSaved {len(self.all_listings)} listings to {filename}")
    
    def save_to_csv(self, filename="phygitals_marketplace_listings.csv"):
        """Save to CSV"""
        if self.all_listings:
            df = pd.DataFrame(self.all_listings)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Saved {len(self.all_listings)} listings to {filename}")
    
    def save_to_json(self, filename="phygitals_marketplace_listings.json"):
        """Save to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.all_listings)} listings to {filename}")
    
    def print_summary(self):
        """Print summary"""
        print("\n" + "="*70)
        print("MARKETPLACE SCRAPING SUMMARY")
        print("="*70)
        print(f"Total listings found: {len(self.all_listings)}")
        
        if self.all_listings:
            # Count by generation
            gen_counts = {}
            for listing in self.all_listings:
                gen = listing.get('generation', 'Unknown')
                gen_counts[gen] = gen_counts.get(gen, 0) + 1
            
            print("\nListings per Generation:")
            for gen in sorted(gen_counts.keys()):
                print(f"  Generation {gen}: {gen_counts[gen]} listings")
            
            # Show sample
            print("\nSample Listings (first 10):")
            print(f"{'Pokemon':<20} {'Listing':<30} {'Price':<12} {'FMV':<12}")
            print("-" * 74)
            
            for listing in self.all_listings[:10]:
                pokemon = listing.get('pokemon_name', 'Unknown')[:18]
                name = listing.get('listing_name', 'N/A')[:28]
                price = listing.get('listing_price', 'N/A')[:10]
                fmv = listing.get('fmv', 'N/A')[:10]
                print(f"{pokemon:<20} {name:<30} {price:<12} {fmv:<12}")
        
        print("="*70)


def main():
    print("""
    ==============================================================
       Phygitals Marketplace Scraper v1.0
       Scrapes listings with prices and FMV
    ==============================================================
    """)
    
    scraper = PhygitalsMarketplaceScraper()
    
    print("Starting marketplace scraping...")
    print("WARNING: This will take a while - scraping individual Pokemon pages")
    print()
    
    scraper.scrape_all_generations()
    
    if scraper.all_listings:
        print("\n" + "="*70)
        print("SAVING DATA...")
        print("="*70)
        
        scraper.save_to_excel()
        scraper.save_to_csv()
        scraper.save_to_json()
        
        scraper.print_summary()
        
        print("\nSCRAPING COMPLETE!")
        print("\nOutput files:")
        print("   • phygitals_marketplace_listings.xlsx (Excel)")
        print("   • phygitals_marketplace_listings.csv (CSV)")
        print("   • phygitals_marketplace_listings.json (JSON)")
    else:
        print("\nNo marketplace listings found")
        print("TIP: Check debug_pokemon_*.html files to inspect page structure")


if __name__ == "__main__":
    main()

