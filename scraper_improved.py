"""
Phygitals Pokemon Scraper - Improved Version with Selenium
Properly scrapes JavaScript-rendered Pokemon data
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

class PhygitalsPokemonScraper:
    def __init__(self):
        self.base_url = "https://www.phygitals.com/pokemon/generation/"
        self.generations = range(1, 10)  # Gen 1-9
        self.all_pokemon = []
        self.driver = None
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome"""
        print("🔧 Setting up Chrome WebDriver...")
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Commented out for debugging
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("✅ Chrome WebDriver ready!")
        
    def scrape_all_generations(self):
        """Scrape all Pokemon from all generations"""
        try:
            self.setup_selenium()
            
            for gen in self.generations:
                url = f"{self.base_url}{gen}"
                print(f"\n📦 Scraping Generation {gen}")
                print(f"   URL: {url}")
                
                pokemon_list = self.scrape_generation(url, gen)
                
                if pokemon_list:
                    print(f"✅ Found {len(pokemon_list)} Pokemon in Generation {gen}")
                    self.all_pokemon.extend(pokemon_list)
                else:
                    print(f"⚠️  No Pokemon found in Generation {gen}")
                
                time.sleep(2)  # Be respectful to server
                
        finally:
            if self.driver:
                self.driver.quit()
                print("\n🔒 Browser closed")
        
        return self.all_pokemon
    
    def scrape_generation(self, url, generation):
        """Scrape a single generation page"""
        pokemon_list = []
        
        try:
            # Load the page
            self.driver.get(url)
            print(f"   ⏳ Waiting for page to load...")
            
            # Wait for the page to load (adjust selector based on actual page)
            time.sleep(5)  # Initial wait for JS to load
            
            # Scroll to load all content
            print(f"   📜 Scrolling to load all Pokemon...")
            self.scroll_to_bottom()
            
            # Get page source after JS rendering
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Save HTML for debugging
            with open(f'debug_gen{generation}.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"   💾 Saved HTML to debug_gen{generation}.html for inspection")
            
            # Try multiple strategies to find Pokemon
            pokemon_list = self.extract_pokemon_multiple_strategies(soup, generation)
            
            # If still no data, try finding any structured data
            if not pokemon_list:
                print(f"   🔍 Trying to extract from visible elements...")
                pokemon_list = self.extract_from_visible_elements(generation)
            
        except Exception as e:
            print(f"   ❌ Error scraping generation {generation}: {e}")
        
        return pokemon_list
    
    def scroll_to_bottom(self):
        """Scroll to bottom of page to load all dynamic content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 10
        
        while scroll_attempts < max_attempts:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                # Try scrolling up and down again
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Check again
                newer_height = self.driver.execute_script("return document.body.scrollHeight")
                if newer_height == new_height:
                    break
            
            last_height = new_height
            scroll_attempts += 1
        
        print(f"   ✅ Scrolling complete (attempts: {scroll_attempts})")
    
    def extract_pokemon_multiple_strategies(self, soup, generation):
        """Try multiple strategies to extract Pokemon data"""
        pokemon_list = []
        
        # Strategy 1: Look for common Pokemon card patterns
        strategies = [
            # Look for grid items
            {'selector': 'div[class*="grid"] > div', 'name': 'Grid items'},
            {'selector': 'div[class*="Grid"] > div', 'name': 'Grid items (capital)'},
            
            # Look for card patterns
            {'selector': 'div[class*="card"]:not([class*="navbar"])', 'name': 'Card divs'},
            {'selector': 'a[href*="/pokemon/"]', 'name': 'Pokemon links'},
            
            # Look for list items
            {'selector': 'li[class*="item"]', 'name': 'List items'},
            
            # Look for specific component patterns (React/Next.js)
            {'selector': '[data-pokemon]', 'name': 'Data attributes'},
            {'selector': 'article', 'name': 'Article elements'},
        ]
        
        for strategy in strategies:
            elements = soup.select(strategy['selector'])
            if elements:
                print(f"   🎯 Trying strategy: {strategy['name']} (found {len(elements)} elements)")
                
                for elem in elements:
                    pokemon = self.parse_pokemon_element(elem, generation)
                    if pokemon and self.is_valid_pokemon(pokemon):
                        pokemon_list.append(pokemon)
                
                if pokemon_list:
                    print(f"   ✅ Strategy '{strategy['name']}' worked! Found {len(pokemon_list)} Pokemon")
                    break
        
        return pokemon_list
    
    def extract_from_visible_elements(self, generation):
        """Extract Pokemon by finding all visible elements"""
        pokemon_list = []
        
        try:
            # Find all clickable elements that might be Pokemon
            elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'cursor-pointer') or contains(@class, 'hover')]")
            
            print(f"   Found {len(elements)} potentially clickable elements")
            
            for elem in elements[:50]:  # Limit to first 50 to avoid too many
                try:
                    # Get text and attributes
                    text = elem.text
                    html = elem.get_attribute('outerHTML')
                    
                    if text and len(text) > 0 and 'Logo' not in text and 'Phygitals' not in text:
                        # Try to find image
                        img_elements = elem.find_elements(By.TAG_NAME, 'img')
                        img_url = ''
                        if img_elements:
                            img_url = img_elements[0].get_attribute('src')
                        
                        # Create Pokemon entry
                        pokemon = {
                            'generation': generation,
                            'name': text.strip().split('\n')[0],  # First line of text
                            'image_url': img_url,
                            'full_text': text.strip()
                        }
                        
                        if self.is_valid_pokemon(pokemon):
                            pokemon_list.append(pokemon)
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"   ❌ Error extracting visible elements: {e}")
        
        return pokemon_list
    
    def parse_pokemon_element(self, element, generation):
        """Parse a single Pokemon element"""
        try:
            pokemon = {
                'generation': generation,
                'name': '',
                'number': '',
                'image_url': '',
                'type': '',
                'url': ''
            }
            
            # Extract name
            name_patterns = [
                element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']),
                element.find(class_=lambda x: x and 'name' in x.lower()),
                element.find('span'),
                element.find('p')
            ]
            
            for pattern in name_patterns:
                if pattern:
                    text = pattern.get_text(strip=True)
                    if text and len(text) > 0:
                        pokemon['name'] = text
                        break
            
            # Extract image
            img = element.find('img')
            if img:
                pokemon['image_url'] = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy', '')
                if not pokemon['name']:
                    pokemon['name'] = img.get('alt', '')
            
            # Extract URL
            link = element.find('a')
            if link:
                pokemon['url'] = link.get('href', '')
            elif element.name == 'a':
                pokemon['url'] = element.get('href', '')
            
            return pokemon if pokemon['name'] or pokemon['image_url'] else None
            
        except Exception as e:
            return None
    
    def is_valid_pokemon(self, pokemon):
        """Check if extracted data is actually a Pokemon (not logo/nav)"""
        if not pokemon:
            return False
        
        name = pokemon.get('name', '').lower()
        img = pokemon.get('image_url', '').lower()
        
        # Filter out navigation/branding elements
        invalid_keywords = ['logo', 'phygital', 'branding', 'navbar', 'menu', 'icon']
        
        for keyword in invalid_keywords:
            if keyword in name or keyword in img:
                return False
        
        # Must have either a name or image
        if not pokemon.get('name') and not pokemon.get('image_url'):
            return False
        
        return True
    
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
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"Total Pokemon scraped: {len(self.all_pokemon)}")
        
        # Group by generation
        gen_counts = {}
        for pokemon in self.all_pokemon:
            gen = pokemon.get('generation', 'Unknown')
            gen_counts[gen] = gen_counts.get(gen, 0) + 1
        
        for gen in sorted(gen_counts.keys()):
            print(f"Generation {gen}: {gen_counts[gen]} Pokemon")
        
        print("="*60)
        
        # Show sample
        if self.all_pokemon:
            print("\n📝 Sample Pokemon (first 10):")
            for i, pokemon in enumerate(self.all_pokemon[:10], 1):
                name = pokemon.get('name', 'Unknown')
                gen = pokemon.get('generation', '?')
                print(f"  {i}. {name} (Gen {gen})")


def main():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   Phygitals Pokemon Scraper v2.0 (Improved)      ║
    ║   Using Selenium for JavaScript-rendered pages   ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    scraper = PhygitalsPokemonScraper()
    
    # Scrape all generations
    scraper.scrape_all_generations()
    
    # Save and display results
    if scraper.all_pokemon:
        scraper.save_to_json()
        scraper.save_to_csv()
        scraper.print_summary()
    else:
        print("\n❌ No Pokemon data found!")
        print("💡 Check the debug_genX.html files to see the actual page structure")
        print("💡 You may need to manually inspect the website and update selectors")


if __name__ == "__main__":
    main()

