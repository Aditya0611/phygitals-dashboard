"""
Phygitals Pokemon Scraper - Final Version
Scrapes all Pokemon with their original URLs and exports to Excel
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
import re

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
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("✅ Chrome WebDriver ready!")
        
    def scrape_all_generations(self):
        """Scrape all Pokemon from all generations"""
        try:
            self.setup_selenium()
            
            for gen in self.generations:
                generation_url = f"{self.base_url}{gen}"
                print(f"\n{'='*60}")
                print(f"📦 SCRAPING GENERATION {gen}")
                print(f"{'='*60}")
                print(f"🔗 URL: {generation_url}")
                
                pokemon_list = self.scrape_generation(generation_url, gen)
                
                if pokemon_list:
                    # Add source URL to each Pokemon
                    for pokemon in pokemon_list:
                        pokemon['source_url'] = generation_url
                    
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
            print(f"⏳ Waiting for page to load...")
            time.sleep(5)  # Wait for JS to render
            
            # Scroll to load all content
            print(f"📜 Scrolling to load all Pokemon...")
            self.scroll_to_bottom()
            
            # Get page source after JS rendering
            page_source = self.driver.page_source
            
            # Save HTML for debugging
            debug_file = f'debug_gen{generation}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"💾 Saved HTML to {debug_file}")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Strategy 1: Find all images that look like Pokemon
            print(f"🔍 Searching for Pokemon images...")
            images = soup.find_all('img')
            print(f"   Found {len(images)} total images")
            
            pokemon_images = []
            for img in images:
                src = img.get('src', '')
                alt = img.get('alt', '')
                
                # Filter out logos, icons, branding
                if any(x in src.lower() for x in ['logo', 'branding', 'icon']):
                    continue
                if any(x in alt.lower() for x in ['logo', 'phygital', 'icon']):
                    continue
                
                # Look for Pokemon-like images
                if src and ('pokemon' in src.lower() or 'raw.githubusercontent' in src.lower() or 'pokeapi' in src.lower()):
                    pokemon_images.append(img)
            
            print(f"   Found {len(pokemon_images)} potential Pokemon images")
            
            # Extract Pokemon data from images
            for img in pokemon_images:
                pokemon = self.extract_pokemon_from_element(img, generation)
                if pokemon:
                    pokemon_list.append(pokemon)
            
            # Strategy 2: Find clickable cards/links
            if not pokemon_list:
                print(f"🔍 Trying to find Pokemon cards/links...")
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '')
                    if '/pokemon/' in href and '/generation/' not in href:
                        pokemon = self.extract_pokemon_from_element(link, generation)
                        if pokemon:
                            pokemon_list.append(pokemon)
            
            # Strategy 3: Use Selenium to find visible elements
            if not pokemon_list:
                print(f"🔍 Using Selenium to find visible Pokemon elements...")
                pokemon_list = self.extract_with_selenium(generation)
            
            # Remove duplicates based on name or image_url
            pokemon_list = self.remove_duplicates(pokemon_list)
            
        except Exception as e:
            print(f"❌ Error scraping generation {generation}: {e}")
            import traceback
            traceback.print_exc()
        
        return pokemon_list
    
    def extract_pokemon_from_element(self, element, generation):
        """Extract Pokemon data from an HTML element"""
        try:
            pokemon = {
                'generation': generation,
                'name': '',
                'pokemon_number': '',
                'image_url': '',
                'pokemon_url': '',
                'type': '',
                'description': ''
            }
            
            # Get image URL
            if element.name == 'img':
                pokemon['image_url'] = element.get('src', '') or element.get('data-src', '')
                pokemon['name'] = element.get('alt', '')
                
                # Try to find parent link
                parent_link = element.find_parent('a')
                if parent_link:
                    pokemon['pokemon_url'] = parent_link.get('href', '')
            
            elif element.name == 'a':
                pokemon['pokemon_url'] = element.get('href', '')
                img = element.find('img')
                if img:
                    pokemon['image_url'] = img.get('src', '') or img.get('data-src', '')
                    pokemon['name'] = img.get('alt', '')
                
                # Try to find name in text
                text = element.get_text(strip=True)
                if text and not pokemon['name']:
                    pokemon['name'] = text.split('\n')[0]
            
            # Clean up Pokemon URL
            if pokemon['pokemon_url']:
                if pokemon['pokemon_url'].startswith('/'):
                    pokemon['pokemon_url'] = 'https://www.phygitals.com' + pokemon['pokemon_url']
            
            # Extract Pokemon number from name (e.g., "#001 Bulbasaur")
            if pokemon['name']:
                number_match = re.search(r'#?(\d+)', pokemon['name'])
                if number_match:
                    pokemon['pokemon_number'] = number_match.group(1)
            
            # Only return if we have meaningful data
            if pokemon['name'] or pokemon['image_url']:
                return pokemon
                
        except Exception as e:
            pass
        
        return None
    
    def extract_with_selenium(self, generation):
        """Use Selenium to extract visible Pokemon elements"""
        pokemon_list = []
        
        try:
            # Find all visible elements
            elements = self.driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'cursor-pointer') or contains(@class, 'hover') or @role='link']")
            
            print(f"   Found {len(elements)} interactive elements")
            
            for elem in elements:
                try:
                    # Skip if not visible
                    if not elem.is_displayed():
                        continue
                    
                    # Get element info
                    text = elem.text.strip()
                    tag_name = elem.tag_name
                    
                    # Skip navigation/branding
                    if any(x in text.lower() for x in ['logo', 'phygital', 'login', 'marketplace', 'packs']):
                        continue
                    
                    # Try to find image within element
                    try:
                        img = elem.find_element(By.TAG_NAME, 'img')
                        img_src = img.get_attribute('src')
                        img_alt = img.get_attribute('alt')
                        
                        # Skip logos/branding
                        if 'logo' in img_src.lower() or 'branding' in img_src.lower():
                            continue
                        
                        pokemon = {
                            'generation': generation,
                            'name': img_alt or text,
                            'pokemon_number': '',
                            'image_url': img_src,
                            'pokemon_url': elem.get_attribute('href') or '',
                            'type': '',
                            'description': text
                        }
                        
                        if pokemon['image_url'] and 'logo' not in pokemon['image_url'].lower():
                            pokemon_list.append(pokemon)
                            
                    except:
                        pass
                        
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"   Error in Selenium extraction: {e}")
        
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
                break
            
            last_height = new_height
            scroll_attempts += 1
        
        # Scroll back to top to ensure all images are loaded
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    
    def remove_duplicates(self, pokemon_list):
        """Remove duplicate Pokemon entries"""
        seen = set()
        unique_pokemon = []
        
        for pokemon in pokemon_list:
            # Create identifier based on name and image
            identifier = (pokemon.get('name', ''), pokemon.get('image_url', ''))
            
            if identifier not in seen and identifier != ('', ''):
                seen.add(identifier)
                unique_pokemon.append(pokemon)
        
        return unique_pokemon
    
    def save_to_excel(self, filename="pokemon_complete_data.xlsx"):
        """Save scraped data to Excel with formatting"""
        if not self.all_pokemon:
            print("❌ No data to save")
            return
        
        df = pd.DataFrame(self.all_pokemon)
        
        # Reorder columns
        columns_order = [
            'generation', 
            'name', 
            'pokemon_number', 
            'type',
            'image_url', 
            'pokemon_url', 
            'source_url',
            'description'
        ]
        
        # Only include columns that exist
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]
        
        # Save to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All Pokemon', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['All Pokemon']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        print(f"\n💾 Saved {len(self.all_pokemon)} Pokemon to {filename}")
    
    def save_to_csv(self, filename="pokemon_complete_data.csv"):
        """Save scraped data to CSV"""
        if not self.all_pokemon:
            print("❌ No data to save")
            return
        
        df = pd.DataFrame(self.all_pokemon)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"💾 Saved {len(self.all_pokemon)} Pokemon to {filename}")
    
    def save_to_json(self, filename="pokemon_complete_data.json"):
        """Save scraped data to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_pokemon, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(self.all_pokemon)} Pokemon to {filename}")
    
    def print_summary(self):
        """Print summary of scraped data"""
        print("\n" + "="*70)
        print("📊 FINAL SCRAPING SUMMARY")
        print("="*70)
        print(f"Total Pokemon scraped: {len(self.all_pokemon)}")
        
        # Group by generation
        gen_counts = {}
        for pokemon in self.all_pokemon:
            gen = pokemon.get('generation', 'Unknown')
            gen_counts[gen] = gen_counts.get(gen, 0) + 1
        
        print("\nPokemon per Generation:")
        for gen in sorted(gen_counts.keys()):
            print(f"  Generation {gen}: {gen_counts[gen]} Pokemon")
        
        print("\n" + "="*70)
        
        # Show sample
        if self.all_pokemon:
            print("\n📝 Sample Pokemon (first 10):")
            print(f"{'#':<5} {'Name':<20} {'Gen':<5} {'URL':<40}")
            print("-" * 70)
            for i, pokemon in enumerate(self.all_pokemon[:10], 1):
                name = pokemon.get('name', 'Unknown')[:18]
                gen = pokemon.get('generation', '?')
                url = pokemon.get('pokemon_url', 'N/A')[:38]
                print(f"{i:<5} {name:<20} {gen:<5} {url:<40}")


def main():
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   Phygitals Pokemon Complete Scraper v3.0           ║
    ║   Exports all Pokemon with URLs to Spreadsheet       ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    scraper = PhygitalsPokemonScraper()
    
    # Scrape all generations
    print("🚀 Starting scraping process...\n")
    scraper.scrape_all_generations()
    
    # Save and display results
    if scraper.all_pokemon:
        print("\n" + "="*70)
        print("💾 SAVING DATA...")
        print("="*70)
        
        scraper.save_to_excel()  # Primary output
        scraper.save_to_csv()    # Alternative format
        scraper.save_to_json()   # Raw data
        
        scraper.print_summary()
        
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETE!")
        print("="*70)
        print("\n📁 Output files created:")
        print("   • pokemon_complete_data.xlsx (Excel - Main file)")
        print("   • pokemon_complete_data.csv (CSV - Alternative)")
        print("   • pokemon_complete_data.json (JSON - Raw data)")
        print("   • debug_gen1.html to debug_gen9.html (Debug files)")
        
    else:
        print("\n❌ No Pokemon data found!")
        print("💡 Check the debug_genX.html files to inspect page structure")


if __name__ == "__main__":
    main()

