#!/usr/bin/env python3
"""
PSA Certificate Number Extractor
Visits individual PSA card pages to extract certificate numbers
"""

import json
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class PSACertificateExtractor:
    def __init__(self, data_file='phygitals_marketplace_complete.json'):
        self.data_file = data_file
        self.cards = self.load_data()
        self.driver = None
        self.enhanced_psa_cards = []
        
    def load_data(self):
        """Load marketplace data"""
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
    
    def extract_psa_certificate_from_page(self, card_url):
        """Extract PSA certificate number from individual card page"""
        try:
            self.driver.get(card_url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            page_text = soup.get_text()
            
            # Look for PSA certificate patterns
            certificate_patterns = [
                r'PSA\s*Cert(?:ificate)?\s*#?\s*(\d{8,})',  # PSA Cert #12345678
                r'Cert(?:ificate)?\s*#?\s*(\d{8,})',        # Cert #12345678
                r'PSA\s*(\d{8,})',                          # PSA 12345678
                r'Certificate\s*#?\s*(\d{8,})',              # Certificate #12345678
                r'Cert\s*#?\s*(\d{8,})',                    # Cert #12345678
                r'#(\d{8,})',                               # #12345678
                r'(\d{8,})',                               # Any 8+ digit number
            ]
            
            for pattern in certificate_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    return (matches[0], [])
            
            # Look for Alt.xyz links or references
            alt_xyz_links = soup.find_all('a', href=re.compile(r'alt\.xyz|altxyz', re.IGNORECASE))
            alt_xyz_info = []
            for link in alt_xyz_links:
                alt_xyz_info.append({
                    'url': link.get('href'),
                    'text': link.get_text(strip=True)
                })
            
            return (None, alt_xyz_info)
            
        except Exception as e:
            print(f"Error extracting certificate from {card_url}: {e}")
            return (None, [])
    
    def generate_alt_xyz_urls(self, certificate_number):
        """Generate Alt.xyz URLs for PSA certificate"""
        if not certificate_number:
            return []
        
        return [
            f"https://alt.xyz/cert/{certificate_number}",
            f"https://alt.xyz/psa/{certificate_number}",
            f"https://alt.xyz/certificate/{certificate_number}",
            f"https://www.alt.xyz/cert/{certificate_number}",
        ]
    
    def process_psa_cards(self, max_cards=20):
        """Process PSA cards to extract certificate numbers"""
        psa_cards = [card for card in self.cards if card.get('grader') == 'PSA']
        
        print(f"Processing {len(psa_cards) if max_cards is None else min(len(psa_cards), max_cards)} PSA cards...")
        
        self.setup_driver()
        
        try:
            cards_to_process = psa_cards if max_cards is None else psa_cards[:max_cards]
            for i, card in enumerate(cards_to_process, 1):
                print(f"\nProcessing PSA card {i}/{len(cards_to_process)}: {card.get('full_listing_name', '')[:50]}...")
                
                card_url = card.get('listing_url', '')
                if not card_url:
                    print("  No listing URL found")
                    continue
                
                # Extract certificate number
                certificate_number, alt_xyz_links = self.extract_psa_certificate_from_page(card_url)
                
                # Enhanced card data
                enhanced_card = card.copy()
                enhanced_card['psa_certificate_number'] = certificate_number
                enhanced_card['alt_xyz_links_found'] = alt_xyz_links
                enhanced_card['alt_xyz_urls'] = self.generate_alt_xyz_urls(certificate_number) if certificate_number else []
                
                if certificate_number:
                    print(f"  ✓ Found PSA certificate: {certificate_number}")
                    print(f"  ✓ Generated {len(enhanced_card['alt_xyz_urls'])} Alt.xyz URLs")
                else:
                    print("  ✗ No PSA certificate number found")
                
                if alt_xyz_links:
                    print(f"  ✓ Found {len(alt_xyz_links)} Alt.xyz links on page")
                
                self.enhanced_psa_cards.append(enhanced_card)
                
                # Small delay to be respectful
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopped by user")
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """Save enhanced PSA card data"""
        try:
            # Save enhanced PSA cards
            with open('enhanced_psa_cards_with_certificates.json', 'w', encoding='utf-8') as f:
                json.dump(self.enhanced_psa_cards, f, indent=2, ensure_ascii=False)
            
            # Create summary
            summary = {
                'total_processed': len(self.enhanced_psa_cards),
                'cards_with_certificates': len([c for c in self.enhanced_psa_cards if c.get('psa_certificate_number')]),
                'cards_with_alt_xyz_links': len([c for c in self.enhanced_psa_cards if c.get('alt_xyz_links_found')]),
                'certificate_numbers': [c.get('psa_certificate_number') for c in self.enhanced_psa_cards if c.get('psa_certificate_number')],
                'alt_xyz_integration_ready': len([c for c in self.enhanced_psa_cards if c.get('psa_certificate_number')])
            }
            
            with open('psa_certificate_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"\nResults saved:")
            print(f"  - enhanced_psa_cards_with_certificates.json ({len(self.enhanced_psa_cards)} cards)")
            print(f"  - psa_certificate_summary.json (summary)")
            
            return summary
            
        except Exception as e:
            print(f"Error saving results: {e}")
            return None

def main():
    """Main function"""
    print("PSA Certificate Number Extractor")
    print("=" * 50)
    
    extractor = PSACertificateExtractor()
    
    if not extractor.cards:
        print("No cards found in data file")
        return
    
    # Process PSA cards (limit to 20 for testing)
    extractor.process_psa_cards(max_cards=None)  # Process ALL PSA cards
    
    # Save results
    summary = extractor.save_results()
    
    if summary:
        print("\n" + "="*50)
        print("EXTRACTION SUMMARY")
        print("="*50)
        print(f"Total Processed: {summary['total_processed']}")
        print(f"Cards with Certificates: {summary['cards_with_certificates']}")
        print(f"Cards with Alt.xyz Links: {summary['cards_with_alt_xyz_links']}")
        print(f"Alt.xyz Integration Ready: {summary['alt_xyz_integration_ready']}")
        
        if summary['certificate_numbers']:
            print(f"\nSample Certificate Numbers:")
            for cert in summary['certificate_numbers'][:5]:
                print(f"  - {cert}")

if __name__ == "__main__":
    main()
