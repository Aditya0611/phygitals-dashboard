"""
Fast Marketplace Scraper - Scrape specific generations only
"""
import sys
sys.path.append('.')
from scraper_marketplace import PhygitalsMarketplaceScraper

class FastMarketplaceScraper(PhygitalsMarketplaceScraper):
    def __init__(self, generations_to_scrape=None, max_pokemon=None):
        super().__init__()
        # Only scrape specific generations
        if generations_to_scrape:
            self.generations = generations_to_scrape
        # Limit number of Pokemon
        self.max_pokemon = max_pokemon
    
    def scrape_all_generations(self):
        """Override to add max_pokemon limit"""
        try:
            self.setup_selenium()
            
            print("\n" + "="*70)
            print("PHASE 1: Collecting Pokemon URLs")
            print("="*70)
            
            all_pokemon_urls = []
            
            for gen in self.generations:
                generation_url = f"{self.base_url}{gen}"
                print(f"\nGeneration {gen}: {generation_url}")
                
                pokemon_urls = self.get_pokemon_urls_from_generation(generation_url, gen)
                all_pokemon_urls.extend(pokemon_urls)
                
                print(f"Found {len(pokemon_urls)} Pokemon URLs")
                
                # Stop if we reached max
                if self.max_pokemon and len(all_pokemon_urls) >= self.max_pokemon:
                    all_pokemon_urls = all_pokemon_urls[:self.max_pokemon]
                    print(f"\nReached max limit of {self.max_pokemon} Pokemon")
                    break
            
            print(f"\nTotal Pokemon to scrape: {len(all_pokemon_urls)}")
            
            # Scrape each Pokemon
            print("\n" + "="*70)
            print("PHASE 2: Scraping marketplace listings")
            print("="*70)
            
            for i, pokemon_data in enumerate(all_pokemon_urls, 1):
                print(f"\n[{i}/{len(all_pokemon_urls)}] {pokemon_data['name']}")
                
                listings = self.scrape_pokemon_listings(pokemon_data)
                
                if listings:
                    print(f"   Found {len(listings)} listings")
                    self.all_listings.extend(listings)
                
                # Faster delay
                import time
                time.sleep(1)  # Reduced from 2 seconds
                
                # Save progress
                if i % 20 == 0:
                    self.save_progress(i)
                
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
        
        return self.all_listings


def main():
    print("""
    ==============================================================
       Fast Marketplace Scraper
       Scrape specific generations or limited Pokemon
    ==============================================================
    """)
    
    print("\nOptions:")
    print("1. Scrape Generation 1 only (~150 Pokemon)")
    print("2. Scrape first 50 Pokemon (testing)")
    print("3. Scrape first 200 Pokemon")
    print("4. Scrape Gen 1-3 (~400 Pokemon)")
    print("5. Custom")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        scraper = FastMarketplaceScraper(generations_to_scrape=[1])
    elif choice == "2":
        scraper = FastMarketplaceScraper(max_pokemon=50)
    elif choice == "3":
        scraper = FastMarketplaceScraper(max_pokemon=200)
    elif choice == "4":
        scraper = FastMarketplaceScraper(generations_to_scrape=[1, 2, 3])
    else:
        gen_input = input("Enter generations (e.g., 1,2,3): ").strip()
        gens = [int(g) for g in gen_input.split(',') if g.isdigit()]
        scraper = FastMarketplaceScraper(generations_to_scrape=gens)
    
    print("\nStarting scraping...")
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
    else:
        print("\nNo listings found")


if __name__ == "__main__":
    main()

