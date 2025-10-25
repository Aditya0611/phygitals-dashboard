#!/usr/bin/env python3
"""
Enhanced PSA Certificate and Alt.xyz Integration Scraper
Extracts PSA certificate numbers and investigates Alt.xyz FMV data sources
"""

import json
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, parse_qs
import pandas as pd

class EnhancedPSAScraper:
    def __init__(self, data_file='phygitals_marketplace_complete.json'):
        self.data_file = data_file
        self.cards = self.load_data()
        self.enhanced_cards = []
        self.driver = None
        
    def load_data(self):
        """Load existing marketplace data"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("Chrome driver initialized")
    
    def extract_psa_certificate_number(self, card_data):
        """Extract PSA certificate number from card data"""
        try:
            # Look for PSA certificate patterns in the listing name
            listing_name = card_data.get('full_listing_name', '')
            
            # Common PSA certificate patterns
            patterns = [
                r'PSA\s*(\d{8,})',  # PSA followed by 8+ digits
                r'Cert\s*#?\s*(\d{8,})',  # Cert # followed by digits
                r'Certificate\s*#?\s*(\d{8,})',  # Certificate # followed by digits
                r'PSA\s*(\d{4,})',  # PSA followed by 4+ digits
            ]
            
            for pattern in patterns:
                match = re.search(pattern, listing_name, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # If no pattern found in name, try to extract from URL or other fields
            return None
            
        except Exception as e:
            print(f"Error extracting PSA certificate: {e}")
            return None
    
    def investigate_alt_xyz_integration(self, card_data):
        """Investigate how Phygitals gets Alt.xyz FMV data"""
        try:
            listing_url = card_data.get('listing_url', '')
            if not listing_url:
                return None
            
            # Navigate to the card page
            self.driver.get(listing_url)
            time.sleep(2)
            
            # Get page source and analyze
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Look for Alt.xyz related elements
            alt_xyz_info = {
                'alt_xyz_links': [],
                'fmv_source': 'unknown',
                'api_calls': [],
                'psa_certificate_number': None,
                'alt_xyz_integration_method': 'unknown'
            }
            
            # 1. Look for direct Alt.xyz links
            alt_links = soup.find_all('a', href=re.compile(r'alt\.xyz|altxyz', re.IGNORECASE))
            for link in alt_links:
                alt_xyz_info['alt_xyz_links'].append({
                    'url': link.get('href'),
                    'text': link.get_text(strip=True)
                })
            
            # 2. Look for PSA certificate numbers in the page
            page_text = soup.get_text()
            psa_patterns = [
                r'PSA\s*(\d{8,})',
                r'Certificate\s*#?\s*(\d{8,})',
                r'Cert\s*#?\s*(\d{8,})'
            ]
            
            for pattern in psa_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    alt_xyz_info['psa_certificate_number'] = match.group(1)
                    break
            
            # 3. Look for FMV source indicators
            fmv_indicators = [
                'alt.xyz', 'altxyz', 'psa', 'certificate', 'fmv', 'fair market value'
            ]
            
            for indicator in fmv_indicators:
                if indicator.lower() in page_text.lower():
                    alt_xyz_info['fmv_source'] = f'contains_{indicator}'
                    break
            
            # 4. Look for JavaScript or API calls that might fetch Alt.xyz data
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_content = script.string
                    if 'alt.xyz' in script_content.lower() or 'psa' in script_content.lower():
                        alt_xyz_info['api_calls'].append(script_content[:200] + '...')
            
            return alt_xyz_info
            
        except Exception as e:
            print(f"Error investigating Alt.xyz integration: {e}")
            return None
    
    def generate_alt_xyz_url(self, psa_certificate_number):
        """Generate Alt.xyz URL for PSA certificate"""
        if not psa_certificate_number:
            return None
        
        # Alt.xyz URL patterns for PSA certificates
        alt_xyz_urls = [
            f"https://alt.xyz/cert/{psa_certificate_number}",
            f"https://alt.xyz/psa/{psa_certificate_number}",
            f"https://alt.xyz/certificate/{psa_certificate_number}",
            f"https://www.alt.xyz/cert/{psa_certificate_number}",
        ]
        
        return alt_xyz_urls
    
    def scrape_alt_xyz_data(self, alt_xyz_url):
        """Scrape data from Alt.xyz for a PSA certificate"""
        try:
            if not alt_xyz_url:
                return None
            
            # Try to access Alt.xyz
            response = requests.get(alt_xyz_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract sales data
                sales_data = {
                    'url': alt_xyz_url,
                    'recent_sales': [],
                    'price_history': [],
                    'certificate_info': {}
                }
                
                # Look for sales data (this would need to be customized based on Alt.xyz structure)
                # This is a placeholder - actual implementation would depend on Alt.xyz's HTML structure
                
                return sales_data
            else:
                return None
                
        except Exception as e:
            print(f"Error scraping Alt.xyz: {e}")
            return None
    
    def process_all_cards(self):
        """Process all cards to extract PSA certificates and Alt.xyz data"""
        print("Starting Enhanced PSA Certificate and Alt.xyz Analysis")
        print("=" * 60)
        
        if not self.cards:
            print("No cards found in data file")
            return
        
        # Setup driver
        self.setup_driver()
        
        psa_cards = [card for card in self.cards if card.get('grader') == 'PSA']
        print(f"Found {len(psa_cards)} PSA cards to analyze")
        
        for i, card in enumerate(psa_cards, 1):
            print(f"\nProcessing PSA card {i}/{len(psa_cards)}: {card.get('full_listing_name', '')[:50]}...")
            
            # Extract PSA certificate number
            psa_cert = self.extract_psa_certificate_number(card)
            if psa_cert:
                print(f"  Found PSA certificate: {psa_cert}")
            else:
                print("  No PSA certificate number found in listing name")
            
            # Investigate Alt.xyz integration
            alt_xyz_info = self.investigate_alt_xyz_integration(card)
            if alt_xyz_info:
                print(f"  Alt.xyz links found: {len(alt_xyz_info.get('alt_xyz_links', []))}")
                print(f"  FMV source: {alt_xyz_info.get('fmv_source', 'unknown')}")
                if alt_xyz_info.get('psa_certificate_number'):
                    print(f"  PSA cert from page: {alt_xyz_info['psa_certificate_number']}")
            
            # Generate Alt.xyz URLs
            if psa_cert:
                alt_xyz_urls = self.generate_alt_xyz_url(psa_cert)
                print(f"  Generated Alt.xyz URLs: {len(alt_xyz_urls)}")
                
                # Try to scrape Alt.xyz data
                for url in alt_xyz_urls:
                    alt_data = self.scrape_alt_xyz_data(url)
                    if alt_data:
                        print(f"  Successfully scraped Alt.xyz data from: {url}")
                        break
            
            # Enhanced card data
            enhanced_card = card.copy()
            enhanced_card['psa_certificate_number'] = psa_cert
            enhanced_card['alt_xyz_integration'] = alt_xyz_info
            enhanced_card['alt_xyz_urls'] = self.generate_alt_xyz_url(psa_cert) if psa_cert else []
            
            self.enhanced_cards.append(enhanced_card)
            
            # Small delay to be respectful
            time.sleep(1)
        
        # Save enhanced data
        self.save_enhanced_data()
        
        if self.driver:
            self.driver.quit()
    
    def save_enhanced_data(self):
        """Save enhanced data with PSA certificates and Alt.xyz info"""
        try:
            # Save enhanced JSON
            with open('enhanced_psa_cards.json', 'w', encoding='utf-8') as f:
                json.dump(self.enhanced_cards, f, indent=2, ensure_ascii=False)
            
            # Create summary report
            summary = {
                'total_psa_cards': len(self.enhanced_cards),
                'cards_with_certificates': len([c for c in self.enhanced_cards if c.get('psa_certificate_number')]),
                'cards_with_alt_xyz_links': len([c for c in self.enhanced_cards if c.get('alt_xyz_integration', {}).get('alt_xyz_links')]),
                'fmv_sources': {},
                'alt_xyz_integration_methods': []
            }
            
            # Analyze FMV sources
            for card in self.enhanced_cards:
                fmv_source = card.get('alt_xyz_integration', {}).get('fmv_source', 'unknown')
                summary['fmv_sources'][fmv_source] = summary['fmv_sources'].get(fmv_source, 0) + 1
            
            # Save summary
            with open('psa_alt_xyz_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"\nEnhanced data saved:")
            print(f"  - enhanced_psa_cards.json ({len(self.enhanced_cards)} cards)")
            print(f"  - psa_alt_xyz_analysis.json (summary)")
            
        except Exception as e:
            print(f"Error saving enhanced data: {e}")

def main():
    """Main function"""
    print("Enhanced PSA Certificate and Alt.xyz Integration Analysis")
    print("=" * 60)
    
    scraper = EnhancedPSAScraper()
    scraper.process_all_cards()
    
    print("\nAnalysis complete!")
    print("Check enhanced_psa_cards.json for detailed results")
    print("Check psa_alt_xyz_analysis.json for summary")

if __name__ == "__main__":
    main()
