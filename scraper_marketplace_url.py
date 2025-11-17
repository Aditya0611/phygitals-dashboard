"""
Phygitals Marketplace Scraper - URL PAGINATION
Uses direct URL navigation instead of button clicking
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import argparse
import json
import time
import pandas as pd
import re

class URLMarketplaceScraper:
    def __init__(self, start_page=1, max_pages=None):
        self.marketplace_base_url = "https://www.phygitals.com/marketplace"
        self.all_listings = []
        self.driver = None
        self.start_page = start_page
        self.max_pages = max_pages
    
    def is_valid_fmv(self, val, current_price_val=None):
        """Validate if a value is a reasonable FMV (not a year or placeholder)"""
        try:
            val = float(val)
            # Reject values that look like years (2000-2099 range)
            if 2000 <= val <= 2099:
                return False  # It's a year, not FMV
            # Must be within reasonable price range
            if not (0.01 <= val <= 10000):
                return False
            # Exclude common placeholder values
            if val == 100.00:
                return False
            # Should be different from current price (if known)
            if current_price_val is not None:
                if abs(val - current_price_val) <= 0.01:
                    return False  # Too close to current price
            return True
        except:
            return False
        
    def setup_selenium(self):
        """Setup Chrome"""
        print("Setting up Chrome...")
        
        # Kill any existing Chrome processes first
        try:
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)  # Wait for processes to terminate
        except:
            pass
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--enable-unsafe-swiftshader')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-features=NetworkService,NetworkServiceInProcess')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('prefs', {
            'profile.managed_default_content_settings.images': 2,
            'profile.managed_default_content_settings.plugins': 2,
            'profile.managed_default_content_settings.stylesheets': 2,
            'profile.managed_default_content_settings.fonts': 2,
            'profile.managed_default_content_settings.media_stream': 2
        })
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Try to create driver with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chrome_options.set_capability('pageLoadStrategy', 'none')
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.set_page_load_timeout(45)
                self.driver.implicitly_wait(0)
                
                # Test connection to marketplace homepage
                print("Testing connection...")
                try:
                    self.driver.set_page_load_timeout(20)
                    self.driver.get("https://www.phygitals.com/marketplace")
                    try:
                        WebDriverWait(self.driver, 5).until(
                            lambda d: d.execute_script("return document.body && document.body.children.length > 0")
                        )
                    except:
                        pass
                    title = self.driver.title
                    print(f"✓ Connection successful! Page title: {title[:50]}...")
                except Exception as conn_err:
                    print(f"  ⚠️  Connection test warning: {str(conn_err)[:100]}")
                    # Continue anyway - might be a timeout but page could still work
                
                print("Chrome ready!\n")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️  Chrome init failed (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(2)
                    # Try killing Chrome processes again
                    try:
                        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(2)
                    except:
                        pass
                else:
                    raise Exception(f"Failed to initialize Chrome after {max_retries} attempts: {e}")
    
    def scrape_all_pages(self):
        """Scrape all marketplace pages using direct URL navigation"""
        try:
            self.setup_selenium()
            
            # Determine pages to scrape
            if self.max_pages:
                # max_pages is the number of pages to scrape from start_page
                end_page = self.start_page + self.max_pages - 1
                pages_to_scrape = self.max_pages
            else:
                pages_to_scrape = 1516  # Total pages from screenshot
                end_page = pages_to_scrape
            
            print(f"{'='*70}")
            print(f"SCRAPING {pages_to_scrape} PAGES (from page {self.start_page} to {end_page})")
            print(f"{'='*70}\n")
            
            # Track the last successfully processed page
            last_completed_page = None
            cards_before_page = len(self.all_listings)
            
            for idx, page_num in enumerate(range(self.start_page, end_page + 1), 1):
                print(f"\n{'='*70}")
                print(f"PAGE {page_num} ({idx}/{pages_to_scrape})")
                print(f"{'='*70}")
                
                # Try different URL patterns
                per_page_options = [48, 36]
                card_urls = None
                page_success = False
                
                for per_page in per_page_options:
                    urls_to_try = [
                        f"{self.marketplace_base_url}?page={page_num}&perPage={per_page}",
                        f"{self.marketplace_base_url}?p={page_num}&perPage={per_page}",
                        f"{self.marketplace_base_url}/page/{page_num}?perPage={per_page}",
                    ]
                    
                    for url in urls_to_try:
                        try:
                            print(f"Trying: {url}")
                            # Use longer timeout and handle timeouts gracefully
                            try:
                                self.driver.set_page_load_timeout(45)  # 45 seconds max
                                self.driver.get(url)
                            except Exception as timeout_err:
                                # If timeout occurs, try to continue anyway
                                if 'timeout' in str(timeout_err).lower() or 'timed out' in str(timeout_err).lower():
                                    print(f"    ⚠️  Page load timeout, but continuing...")
                                    # Try to stop loading and continue
                                    try:
                                        self.driver.execute_script("window.stop();")
                                    except:
                                        pass
                                else:
                                    raise  # Re-raise if it's a different error
                            
                            # Targeted waits only
                            try:
                                WebDriverWait(self.driver, 10).until(
                                    lambda d: d.execute_script("return document.readyState") in ["interactive", "complete"]
                                )
                            except:
                                pass
                            
                            # Wait longer for card links to load (dynamic content)
                            print("    ⏳ Waiting for cards to load...")
                            time.sleep(5)  # Initial wait for dynamic content
                            
                            # Scroll to trigger lazy loading
                            try:
                                self.driver.execute_script("window.scrollTo(0, 500);")
                                time.sleep(2)
                                self.driver.execute_script("window.scrollTo(0, 1000);")
                                time.sleep(2)
                                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                time.sleep(3)
                            except:
                                pass
                            
                            # Wait for card links specifically (grid ready)
                            try:
                                WebDriverWait(self.driver, 20).until(
                                    lambda d: len(d.find_elements(By.XPATH, "//a[contains(@href, '/card/')]") ) > 0
                                )
                                print("    ✓ Cards detected!")
                            except:
                                print("    ⚠️  Cards not found in initial wait, will try in get_cards_from_current_page()")
                                pass
                            
                            # Debug: Check what we actually loaded
                            try:
                                current_url = self.driver.current_url
                                page_title = self.driver.title
                                page_source_len = len(self.driver.page_source)
                                print(f"    📊 Page loaded: URL={current_url[:60]}..., Title={page_title[:40]}..., HTML size={page_source_len:,} chars")
                            except:
                                pass
                            
                            # Check if page loaded correctly
                            card_urls = self.get_cards_from_current_page()
                            
                            if card_urls and len(card_urls) > 0:
                                print(f"✓ Found {len(card_urls)} cards with this URL pattern!")
                                page_success = True
                                break
                            else:
                                print(f"✗ No cards found with this URL")
                                # Debug: Try to see what links exist
                                try:
                                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                                    card_links = [l for l in all_links if '/card/' in (l.get_attribute('href') or '')]
                                    print(f"    🔍 Debug: Found {len(all_links)} total links, {len(card_links)} with '/card/' in href")
                                except:
                                    pass
                        except Exception as e:
                            error_msg = str(e)
                            if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                                print(f"    ⚠️  Page timeout - trying to continue anyway...")
                                # Reset timeout for next page
                                self.driver.set_page_load_timeout(45)
                                # Try to clear any stuck state
                                try:
                                    self.driver.execute_script("window.stop();")
                                    time.sleep(2)
                                    # Try to get cards anyway, even after timeout
                                    try:
                                        card_urls = self.get_cards_from_current_page()
                                        if card_urls and len(card_urls) > 0:
                                            print(f"✓ Found {len(card_urls)} cards (after timeout recovery)!")
                                            page_success = True
                                            break
                                    except:
                                        pass
                                except:
                                    pass
                            else:
                                print(f"    ❌ Error loading page: {error_msg[:100]}")
                                # If it's a connection pool error, wait a bit longer before retrying
                                if 'connectionpool' in error_msg.lower() or 'localhost' in error_msg.lower():
                                    print(f"    ⏳ Connection issue detected, waiting 3 seconds before retry...")
                                    time.sleep(3)
                            continue
                    
                    if page_success:
                        if per_page != per_page_options[0]:
                            print(f"    ℹ️  Falling back to {per_page} cards per page (initial setting returned no results)")
                        break
                
                if not page_success:
                    print("⚠️  Failed to load this page after all attempts. Skipping...")
                    # Save progress before skipping
                    self.save_progress(page_num)
                    continue
                
                # Track cards collected from this page (reset for each page)
                cards_before_page = len(self.all_listings)
                
                # Scrape each card
                for i, card_url in enumerate(card_urls, 1):
                    print(f"  [{i}/{len(card_urls)}] {card_url[:70]}...")
                    
                    card_data = self.scrape_card_page(card_url)
                    if card_data:
                        self.all_listings.append(card_data)
                        fmv_status = card_data.get('fmv', 'N/A')
                        fmv_source = card_data.get('fmv_source', '')
                        if fmv_status != 'N/A' and fmv_source == 'alt':
                            print(f"    ✓ {card_data.get('grader', 'N/A')} {card_data.get('grade', '')} - {card_data.get('current_price', 'N/A')} | FMV: {fmv_status} (ALT)")
                        else:
                            print(f"    ✓ {card_data.get('grader', 'N/A')} {card_data.get('grade', '')} - {card_data.get('current_price', 'N/A')} | FMV: {fmv_status}")
                    
                    time.sleep(0.3)
                
                # Track if we collected any cards from this page
                cards_collected_this_page = len(self.all_listings) - cards_before_page
                
                print(f"\nTotal cards collected: {len(self.all_listings):,}")
                
                # Save progress after EVERY page for real-time dashboard updates
                # Only save as current page if we collected cards from it
                if cards_collected_this_page > 0:
                    self.save_progress(page_num)
                    last_completed_page = page_num
                    print(f"    💡 Progress saved - dashboard will update automatically")
                else:
                    print(f"    ⚠️  No cards collected from this page, skipping save")
                
                # Add delay between pages to avoid connection issues
                if page_num < end_page:  # Don't delay after the last page
                    time.sleep(2)  # 2 second delay between pages
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Stopped by user!")
            if hasattr(self, 'all_listings') and self.all_listings:
                # Check if we collected any cards from the current page
                cards_collected_this_page = len(self.all_listings) - cards_before_page
                
                # If we collected cards from current page, save as current page
                # Otherwise, use the last completed page (or previous page)
                if cards_collected_this_page > 0:
                    last_page = page_num
                    print(f"\n✅ Progress saved! Collected {cards_collected_this_page} cards from page {page_num}")
                elif last_completed_page is not None:
                    last_page = last_completed_page
                    print(f"\n✅ Progress saved! Last completed page was {last_completed_page}")
                else:
                    # No pages completed yet, save as start_page - 1 (so resume from start_page)
                    last_page = self.start_page - 1 if self.start_page > 1 else 0
                    print(f"\n✅ Progress saved! No pages completed, saving as page {last_page}")
                
                self.save_progress(last_page)
                print(f"✅ Resume from page {last_page + 1}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'all_listings') and self.all_listings:
                # Check if we collected any cards from the current page
                cards_collected_this_page = len(self.all_listings) - cards_before_page
                
                # If we collected cards from current page, save as current page
                # Otherwise, use the last completed page (or previous page)
                if cards_collected_this_page > 0:
                    last_page = page_num
                elif last_completed_page is not None:
                    last_page = last_completed_page
                else:
                    # No pages completed yet, save as start_page - 1 (so resume from start_page)
                    last_page = self.start_page - 1 if self.start_page > 1 else 0
                
                self.save_progress(last_page)
                print(f"\n✅ Progress saved! Resume from page {last_page + 1}")
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
    
    def get_cards_from_current_page(self):
        """Get all card URLs from the current page"""
        card_urls = set()
        
        # Wait for dynamic content to load
        print("    ⏳ Waiting for page content to settle...")
        time.sleep(3)  # Increased wait for dynamic content
        
        # Check if page loaded and body exists before scrolling
        try:
            # Wait for document body to exist
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return document.body !== null")
                )
            except:
                pass  # Continue anyway
            
            # Minimal readiness wait
            try:
                WebDriverWait(self.driver, 6).until(
                    lambda d: d.execute_script("return document.readyState") in ["interactive", "complete"]
                )
            except:
                pass
            
            # Light nudge only if needed
            try:
                self.driver.execute_script("window.scrollTo(0, 400);")
            except:
                pass
            
            # Safe scroll - check if body exists first
            try:
                scroll_height = self.driver.execute_script("""
                    return document.body ? document.body.scrollHeight : 0;
                """)
                
                if scroll_height > 100:  # Only scroll if there's content
                    # Minimal scroll step
                    try:
                        self.driver.execute_script("window.scrollTo(0, Math.min(800, arguments[0]));", scroll_height)
                    except Exception as scroll_err:
                        # Connection pool errors - wait and continue
                        if 'connectionpool' in str(scroll_err).lower() or 'localhost' in str(scroll_err).lower():
                            print(f"    ⚠️  Connection issue during scroll, waiting...")
                            time.sleep(3)
                        else:
                            raise
                else:
                    print("    ⚠️  Page body not ready or no content, waiting...")
                    time.sleep(3)  # Wait longer if page seems empty
            except Exception as scroll_err:
                # If connection error, wait longer
                if 'connectionpool' in str(scroll_err).lower() or 'localhost' in str(scroll_err).lower():
                    print(f"    ⚠️  Connection pool error, waiting 5 seconds...")
                    time.sleep(5)
                else:
                    raise
        except Exception as e:
            error_msg = str(e)
            print(f"    ⚠️  Scroll error (continuing anyway): {error_msg[:80]}")
            # If it's a connection error, wait longer
            if 'connectionpool' in error_msg.lower() or 'localhost' in error_msg.lower():
                time.sleep(5)
            else:
                time.sleep(3)  # Wait even if scroll fails
        
        # Find card links - try multiple selectors
        try:
            # Method 1: Standard href links - try multiple patterns
            link_patterns = [
                "//a[contains(@href, '/card/')]",
                "//a[contains(@href, 'phygitals.com/card/')]",
                "//a[starts-with(@href, '/card/')]",
                "//a[contains(@href, 'card')]",  # More flexible
            ]
            
            for pattern in link_patterns:
                try:
                    try:
                        links = self.driver.find_elements(By.XPATH, pattern)
                    except Exception as find_err:
                        # Connection pool errors - wait and retry once
                        if 'connectionpool' in str(find_err).lower() or 'localhost' in str(find_err).lower():
                            print(f"    ⚠️  Connection issue finding links, waiting 3 seconds...")
                            time.sleep(3)
                            links = self.driver.find_elements(By.XPATH, pattern)  # Retry once
                        else:
                            raise
                    
                    for link in links:
                        try:
                            href = link.get_attribute('href')
                            if href and ('/card/' in href or 'phygitals.com/card' in href):
                                # Normalize URL
                                if 'phygitals.com' not in href:
                                    if href.startswith('/'):
                                        href = f"https://www.phygitals.com{href}"
                                    else:
                                        href = f"https://www.phygitals.com/{href}"
                                # Validate it's actually a card URL
                                if '/card/' in href and len(href) > 30:  # Card URLs are usually longer
                                    card_urls.add(href)
                        except:
                            pass
                    if len(card_urls) > 0:
                        break  # Found cards with this pattern
                except:
                    continue
            
            # Method 2: If no links found, try looking in page HTML directly
            if len(card_urls) == 0:
                print("    🔍 Trying to parse card URLs from page source...")
                try:
                    page_html = self.driver.page_source
                    # Find all URLs in HTML - multiple patterns
                    patterns = [
                        r'https?://[^\s<>"\']*phygitals\.com[^\s<>"\']*card[^\s<>"\']*',
                        r'href=["\']([^"\']*card/[^"\']*)["\']',
                        r'"/card/([^"\']+)"',
                        r"'/card/([^']+)'",
                        r'phygitals\.com/card/([a-zA-Z0-9\-_]+)',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, page_html, re.IGNORECASE)
                        for match in matches:
                            if isinstance(match, tuple):
                                match = match[0] if match else ''
                            
                            # Build full URL
                            if match.startswith('http'):
                                url = match
                            elif match.startswith('/card/'):
                                url = f"https://www.phygitals.com{match}"
                            elif '/card/' in match:
                                url = f"https://www.phygitals.com/{match}" if not match.startswith('http') else match
                            else:
                                url = f"https://www.phygitals.com/card/{match}"
                            
                            # Clean URL
                            url = url.split('"')[0].split("'")[0].split('>')[0].split('<')[0].split('?')[0].split('#')[0].strip()
                            
                            if '/card/' in url and len(url) > 40 and 'phygitals.com' in url:
                                card_urls.add(url)
                                
                    if len(card_urls) > 0:
                        print(f"    ✓ Found {len(card_urls)} card URLs in page source!")
                except Exception as e:
                    print(f"    ⚠️  Error parsing page source: {str(e)[:50]}")
                    pass
            
            # Method 3: Try looking for any element with /card/ in any attribute
            if len(card_urls) == 0:
                # Try looking for any element with /card/ in any attribute
                all_elements = self.driver.find_elements(By.XPATH, "//*[@*[contains(., '/card/') or contains(., 'card/')]]")
                for elem in all_elements:
                    try:
                        # Check all attributes
                        for attr in ['href', 'data-href', 'data-url', 'url', 'data-link', 'onclick']:
                            val = elem.get_attribute(attr)
                            if val and ('/card/' in val or 'card/' in val):
                                # Extract URL from attribute
                                url_match = re.search(r'(https?://[^\s<>"\']*card[^\s<>"\']*)', str(val))
                                if url_match:
                                    val = url_match.group(1)
                                if 'phygitals.com' not in val:
                                    if val.startswith('/'):
                                        val = f"https://www.phygitals.com{val}"
                                    elif not val.startswith('http'):
                                        val = f"https://www.phygitals.com/{val}"
                                if '/card/' in val and len(val) > 40:
                                    card_urls.add(val)
                    except:
                        pass
        except Exception as e:
            print(f"    ⚠️  Error finding links: {str(e)[:50]}")
        
        return list(card_urls)
    
    def scrape_card_page(self, card_url):
        """Scrape individual card listing page"""
        try:
            # Set shorter timeout for card pages
            self.driver.set_page_load_timeout(15)  # 15 seconds for individual cards
            self.driver.get(card_url)
            time.sleep(1.5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            card = {
                'listing_url': card_url,
                'full_listing_name': '',
                'pokemon_name': '',
                'grader': '',
                'grade': '',
                'current_price': '',
                'fmv': '',
                'fmv_source': '',
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
                    title_parts = card['full_listing_name'].split()
                    if len(title_parts) > 2:
                        card['pokemon_name'] = ' '.join(title_parts[2:8])
            except:
                pass
            
            # Get all text
            page_text = soup.get_text()
            
            # Extract data
            grader_match = re.search(r'\b(PSA|CGC|BGS|Beckett)\b', page_text, re.IGNORECASE)
            if grader_match:
                card['grader'] = grader_match.group(1).upper()
            
            grade_match = re.search(r'(?:PSA|CGC|BGS)\s*(\d+(?:\.\d+)?)', page_text, re.IGNORECASE)
            if grade_match:
                card['grade'] = grade_match.group(1)
            
            # Extract prices using context-aware approach
            lower_text = page_text.lower()
            
            # FIRST: Check if card is explicitly "Unlisted" or "Not For Sale"
            # This check must happen BEFORE extracting any prices to avoid grabbing FMV
            is_unlisted = False
            unlisted_patterns = [
                r'current\s+price[^$]{0,40}(?:unlisted|not\s+for\s+sale|n/?a)',
                r'listingstatus\"\s*:\s*\"unlisted\"',
            ]
            
            for pattern in unlisted_patterns:
                if re.search(pattern, lower_text, re.IGNORECASE):
                    is_unlisted = True
                    break
            
            # Also check page source for "Unlisted" text near price elements
            try:
                page_html = self.driver.page_source.lower()
                if 'unlisted' in page_html or 'not for sale' in page_html:
                    # Check if it's near price context
                    if re.search(r'(?:current\s+price|price)[^$]{0,100}(?:unlisted|not\s+for\s+sale)', page_html, re.IGNORECASE):
                        is_unlisted = True
            except:
                pass
            
            # If unlisted, set price immediately and skip price extraction
            if is_unlisted:
                card['current_price'] = 'Unlisted'
                print(f"    ⚠️  Card marked as unlisted/not for sale")
            else:
                # Only extract current_price if NOT unlisted
                # Look for "Current price" or similar labels - MUST be explicitly labeled
                current_price_match = None
                
                # Pattern 1: "Current price: $12.34" - MUST have "Current price" label
                current_price_match = re.search(r'current\s+price[:\s]*\$?([\d,]+\.?\d*)', page_text, re.IGNORECASE)
                
                # Pattern 2: "Price: $12.34" - MUST have "Price" label immediately before
                if not current_price_match:
                    current_price_match = re.search(r'(?:^|\n|>)\s*price[:\s]*\$?([\d,]+\.?\d*)', page_text, re.IGNORECASE)
                
                # Pattern 3: Look for price button or listing price element
                if not current_price_match:
                    try:
                        # Try to find price in button text or specific elements
                        price_elements = soup.find_all(string=re.compile(r'\$[\d,]+\.?\d{2}'))
                        for elem in price_elements:
                            parent = elem.parent if elem.parent else None
                            if parent:
                                parent_text = parent.get_text().lower()
                                # Only if parent contains "price" or "buy" or "purchase"
                                if any(keyword in parent_text for keyword in ['price', 'buy', 'purchase', 'cost', 'listing']):
                                    price_match = re.search(r'\$([\d,]+\.?\d{2})', elem)
                                    if price_match:
                                        # Make sure it's NOT FMV
                                        if 'fmv' not in parent_text[:200] and 'fair market' not in parent_text[:200]:
                                            current_price_match = price_match
                                            break
                    except:
                        pass
                
                if current_price_match:
                    price_val = current_price_match.group(1).replace(',', '')
                    # Validate it's a reasonable price (not FMV)
                    try:
                        price_float = float(price_val)
                        if 0.01 <= price_float <= 10000:
                            card['current_price'] = '$' + price_val
                        else:
                            card['current_price'] = 'Unlisted'
                    except:
                        card['current_price'] = 'Unlisted'
                else:
                    # Try Selenium-based extraction for dynamically rendered prices
                    try:
                        # Wait a bit for dynamic content
                        time.sleep(1.5)
                        # Get fresh page source after JavaScript rendering
                        fresh_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        fresh_text = fresh_soup.get_text()
                        fresh_lower = fresh_text.lower()
                        
                        # Check again for unlisted in fresh text
                        if not is_unlisted:
                            for pattern in unlisted_patterns:
                                if re.search(pattern, fresh_lower, re.IGNORECASE):
                                    is_unlisted = True
                                    card['current_price'] = 'Unlisted'
                                    break
                        
                        # Only try to extract price if not unlisted
                        if not is_unlisted:
                            # Try pattern 1: Look for "Current price:" label explicitly
                            fresh_price_match = re.search(r'current\s+price[:\s]*\$?([\d,]+\.?\d{2})', fresh_text, re.IGNORECASE)
                            if fresh_price_match:
                                price_val = fresh_price_match.group(1).replace(',', '')
                                try:
                                    val = float(price_val)
                                    if 0.01 <= val <= 10000:
                                        card['current_price'] = '$' + price_val
                                        current_price_match = True
                                except:
                                    pass
                    except Exception as e:
                        # Silently continue if Selenium extraction fails
                        pass
                    
                    if not card.get('current_price'):
                        # No explicit current price found -> treat as unlisted
                        card['current_price'] = 'Unlisted'
                        print(f"    ⚠️  No explicit current price found, marking as unlisted")
            
            # If still unlisted after all checks, skip the card
            if card.get('current_price') == 'Unlisted':
                print(f"    ⚠️  Skipping: Card marked as unlisted/not for sale")
                return None
            
            # Extract FMV by ALT - multiple methods for reliability
            fmv_found = False
            
            # Wait longer for dynamic content to load (FMV might be loaded via JavaScript)
            time.sleep(3)  # Increased wait time for dynamic content
            
            # Try scrolling to trigger lazy-loaded content
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except:
                pass
            
            # Get fresh page source after JavaScript has rendered
            try:
                # Wait for page to be interactive
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(2)  # Additional wait for dynamic FMV content
            except:
                time.sleep(2)  # Fallback wait
            
            # Get fresh page source for JSON extraction
            fresh_page_source = self.driver.page_source
            
            # Method 0: Extract FMV from JSON data in page source (NEW - Phygitals changed format)
            if not fmv_found:
                try:
                    # Look for JSON data with altFmv field
                    json_match = re.search(r'"altFmv"\s*:\s*"([\d,]+\.?\d*)"', fresh_page_source)
                    if json_match:
                        fmv_val = json_match.group(1).replace(',', '').strip()
                        try:
                            val = float(fmv_val)
                            current_price_val = None
                            if card.get('current_price'):
                                try:
                                    current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                except:
                                    pass
                            if self.is_valid_fmv(val, current_price_val):
                                card['fmv'] = f'${val:.2f}'
                                card['fmv_source'] = 'alt'
                                fmv_found = True
                        except:
                            pass
                except:
                    pass
            
            # Method 1: Look for "FMV" elements and find nearby prices (ALT might be in different element)
            try:
                # First try to find elements with "FMV by" (NEW format - Phygitals removed "ALT" text)
                fmv_selectors = [
                    "//*[contains(., 'FMV by') or contains(., 'fmv by')]",  # NEW: "FMV by" without ALT
                    "//*[contains(., 'FMV by .ALT') or contains(., 'FMV by .Alt') or contains(., 'fmv by .alt')]",  # Old format
                    "//*[contains(., 'FMV by ALT') or contains(., 'FMV by Alt') or contains(., 'fmv by alt')]",  # Old format
                    "//*[contains(text(), 'FMV') and (contains(text(), '.ALT') or contains(text(), '.Alt'))]",  # Look for .ALT specifically
                    "//*[contains(text(), 'FMV') and (contains(text(), 'ALT') or contains(text(), 'Alt'))]",
                    "//*[contains(text(), 'FMV')]",  # Just "FMV" - ALT might be elsewhere
                ]
                
                for selector in fmv_selectors:
                    try:
                        fmv_elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in fmv_elements[:5]:  # Increased to 5 matches
                            try:
                                # Get parent element (likely contains the price)
                                parent = elem.find_element(By.XPATH, "./..")
                                parent_text = parent.text
                                
                                # Get all sibling elements (price might be in a sibling div/span)
                                try:
                                    following = elem.find_elements(By.XPATH, "./following-sibling::*")
                                    preceding = elem.find_elements(By.XPATH, "./preceding-sibling::*")
                                    siblings_text = " ".join([f.text for f in (following[:3] + preceding[:2]) if f.text])
                                except:
                                    siblings_text = ""
                                
                                # Get parent's parent (sometimes FMV is in a container)
                                try:
                                    grandparent = parent.find_element(By.XPATH, "./..")
                                    grandparent_text = grandparent.text
                                except:
                                    grandparent_text = ""
                                
                                # Search in all collected text - prioritize text near "FMV by ALT"
                                full_text = (elem.text or "") + " " + (parent_text or "") + " " + (siblings_text or "") + " " + (grandparent_text or "")
                                
                                # Extract section around "FMV by" - NEW format (Phygitals removed "ALT" text)
                                # Also handle old "FMV by ALT" format
                                # Look for $ immediately before the number to avoid matching years
                                fmv_section_match = re.search(r'(?:fmv\s+by\s+\.?\s*alt|fmv\s+by\s+alt|fmv\s+by)[^$]{0,30}\$([\d,]+\.\d{2})', full_text, re.IGNORECASE)
                                if fmv_section_match:
                                    fmv_val = fmv_section_match.group(1).replace(',', '').strip()
                                    try:
                                        val = float(fmv_val)
                                        current_price_val = None
                                        if card.get('current_price'):
                                            try:
                                                current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                            except:
                                                pass
                                        if self.is_valid_fmv(val, current_price_val):
                                            card['fmv'] = f'${val:.2f}'
                                            card['fmv_source'] = 'alt'
                                            fmv_found = True
                                            break
                                    except:
                                        pass
                                
                                # Fallback: If just "FMV" found (no ALT), look for any price in container
                                if not fmv_found and 'fmv' in full_text.lower() and 'by' in full_text.lower():
                                    # Find any price in the container that's different from current price
                                    current_price_val = None
                                    if card.get('current_price'):
                                        try:
                                            current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                        except:
                                            pass
                                    
                                    all_container_prices = re.findall(r'\$([\d,]+\.\d{2})', full_text)
                                    for price_str in all_container_prices:
                                        try:
                                            price_val = float(price_str.replace(',', ''))
                                            if self.is_valid_fmv(price_val, current_price_val):
                                                card['fmv'] = f'${price_val:.2f}'
                                                card['fmv_source'] = 'alt'
                                                fmv_found = True
                                                break
                                        except:
                                            pass
                                    if fmv_found:
                                        break
                                
                                # Fallback: Look for dollar amount near FMV text (if primary match didn't work)
                                if not fmv_found:
                                    fmv_patterns = [
                                        r'\$([\d,]+\.\d{2})',  # Standard $12.34 with 2 decimals
                                    ]
                                    
                                    for pattern in fmv_patterns:
                                        fmv_match = re.search(pattern, full_text)
                                        if fmv_match:
                                            fmv_val = fmv_match.group(1).replace(',', '').strip()
                                            try:
                                                val = float(fmv_val)
                                                # Validate: FMV should be reasonable and different from common placeholders
                                                current_price_val = None
                                                if card.get('current_price'):
                                                    try:
                                                        current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                                    except:
                                                        pass
                                                
                                                if self.is_valid_fmv(val, current_price_val):
                                                    card['fmv'] = f'${val:.2f}'
                                                    card['fmv_source'] = 'alt'
                                                    fmv_found = True
                                                    break
                                            except:
                                                pass
                                
                                if fmv_found:
                                    break
                            except:
                                continue
                        if fmv_found:
                            break
                    except:
                        continue
            except:
                pass
            
            # Method 2: Search in HTML source directly (FMV might be in HTML attributes or structured data)
            if not fmv_found:
                try:
                    # Get fresh HTML source
                    page_html = self.driver.page_source
                    
                    # Search HTML source for FMV patterns (before BeautifulSoup parsing)
                    # Look for "FMV by ALT" followed by price within reasonable distance
                    html_fmv_patterns = [
                        r'FMV\s+by\s+\.?\s*ALT[:\s]*\$?([\d,]+\.?\d{2})',  # "FMV by .ALT: $13.42" - PRIORITIZE
                        r'FMV\s+by\s+ALT[:\s]*\$?([\d,]+\.?\d*)',  # "FMV by ALT: $14.28"
                        r'FMV\s+by\s+Alt[:\s]*\$?([\d,]+\.?\d*)',  # Case variation
                        r'fmv\s+by\s+\.?\s*alt[:\s]*\$?([\d,]+\.?\d{2})',  # "fmv by .alt: $13.42"
                        r'fmv\s+by\s+alt[:\s]*\$?([\d,]+\.?\d*)',  # Lowercase
                        r'FMV.*?\.?\s*ALT.*?\$?([\d,]+\.?\d{2})',  # FMV ... .ALT ... $13.42 (flexible spacing)
                        r'FMV\s+by\s+\.?\s*ALT[^$]*\$([\d,]+\.?\d{2})',  # FMV by .ALT ... $13.42 (anything between)
                        r'>([\d,]+\.?\d{2})<[^<]{0,200}FMV.*?\.?\s*ALT',  # Price tag followed by FMV .ALT within 200 chars
                        r'FMV.*?\.?\s*ALT[^$]{0,100}\$([\d,]+\.?\d{2})',  # FMV .ALT ... $13.42 within 100 chars
                    ]
                    
                    for pattern in html_fmv_patterns:
                        fmv_match = re.search(pattern, page_html, re.IGNORECASE)
                        if fmv_match:
                            fmv_val = fmv_match.group(1).replace(',', '').strip()
                            try:
                                val = float(fmv_val)
                                # Validate: FMV should be reasonable and different from current price
                                current_price_val = None
                                if card.get('current_price'):
                                    try:
                                        current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                    except:
                                        pass
                                
                                if self.is_valid_fmv(val, current_price_val):
                                    card['fmv'] = f'${val:.2f}'
                                    card['fmv_source'] = 'alt'
                                    fmv_found = True
                                    break
                            except:
                                pass
                    
                    # Also try parsing with BeautifulSoup and searching text
                    if not fmv_found:
                        soup_fresh = BeautifulSoup(page_html, 'html.parser')
                        page_text_full = soup_fresh.get_text()
                        
                        fmv_patterns = [
                            r'fmv\s+by\s+\.?\s*alt[:\s]*\$([\d,]+\.?\d{2})',  # "FMV by .ALT: $13.42" - PRIORITIZE THIS
                            r'fmv\s+by\s+alt[:\s]*\$([\d,]+\.?\d*)',  # "FMV by ALT: $12.50"
                            r'fmv\s+by\s+\.?\s*alt\s*\$([\d,]+\.?\d{2})',  # "FMV by .ALT $13.42" (no colon)
                            r'\.alt[:\s]*\$([\d,]+\.?\d{2})',  # ".ALT: $13.42"
                            r'fmv\s+by\s+alt\s*\$([\d,]+\.?\d*)',  # "FMV by ALT $12.50" (no colon)
                            r'alt[:\s]*\$([\d,]+\.?\d*)',  # "ALT: $12.50"
                            r'fmv[:\s]*\$([\d,]+\.?\d*)',  # "FMV: $12.50"
                            # Look for patterns with "by Alt" nearby
                            r'(?:fmv|fair\s+market).*?by.*?\.?\s*alt.*?\$([\d,]+\.?\d{2})',  # "FMV ... by ... .ALT $13.42"
                        ]
                        
                        for pattern in fmv_patterns:
                            fmv_match = re.search(pattern, page_text_full, re.IGNORECASE | re.DOTALL)
                            if fmv_match:
                                fmv_val = fmv_match.group(1).replace(',', '').strip()
                                try:
                                    val = float(fmv_val)
                                    # Validate against current price to avoid false matches
                                    current_price_val = None
                                    if card.get('current_price'):
                                        try:
                                            current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                        except:
                                            pass
                                    
                                    if self.is_valid_fmv(val, current_price_val):
                                        card['fmv'] = f'${val:.2f}'
                                        card['fmv_source'] = 'alt'
                                        fmv_found = True
                                        break
                                except:
                                    pass
                        
                        # Also search in original page_text if not found
                        if not fmv_found:
                            for pattern in fmv_patterns[:3]:
                                fmv_match = re.search(pattern, page_text, re.IGNORECASE)
                                if fmv_match:
                                    fmv_val = fmv_match.group(1).replace(',', '').strip()
                                    try:
                                        val = float(fmv_val)
                                        current_price_val = None
                                        if card.get('current_price'):
                                            try:
                                                current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                            except:
                                                pass
                                        if self.is_valid_fmv(val, current_price_val):
                                            card['fmv'] = f'${val:.2f}'
                                            card['fmv_source'] = 'alt'
                                            fmv_found = True
                                            break
                                    except:
                                        pass
                except Exception as e:
                    pass  # Continue to next method
            
            # Method 2b: Look for price-like elements near "FMV by ALT" text
            if not fmv_found:
                try:
                    # Find element containing "FMV by ALT" or "FMV by .ALT"
                    fmv_label_elem = None
                    try:
                        fmv_label_elem = self.driver.find_element(By.XPATH, "//*[contains(., 'FMV') and (contains(., 'ALT') or contains(., '.ALT'))]")
                    except:
                        pass
                    
                    if fmv_label_elem:
                        # Get the entire container (parent or parent's parent)
                        try:
                            container = fmv_label_elem.find_element(By.XPATH, "./ancestor::*[position()<=4]")  # Go up 4 levels for wider search
                            container_text = container.text or ""
                            
                            # Look for FMV pattern in container text
                            container_fmv_match = re.search(r'FMV\s+by\s+\.?\s*ALT[^$]{0,50}\$([\d,]+\.?\d{2})', container_text, re.IGNORECASE)
                            if container_fmv_match:
                                fmv_val = container_fmv_match.group(1).replace(',', '').strip()
                                try:
                                    val = float(fmv_val)
                                    current_price_val = None
                                    if card.get('current_price'):
                                        try:
                                            current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                        except:
                                            pass
                                    if self.is_valid_fmv(val, current_price_val):
                                        card['fmv'] = f'${val:.2f}'
                                        card['fmv_source'] = 'alt'
                                        fmv_found = True
                                except:
                                    pass
                            
                            # Also try finding price elements in container
                            if not fmv_found:
                                price_elements = container.find_elements(By.XPATH, ".//*[contains(text(), '$')]")
                                for price_elem in price_elements[:10]:  # Check more elements
                                    text = price_elem.text or ""
                                    # Extract price value - look specifically for 2 decimal format
                                    price_match = re.search(r'\$([\d,]+\.\d{2})', text)
                                    if price_match:
                                        fmv_val = price_match.group(1).replace(',', '').strip()
                                        try:
                                            val = float(fmv_val)
                                            current_price_val = None
                                            if card.get('current_price'):
                                                try:
                                                    current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                                except:
                                                    pass
                                            if self.is_valid_fmv(val, current_price_val):
                                                card['fmv'] = f'${val:.2f}'
                                                card['fmv_source'] = 'alt'
                                                fmv_found = True
                                                break
                                        except:
                                            pass
                        except:
                            pass
                except:
                    pass
            
            # Method 3: Look for FMV in all visible text one more time with fresh HTML
            if not fmv_found:
                try:
                    # Get completely fresh HTML and page text
                    final_html = self.driver.page_source
                    final_soup = BeautifulSoup(final_html, 'html.parser')
                    final_all_text = final_soup.get_text()
                    
                    # Try ALL possible FMV patterns on fresh text
                    all_fmv_patterns = [
                        r'FMV\s+by\s+\.?\s*ALT[:\s]*\$([\d,]+\.\d{2})',  # "FMV by .ALT: $13.42"
                        r'FMV\s+by\s+\.?\s*ALT\s*\$([\d,]+\.\d{2})',  # "FMV by .ALT $13.42" no colon
                        r'fmv\s+by\s+\.?\s*alt[:\s]*\$([\d,]+\.\d{2})',  # lowercase
                        r'\.alt[:\s]*\$([\d,]+\.\d{2})',  # Just ".ALT: $13.42"
                        r'FMV.*?\.?\s*ALT.*?\$([\d,]+\.\d{2})',  # Flexible spacing
                        # Fallback: If "FMV" is found, look for any price nearby (within 200 chars)
                        r'FMV[^$]{0,200}\$([\d,]+\.\d{2})',  # "FMV ... $13.42" (flexible, ALT might be in different element)
                    ]
                    
                    for pattern in all_fmv_patterns:
                        fmv_match = re.search(pattern, final_all_text, re.IGNORECASE | re.DOTALL)
                        if fmv_match:
                            fmv_val = fmv_match.group(1).replace(',', '').strip()
                            try:
                                val = float(fmv_val)
                                current_price_val = None
                                if card.get('current_price'):
                                    try:
                                        current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                    except:
                                        pass
                                if self.is_valid_fmv(val, current_price_val):
                                    card['fmv'] = f'${val:.2f}'
                                    card['fmv_source'] = 'alt'
                                    fmv_found = True
                                    break
                            except:
                                pass
                except:
                    pass
            
            # Method 4: Look for specific HTML structure and nearby elements
            if not fmv_found:
                try:
                    # Try finding elements with data-fmv or similar attributes
                    fmv_selectors_css = [
                        "[data-fmv]",
                        "[data-alt-fmv]",
                        "[data-alt]",
                        ".fmv",
                        ".alt-fmv",
                        "*[class*='fmv']",
                        "*[class*='alt']"
                    ]
                    
                    for selector in fmv_selectors_css:
                        try:
                            fmv_attrs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in fmv_attrs:
                                # Check multiple sources
                                text_sources = [
                                    elem.text,
                                    elem.get_attribute('value'),
                                    elem.get_attribute('data-fmv'),
                                    elem.get_attribute('data-alt-fmv'),
                                    elem.get_attribute('data-alt'),
                                    elem.get_attribute('innerText'),
                                    elem.get_attribute('textContent')
                                ]
                                
                                for text_source in text_sources:
                                    if text_source:
                                        fmv_match = re.search(r'\$?([\d,]+\.?\d*)', str(text_source))
                                        if fmv_match:
                                            fmv_val = fmv_match.group(1).replace(',', '').strip()
                                            try:
                                                val = float(fmv_val)
                                                current_price_val = None
                                                if card.get('current_price'):
                                                    try:
                                                        current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                                    except:
                                                        pass
                                                if self.is_valid_fmv(val, current_price_val):
                                                    card['fmv'] = f'${val:.2f}'
                                                    card['fmv_source'] = 'alt'
                                                    fmv_found = True
                                                    break
                                            except:
                                                pass
                                if fmv_found:
                                    break
                            if fmv_found:
                                break
                        except:
                            continue
                            
                    # Method 3b: Look for elements next to "FMV by ALT" text
                    if not fmv_found:
                        try:
                            # Find element containing "FMV" or "ALT", then look for $ amount in nearby siblings
                            fmv_containers = self.driver.find_elements(By.XPATH, 
                                "//*[contains(text(), 'FMV') or contains(text(), 'ALT')]")
                            for container in fmv_containers[:5]:  # Limit to first 5 matches
                                try:
                                    # Check next sibling, previous sibling, and parent
                                    siblings = container.find_elements(By.XPATH, "./following-sibling::* | ./preceding-sibling::* | ./parent::*")
                                    for sibling in siblings:
                                        text = sibling.text or sibling.get_attribute('innerText') or ''
                                        fmv_match = re.search(r'\$([\d,]+\.?\d*)', text)
                                        if fmv_match:
                                            fmv_val = fmv_match.group(1).replace(',', '').strip()
                                            try:
                                                val = float(fmv_val)
                                                current_price_val = None
                                                if card.get('current_price'):
                                                    try:
                                                        current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                                    except:
                                                        pass
                                                if self.is_valid_fmv(val, current_price_val):
                                                    card['fmv'] = f'${val:.2f}'
                                                    card['fmv_source'] = 'alt'
                                                    fmv_found = True
                                                    break
                                            except:
                                                pass
                                    if fmv_found:
                                        break
                                except:
                                    continue
                        except:
                            pass
                except:
                    pass
            
            # If no FMV found, set to "N/A" (will be calculated later)
            if not fmv_found:
                # Last attempt: Check fresh page source one more time after all waits
                try:
                    final_page_html = self.driver.page_source
                    # Try very specific pattern for "FMV by .ALT" with price
                    # Try multiple patterns as last attempt
                    final_patterns = [
                        r'FMV\s+by\s+\.?\s*ALT[^$]{0,100}\$([\d,]+\.?\d{2})',  # Standard format
                        r'FMV[^$]{0,300}\$([\d,]+\.\d{2})',  # Any price after FMV (ALT might be in different element)
                    ]
                    final_fmv_match = None
                    for pattern in final_patterns:
                        final_fmv_match = re.search(pattern, final_page_html, re.IGNORECASE)
                        if final_fmv_match:
                            break
                    if final_fmv_match:
                        fmv_val = final_fmv_match.group(1).replace(',', '').strip()
                        try:
                            val = float(fmv_val)
                            current_price_val = None
                            if card.get('current_price'):
                                try:
                                    current_price_val = float(card['current_price'].replace('$', '').replace(',', ''))
                                except:
                                    pass
                            if self.is_valid_fmv(val, current_price_val):
                                card['fmv'] = f'${val:.2f}'
                                card['fmv_source'] = 'alt'
                                fmv_found = True
                        except:
                            pass
                except:
                    pass
                
                if not fmv_found:
                    card['fmv'] = "N/A"
                    # Debug: Check if page has "FMV" or "ALT" text at all
                    try:
                        debug_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        if 'fmv' in debug_text and 'alt' in debug_text:
                            # Page has FMV/ALT text but extraction failed - log for debugging
                            # Extract a snippet to help debug
                            fmv_snippet = re.search(r'.{0,50}fmv.{0,50}alt.{0,50}', debug_text, re.IGNORECASE)
                            if fmv_snippet:
                                pass  # Could add debug logging here if needed
                    except:
                        pass
            
            card_num_match = re.search(r'#(\d+)', card['full_listing_name'])
            if card_num_match:
                card['card_number'] = card_num_match.group(1)
            
            # Validate and ensure FMV is properly set
            if card.get('fmv') and card['fmv'] != 'N/A' and not card.get('fmv_source'):
                # If FMV was set but source wasn't, assume it's from ALT (since that's what we look for)
                card['fmv_source'] = 'alt'
            
            # Debug: Log if key fields are missing
            if not card.get('current_price'):
                print(f"    ⚠️  WARNING: No price extracted for card")
            if not card.get('grader') or not card.get('grade'):
                print(f"    ⚠️  WARNING: Missing grader/grade: {card.get('grader')}/{card.get('grade')}")
            
            return card
            
        except Exception as e:
            return None
    
    def save_progress(self, page_num):
        """Save progress checkpoint"""
        if self.all_listings:
            filename = f'marketplace_url_progress_page{page_num}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
            print(f"\n*** Progress saved: {filename} ({len(self.all_listings):,} cards) ***\n")
    
    def save_final(self):
        """Save final results"""
        if not self.all_listings:
            print("\nNo data to save!")
            return
        
        print("\n" + "="*70)
        print("SAVING FINAL DATA")
        print("="*70)
        
        # JSON
        with open('phygitals_marketplace_complete.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, indent=2, ensure_ascii=False)
        print("Saved: phygitals_marketplace_complete.json")
        
        # Excel and CSV
        df = pd.DataFrame(self.all_listings)
        df.to_excel('phygitals_marketplace_complete.xlsx', index=False)
        print("Saved: phygitals_marketplace_complete.xlsx")
        
        df.to_csv('phygitals_marketplace_complete.csv', index=False, encoding='utf-8')
        print("Saved: phygitals_marketplace_complete.csv")
        
        print(f"\nTotal cards saved: {len(self.all_listings):,}")
        
        # Statistics
        print("\n" + "="*70)
        print("STATISTICS")
        print("="*70)
        
        if len(df) > 0:
            graders = df['grader'].value_counts()
            print("\nGraders:")
            for grader, count in graders.head(10).items():
                if grader:
                    print(f"  {grader}: {count:,}")
            
            grades = df['grade'].value_counts().head(10)
            print("\nTop Grades:")
            for grade, count in grades.items():
                if grade:
                    print(f"  Grade {grade}: {count:,}")
        
        print("\n" + "="*70)


def main():
    print("""
    ==============================================================
       Phygitals Marketplace Scraper - URL METHOD
       Navigates pages using direct URLs
    ==============================================================
    """)
    
    parser = argparse.ArgumentParser(description="Scrape Phygitals marketplace by direct page URLs.")
    parser.add_argument("--start-page", type=int, default=1, help="First marketplace page to scrape (default: 1).")
    parser.add_argument("--max-pages", type=int, default=None, help="Number of pages to scrape (default: all).")
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument("--resume", dest="resume", action="store_true", help="Resume from existing progress (default).")
    resume_group.add_argument("--no-resume", dest="resume", action="store_false", help="Ignore progress files and start fresh.")
    parser.set_defaults(resume=True)
    args = parser.parse_args()
    
    start_from = args.start_page
    max_pages = args.max_pages
    
    if args.resume:
        import glob
        progress_files = glob.glob('marketplace_url_progress_page*.json')
        if progress_files:
            page_nums = []
            for pf in progress_files:
                try:
                    match = re.search(r'page(\d+)', pf)
                    if match:
                        page_nums.append(int(match.group(1)))
                except:
                    pass
            
            if page_nums:
                last_page = max(page_nums)
                resume_page = last_page + 1
                if resume_page > start_from:
                    start_from = resume_page
                print(f"\n📊 RESUME MODE: Found existing progress up to page {last_page}")
                print(f"   Resuming from page {start_from}")
            else:
                print("\nFULL SCRAPE MODE: Starting from page 1")
        else:
            print("\nFULL SCRAPE MODE: Starting fresh from page 1")
    else:
        print("\nFULL SCRAPE MODE: Resume disabled – starting fresh")
    
    if max_pages is None:
        print("\nFULL SCRAPE MODE: Getting ALL 1,516 pages (24,254 cards)")
        print("   Estimated time: 6-8 hours")
        print("   Progress auto-saves after EVERY page")
        print("   Press Ctrl+C anytime to stop safely")
        print("   URL pattern: https://www.phygitals.com/marketplace?page=N")
    else:
        print(f"\nSCRAPE MODE: Getting {max_pages} pages starting at page {start_from}")
    
    print("\nStarting in 5 seconds...")
    time.sleep(5)
    
    scraper = URLMarketplaceScraper(start_page=start_from, max_pages=max_pages)
    
    try:
        scraper.scrape_all_pages()
    except KeyboardInterrupt:
        print("\nStopped by user!")
    
    scraper.save_final()
    print("\n✅ DONE!")


if __name__ == "__main__":
    main()

