#!/usr/bin/env python3
"""
Find which page on Phygitals marketplace has cards with price >= $100
Checks pages systematically to find the starting page
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time

def parse_price(price_str):
    """Parse price string to float"""
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', str(price_str))
    try:
        return float(cleaned)
    except:
        return 0.0

def setup_chrome():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def get_card_prices_from_marketplace_page(driver, page_num):
    """Get prices from cards on a marketplace page - try to extract from page source first"""
    url = f"https://www.phygitals.com/marketplace?page={page_num}&perPage=48"
    
    try:
        driver.get(url)
        time.sleep(4)  # Wait for page to load
        
        # Wait for cards to load
        try:
            WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")) > 0
            )
        except:
            pass
        
        time.sleep(2)
        
        # Try to extract prices from marketplace page source first (faster)
        page_source = driver.page_source
        page_text = driver.find_element(By.TAG_NAME, "body").text if driver.find_elements(By.TAG_NAME, "body") else ""
        
        # Look for prices in page source (might be in JSON or visible text)
        prices_from_page = []
        
        # Method 1: Look for price patterns in page text
        price_patterns = [
            r'\$([\d,]+\.?\d{2})',
            r'price["\']?\s*:\s*["\']?\$?([\d,]+\.?\d{2})',
            r'currentPrice["\']?\s*:\s*["\']?\$?([\d,]+\.?\d{2})',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                price_val = parse_price(match)
                if 0.01 <= price_val <= 100000:  # Reasonable range
                    prices_from_page.append(price_val)
        
        # Method 2: Look in JSON data in page source
        json_price_patterns = [
            r'"price"\s*:\s*"([\d,]+\.?\d{2})"',
            r'"currentPrice"\s*:\s*"([\d,]+\.?\d{2})"',
            r'"current_price"\s*:\s*"([\d,]+\.?\d{2})"',
        ]
        
        for pattern in json_price_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            for match in matches:
                price_val = parse_price(match)
                if 0.01 <= price_val <= 100000:
                    prices_from_page.append(price_val)
        
        # If we found prices in page source, use them
        if prices_from_page:
            # Remove duplicates and sort
            unique_prices = sorted(list(set(prices_from_page)))
            # Take reasonable sample (first 10 unique prices)
            sample_prices = unique_prices[:10]
            
            return {
                'page': page_num,
                'prices': sample_prices,
                'min_price': min(sample_prices),
                'max_price': max(sample_prices),
                'avg_price': sum(sample_prices) / len(sample_prices) if sample_prices else 0,
                'cards_checked': len(sample_prices),
                'has_100_plus': any(p >= 100 for p in sample_prices),
                'all_100_plus': all(p >= 100 for p in sample_prices),
                'method': 'page_source'
            }
        
        # Fallback: Visit individual cards (slower but more accurate)
        card_links = []
        try:
            links = driver.find_elements(By.XPATH, "//a[contains(@href, '/card/')]")
            for link in links:
                href = link.get_attribute('href')
                if href and '/card/' in href:
                    card_links.append(href)
        except:
            pass
        
        if not card_links:
            return None
        
        # Visit first 3 cards only (faster)
        prices = []
        sample_size = min(3, len(card_links))
        
        for i, card_url in enumerate(card_links[:sample_size]):
            try:
                driver.get(card_url)
                time.sleep(1)
                
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                page_text = soup.get_text()
                
                # Extract current price
                price_match = re.search(r'current\s+price[:\s]*\$?([\d,]+\.?\d*)', page_text, re.IGNORECASE)
                if price_match:
                    price_val = parse_price(price_match.group(1))
                    if 0.01 <= price_val <= 100000:
                        prices.append(price_val)
                
                # Go back to marketplace
                driver.back()
                time.sleep(0.5)
            except:
                continue
        
        if prices:
            return {
                'page': page_num,
                'prices': prices,
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'cards_checked': sample_size,
                'has_100_plus': any(p >= 100 for p in prices),
                'all_100_plus': all(p >= 100 for p in prices),
                'method': 'individual_cards'
            }
        return None
        
    except Exception as e:
        print(f"  Error on page {page_num}: {str(e)[:50]}")
        return None

def find_starting_page():
    """Find the starting page for $100+ cards"""
    print("=" * 70)
    print("  FINDING PAGE WITH CARDS PRICED >= $100")
    print("=" * 70)
    print("\nThis will check pages to find where $100+ cards start...")
    print("Note: Checking sample cards from each page for efficiency\n")
    
    driver = setup_chrome()
    
    try:
        # Strategy: Check sample pages first to understand price distribution
        print("Step 1: Checking sample pages to understand price distribution...\n")
        
        # Start from page 200 since you mentioned page 242 has high prices
        test_pages = [200, 220, 240, 242, 250, 260, 280, 300]
        results = []
        
        for page_num in test_pages:
            print(f"Checking page {page_num}...", end=" ", flush=True)
            result = get_card_prices_from_marketplace_page(driver, page_num)
            if result:
                status = "✅ $100+" if result['has_100_plus'] else "❌ <$100"
                method = result.get('method', 'unknown')
                print(f"{status} | Min: ${result['min_price']:.2f}, Max: ${result['max_price']:.2f} ({method})")
                results.append(result)
            else:
                print("Failed to get prices")
            time.sleep(0.5)
        
        # Find approximate range
        print("\n" + "=" * 70)
        print("Step 2: Finding exact starting page...\n")
        
        # Find first page with $100+ cards
        first_100_plus_page = None
        for r in results:
            if r['has_100_plus']:
                first_100_plus_page = r['page']
                break
        
        if not first_100_plus_page:
            print("⚠️  No $100+ cards found in sample pages")
            print("   Checking earlier pages (100-200)...")
            
            # Check earlier pages
            for page_num in [100, 120, 140, 160, 180]:
                print(f"Checking page {page_num}...", end=" ", flush=True)
                result = get_card_prices_from_marketplace_page(driver, page_num)
                if result:
                    status = "✅ $100+" if result['has_100_plus'] else "❌ <$100"
                    print(f"{status} | Min: ${result['min_price']:.2f}, Max: ${result['max_price']:.2f}")
                    results.append(result)
                    if result['has_100_plus']:
                        first_100_plus_page = page_num
                        break
                else:
                    print("Failed")
                time.sleep(0.5)
        
        # Binary search around the found page
        if first_100_plus_page:
            print(f"\nFound $100+ cards around page {first_100_plus_page}")
            print("Narrowing down exact starting page...\n")
            
            # Search backwards to find first page with $100+
            start_search = max(1, first_100_plus_page - 50)
            end_search = first_100_plus_page
            
            exact_start = None
            for page_num in range(start_search, end_search + 1, 10):
                print(f"Checking page {page_num}...", end=" ", flush=True)
                result = get_card_prices_from_marketplace_page(driver, page_num)
                if result:
                    status = "✅ $100+" if result['has_100_plus'] else "❌ <$100"
                    print(f"{status} | Min: ${result['min_price']:.2f}")
                    if result['has_100_plus'] and exact_start is None:
                        exact_start = page_num
                else:
                    print("Failed")
                time.sleep(1)
            
            # Fine-tune: check pages around exact_start (skip if already found page 242)
            if exact_start and exact_start != 242:
                print(f"\nFine-tuning around page {exact_start}...")
                # Check 5 pages before
                for page_num in range(max(1, exact_start - 5), exact_start):
                    print(f"Checking page {page_num}...", end=" ", flush=True)
                    result = get_card_prices_from_marketplace_page(driver, page_num)
                    if result:
                        status = "✅ $100+" if result['has_100_plus'] else "❌ <$100"
                        print(f"{status} | Min: ${result['min_price']:.2f}")
                        if result['has_100_plus']:
                            exact_start = min(exact_start, page_num)
                    else:
                        print("Failed")
                    time.sleep(0.5)
        
        # Final results
        print("\n" + "=" * 70)
        print("  RESULTS")
        print("=" * 70)
        
        if exact_start:
            print(f"\n✅ Starting page for $100+ cards: Page {exact_start}")
            print(f"\nTo scrape only $100+ cards, start from page {exact_start}")
            print(f"\nCommand:")
            print(f"  python scraper_marketplace_url.py --start-page {exact_start} --no-resume")
        elif first_100_plus_page:
            print(f"\n✅ Approximate starting page: Page {first_100_plus_page}")
            print(f"   (Cards with price >= $100 found around this page)")
            print(f"\nCommand:")
            print(f"  python scraper_marketplace_url.py --start-page {first_100_plus_page} --no-resume")
        else:
            print("\n⚠️  Could not determine exact starting page")
            print("   Possible reasons:")
            print("   - Cards are not sorted by price")
            print("   - $100+ cards are mixed throughout pages")
            print("   - Need to check more pages")
        
        # Show sample results
        print("\nSample page results:")
        for r in results[:8]:
            status = "✅ $100+" if r['has_100_plus'] else "❌ <$100"
            print(f"  Page {r['page']}: {status} | ${r['min_price']:.2f} - ${r['max_price']:.2f} (avg: ${r['avg_price']:.2f})")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    find_starting_page()

