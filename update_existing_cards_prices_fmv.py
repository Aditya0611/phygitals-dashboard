#!/usr/bin/env python3
"""
Update existing cards with current prices and FMV from Phygitals
This will re-visit card pages to get the latest data
Supports parallel execution with start/end indices
Usage: python update_existing_cards_prices_fmv.py [start_index] [end_index]
"""
import json
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

# Parse command-line arguments for parallel execution
start_index = 0
end_index = None
instance_id = "1"

if len(sys.argv) >= 2:
    start_index = int(sys.argv[1])
if len(sys.argv) >= 3:
    end_index = int(sys.argv[2])
if len(sys.argv) >= 4:
    instance_id = sys.argv[3]

print("=" * 70)
print(f"  UPDATING EXISTING CARDS WITH CURRENT PRICES & FMV (Instance {instance_id})")
print("=" * 70)

# Load existing data
with open('phygitals_marketplace_complete.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Slice data for this instance
if end_index is None:
    end_index = len(data)
    
data = data[start_index:end_index]
actual_start = start_index

print(f"\nInstance {instance_id}: Processing cards {actual_start} to {actual_start + len(data) - 1}")
print(f"Total cards in this instance: {len(data)}")

# Setup Chrome with separate configuration for parallel instances
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-software-rasterizer')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
chrome_options.add_argument('--remote-debugging-port=' + str(9222 + int(instance_id)))  # Different port for each instance (9223, 9224)
chrome_options.add_argument('--disable-web-security')
chrome_options.add_argument('--allow-running-insecure-content')
chrome_options.add_argument('--window-size=1920,1080')

# Use separate user data directory for each instance to avoid conflicts
try:
    user_data_dir = os.path.abspath(f'chrome_data_{instance_id}')
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir, exist_ok=True)
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
except Exception as e:
    print(f"Warning: Could not create user data directory: {e}")
    # Continue without user-data-dir if it fails

chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)

updated_count = 0
error_count = 0
skipped_count = 0

# Load full data for updates (we'll update the full dataset)
with open('phygitals_marketplace_complete.json', 'r', encoding='utf-8') as f:
    full_data = json.load(f)

