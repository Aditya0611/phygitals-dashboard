"""
Phygitals Pokemon Scraper
Scrapes all Pokemon data from all generations
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd

class PhygitalsPokemonScraper:
    def __init__(self):
        self.base_url = "https://www.phygitals.com/pokemon/generation/"
        self.generations = range(1, 10)  # Gen 1-9
        self.all_pokemon = []
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    
    def scrape_with_selenium(self):
        """Scrape using Selenium (for JavaScript-rendered content)"""
        print("🚀 Starting Selenium scraper...")
        driver = self.setup_selenium()
        
        try:
            for gen in self.generations:
                url = f"{self.base_url}{gen}"
                print(f"\n📦 Scraping Generation {gen}: {url}")
                
                driver.get(url)
                time.sleep(3)  # Wait for page to load
                
                # Scroll to load all content
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                # Extract Pokemon cards
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                pokemon_data = self.extract_pokemon_data(soup, gen)
                
                print(f"✅ Found {len(pokemon_data)} Pokemon in Generation {gen}")
                self.all_pokemon.extend(pokemon_data)
                
                time.sleep(2)  # Be respectful to server
                
        finally:
            driver.quit()
        
        return self.all_pokemon
    
    def scrape_with_requests(self):
        """Scrape using requests (faster, but may miss JS content)"""
        print("🚀 Starting requests scraper...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        for gen in self.generations:
            url = f"{self.base_url}{gen}"
            print(f"\n📦 Scraping Generation {gen}: {url}")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                pokemon_data = self.extract_pokemon_data(soup, gen)
                
                print(f"✅ Found {len(pokemon_data)} Pokemon in Generation {gen}")
                self.all_pokemon.extend(pokemon_data)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error scraping Gen {gen}: {e}")
        
        return self.all_pokemon
    
    def extract_pokemon_data(self, soup, generation):
        """Extract Pokemon data from BeautifulSoup object"""
        pokemon_list = []
        
        # Try multiple selectors to find Pokemon cards
        # Common patterns for card listings
        selectors = [
            'div[class*="card"]',
            'div[class*="pokemon"]',
            'div[class*="item"]',
            'article',
            'a[href*="/pokemon/"]',
            'img[alt*="pokemon" i]',
        ]
        
        for selector in selectors:
            cards = soup.select(selector)
            if cards and len(cards) > 10:  # If we find substantial results
                print(f"   Using selector: {selector}")
                
                for card in cards:
                    pokemon = self.parse_pokemon_card(card, generation)
                    if pokemon:
                        pokemon_list.append(pokemon)
                
                if pokemon_list:
                    break
        
        # Fallback: extract all images and links
        if not pokemon_list:
            print("   Using fallback extraction method...")
            images = soup.find_all('img')
            for img in images:
                alt_text = img.get('alt', '')
                src = img.get('src', '')
                if 'pokemon' in alt_text.lower() or 'pokemon' in src.lower():
                    pokemon = {
                        'name': alt_text,
                        'image_url': src,
                        'generation': generation,
                        'url': self.base_url + str(generation)
                    }
                    pokemon_list.append(pokemon)
        
        return pokemon_list
    
    def parse_pokemon_card(self, card, generation):
        """Parse individual Pokemon card element"""
        try:
            pokemon = {
                'generation': generation,
                'name': '',
                'number': '',
                'image_url': '',
                'type': '',
                'rarity': '',
                'price': '',
                'url': ''
            }
            
            # Extract name
            name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'p'], class_=lambda x: x and ('name' in x.lower() or 'title' in x.lower()))
            if name_elem:
                pokemon['name'] = name_elem.get_text(strip=True)
            
            # Extract image
            img = card.find('img')
            if img:
                pokemon['image_url'] = img.get('src', '') or img.get('data-src', '')
                if not pokemon['name']:
                    pokemon['name'] = img.get('alt', '')
            
            # Extract URL/link
            link = card.find('a')
            if link:
                pokemon['url'] = link.get('href', '')
            
            # Extract price
            price_elem = card.find(['span', 'div', 'p'], class_=lambda x: x and 'price' in x.lower())
            if price_elem:
                pokemon['price'] = price_elem.get_text(strip=True)
            
            # Only return if we have at least a name or image
            if pokemon['name'] or pokemon['image_url']:
                return pokemon
            
        except Exception as e:
            pass
        
        return None
    
    def check_for_api(self):
        """Check if there's an API endpoint we can use"""
        print("🔍 Checking for API endpoints...")
        
        # Common API patterns
        api_urls = [
            "https://www.phygitals.com/api/pokemon",
            "https://api.phygitals.com/pokemon",
            "https://www.phygitals.com/api/v1/pokemon",
        ]
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for api_url in api_urls:
            try:
                response = requests.get(api_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Found API endpoint: {api_url}")
                    return api_url
            except:
                pass
        
        print("❌ No API endpoints found, will use web scraping")
        return None
    
    def save_to_json(self, filename="pokemon_data.json"):
        """Save scraped data to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_pokemon, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved {len(self.all_pokemon)} Pokemon to {filename}")
    
    def save_to_csv(self, filename="pokemon_data.csv"):
        """Save scraped data to CSV"""
        if self.all_pokemon:
            df = pd.DataFrame(self.all_pokemon)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"💾 Saved {len(self.all_pokemon)} Pokemon to {filename}")
    
    def print_summary(self):
        """Print summary of scraped data"""
        print("\n" + "="*50)
        print("📊 SCRAPING SUMMARY")
        print("="*50)
        print(f"Total Pokemon scraped: {len(self.all_pokemon)}")
        
        # Group by generation
        gen_counts = {}
        for pokemon in self.all_pokemon:
            gen = pokemon.get('generation', 'Unknown')
            gen_counts[gen] = gen_counts.get(gen, 0) + 1
        
        for gen in sorted(gen_counts.keys()):
            print(f"Generation {gen}: {gen_counts[gen]} Pokemon")
        
        print("="*50)


def main():
    print("""
    ╔══════════════════════════════════════════╗
    ║   Phygitals Pokemon Scraper v1.0         ║
    ║   Scraping all Pokemon from Gen 1-9      ║
    ╚══════════════════════════════════════════╝
    """)
    
    scraper = PhygitalsPokemonScraper()
    
    # Check for API first
    api_endpoint = scraper.check_for_api()
    
    if api_endpoint:
        # Use API if available
        print("Using API method (not implemented yet)")
    
    # Try requests method first (faster)
    print("\n🎯 Attempting with requests library (fast method)...")
    scraper.scrape_with_requests()
    
    # If no data found, try Selenium
    if not scraper.all_pokemon:
        print("\n⚠️  No data found with requests. Trying Selenium (slow but thorough)...")
        scraper.scrape_with_selenium()
    
    # Save results
    if scraper.all_pokemon:
        scraper.save_to_json()
        scraper.save_to_csv()
        scraper.print_summary()
        
        # Show sample
        print("\n📝 Sample Pokemon (first 5):")
        for pokemon in scraper.all_pokemon[:5]:
            print(f"  - {pokemon.get('name', 'Unknown')} (Gen {pokemon.get('generation')})")
    else:
        print("\n❌ No Pokemon data found. The website structure might have changed.")
        print("💡 Try inspecting the website manually to understand its structure.")


if __name__ == "__main__":
    main()