# Initialize Chrome driver with retry logic
driver = None
max_retries = 3
for retry in range(max_retries):
    try:
        print(f"Initializing Chrome driver (attempt {retry + 1}/{max_retries})...")
        # On second retry, try without user-data-dir
        if retry == 1:
            print("Retrying with simplified Chrome options (without user-data-dir)...")
            simple_options = Options()
            simple_options.add_argument('--headless=new')
            simple_options.add_argument('--no-sandbox')
            simple_options.add_argument('--disable-dev-shm-usage')
            simple_options.add_argument('--disable-gpu')
            simple_options.add_argument('--remote-debugging-port=' + str(9222 + int(instance_id)))
            simple_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            simple_options.add_experimental_option('useAutomationExtension', False)
            driver = webdriver.Chrome(options=simple_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        print("Chrome driver initialized successfully!")
        break
    except Exception as e:
        if retry < max_retries - 1:
            print(f"Chrome initialization failed, retrying in 2 seconds... Error: {str(e)[:100]}")
            time.sleep(2)
        else:
            raise Exception(f"Failed to initialize Chrome after {max_retries} attempts: {e}")

if driver is None:
    raise Exception("Could not initialize Chrome driver")

try:
    
    for i, card in enumerate(data, 1):
        card_index = actual_start + i - 1
        url = card.get('listing_url', '') or card.get('card_url', '') or card.get('url', '')
        
        if not url:
            skipped_count += 1
            continue
        
        name = card.get('full_listing_name', '')[:50]
        old_price = card.get('current_price', 'N/A')
        old_fmv = card.get('fmv', 'N/A')
        
        print(f"\n[Instance {instance_id}] [{i}/{len(data)}] (Card {card_index}) {name}...")
        print(f"  URL: {url[:60]}...")
        
        try:
            driver.get(url)
            time.sleep(3)
            
            # Wait for page to load
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(2)
            except:
                pass
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            page_text = soup.get_text()
            lower_text = page_text.lower()
            
            page_title = driver.title.lower()
            not_found_patterns = [
                'page not found',
                '404',
                'error loading',
                'doesn\'t exist',
                'not found'
            ]

            if any(pattern in page_title for pattern in not_found_patterns) or any(pattern in lower_text for pattern in not_found_patterns):
                full_data[card_index]['current_price'] = 'Unlisted'
                full_data[card_index]['fmv'] = 'N/A'
                full_data[card_index]['fmv_source'] = ''
                full_data[card_index]['listing_status'] = 'unavailable'
                full_data[card_index]['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
                skipped_count += 1
                print("  ⚠️  Listing appears to be unavailable (404). Marked as unlisted.")
                continue

            # Extract current price
            new_price = None
            
            # Check if unlisted first
            is_unlisted = False
            unlisted_patterns = [
                r'current\s+price[^$]{0,40}(?:unlisted|not\s+for\s+sale|n/?a)',
                r'listingstatus\"\s*:\s*\"unlisted\"',
            ]
            
            for pattern in unlisted_patterns:
                if re.search(pattern, lower_text, re.IGNORECASE):
                    is_unlisted = True
                    break
            
            if is_unlisted:
                new_price = 'Unlisted'
            else:
                # Extract current price
                current_price_match = re.search(r'current\s+price[:\s]*\$?([\d,]+\.?\d*)', page_text, re.IGNORECASE)
                if current_price_match:
                    price_val = current_price_match.group(1).replace(',', '')
                    try:
                        price_float = float(price_val)
                        if 0.01 <= price_float <= 10000:
                            new_price = f'${price_val}'
                        else:
                            new_price = 'Unlisted'
                    except:
                        new_price = 'Unlisted'
                else:
                    # Try alternative patterns
                    price_elements = soup.find_all(string=re.compile(r'\$[\d,]+\.?\d{2}'))
                    for elem in price_elements:
                        parent = elem.parent if elem.parent else None
                        if parent:
                            parent_text = parent.get_text().lower()
                            if 'price' in parent_text and 'fmv' not in parent_text[:200]:
                                price_match = re.search(r'\$([\d,]+\.?\d{2})', elem)
                                if price_match:
                                    price_val = price_match.group(1).replace(',', '')
                                    try:
                                        price_float = float(price_val)
                                        if 0.01 <= price_float <= 10000:
                                            new_price = f'${price_val}'
                                            break
                                    except:
                                        pass
            
            if not new_price:
                new_price = 'Unlisted'
            
            # Extract FMV from JSON (new method)
            new_fmv = None
            json_match = re.search(r'"altFmv"\s*:\s*"([\d,]+\.?\d*)"', page_source)
            if json_match:
                fmv_val = json_match.group(1).replace(',', '').strip()
                try:
                    fmv_float = float(fmv_val)
                    if fmv_float > 0:
                        new_fmv = f'${fmv_float:.2f}'
                except:
                    pass
            
            # If JSON method didn't work, try text extraction
            if not new_fmv:
                # Look for "FMV by" pattern
                fmv_match = re.search(r'fmv\s+by[^$]{0,30}\$([\d,]+\.\d{2})', page_text, re.IGNORECASE)
                if fmv_match:
                    fmv_val = fmv_match.group(1).replace(',', '').strip()
                    try:
                        fmv_float = float(fmv_val)
                        if fmv_float > 0:
                            new_fmv = f'${fmv_float:.2f}'
                    except:
                        pass
            
            # If FMV is still not found, mark it as N/A
            if not new_fmv:
                new_fmv = 'N/A'
            
            # Update card in full_data
            price_changed = new_price != old_price
            # FMV changed if it's different from old value (including setting to N/A)
            fmv_changed = new_fmv != old_fmv
            
            if price_changed or fmv_changed:
                if price_changed:
                    full_data[card_index]['current_price'] = new_price
                    print(f"  Price: {old_price} -> {new_price}")
                
                if fmv_changed:
                    full_data[card_index]['fmv'] = new_fmv
                    # Only set fmv_source to 'alt' if FMV was actually found (not N/A)
                    if new_fmv != 'N/A':
                        full_data[card_index]['fmv_source'] = 'alt'
                    else:
                        # Clear fmv_source when FMV is not available
                        full_data[card_index]['fmv_source'] = ''
                    print(f"  FMV: {old_fmv} -> {new_fmv}")
                
                full_data[card_index]['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
                updated_count += 1
            else:
                print(f"  No changes (Price: {old_price}, FMV: {old_fmv})")
            
            # Save progress every 50 cards (with retry for file locking)
            if i % 50 == 0:
                max_retries = 5
                for retry in range(max_retries):
                    try:
                        # Reload full data to merge with other instance's changes
                        with open('phygitals_marketplace_complete.json', 'r', encoding='utf-8') as f:
                            current_data = json.load(f)
                        # Update our changes into the current data
                        for idx in range(actual_start, min(actual_start + len(data), len(current_data))):
                            if idx < len(full_data):
                                current_data[idx] = full_data[idx]
                        # Save back
                        with open('phygitals_marketplace_complete.json', 'w', encoding='utf-8') as f:
                            json.dump(current_data, f, indent=2, ensure_ascii=False)
                        # Update our local copy
                        full_data = current_data
                        print(f"  Progress saved ({i}/{len(data)})")
                        break
                    except Exception as e:
                        if retry < max_retries - 1:
                            time.sleep(0.5)
                            continue
                        else:
                            print(f"  Warning: Could not save progress: {e}")
                
        except Exception as e:
            error_count += 1
            print(f"  Error: {str(e)[:50]}")
            continue
    
    driver.quit()
    
except Exception as e:
    print(f"\nFatal error: {e}")
    import traceback
    traceback.print_exc()
    if 'driver' in locals():
        driver.quit()

# Save final data (with retry for file locking)
max_retries = 10
for retry in range(max_retries):
    try:
        # Reload full data to merge with other instance's changes
        with open('phygitals_marketplace_complete.json', 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        # Update our changes into the current data
        for idx in range(actual_start, min(actual_start + len(data), len(current_data))):
            if idx < len(full_data):
                current_data[idx] = full_data[idx]
        # Save back
        with open('phygitals_marketplace_complete.json', 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
        break
    except Exception as e:
        if retry < max_retries - 1:
            time.sleep(1)
            continue
        else:
            print(f"  Warning: Could not save final data: {e}")

print("\n" + "=" * 70)
print(f"  UPDATE COMPLETE (Instance {instance_id})")
print("=" * 70)
print(f"Instance {instance_id} processed cards {actual_start} to {actual_start + len(data) - 1}")
print(f"Updated: {updated_count} cards")
print(f"Errors: {error_count} cards")
print(f"Skipped (no URL): {skipped_count} cards")
print("=" * 70)

