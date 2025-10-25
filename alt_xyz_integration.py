#!/usr/bin/env python3
"""
Alt.xyz Integration System
Generates Alt.xyz URLs and provides integration for PSA cards
"""

import json
import requests
from urllib.parse import urlparse
import time

class AltXYZIntegration:
    def __init__(self, psa_data_file='enhanced_psa_cards_with_certificates.json'):
        self.psa_data_file = psa_data_file
        self.psa_cards = self.load_psa_data()
        
    def load_psa_data(self):
        """Load PSA cards with certificates"""
        try:
            with open(self.psa_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading PSA data: {e}")
            return []
    
    def generate_alt_xyz_urls(self, certificate_number):
        """Generate Alt.xyz URLs for PSA certificate"""
        if not certificate_number:
            return []
        
        return [
            f"https://alt.xyz/cert/{certificate_number}",
            f"https://alt.xyz/psa/{certificate_number}",
            f"https://alt.xyz/certificate/{certificate_number}",
            f"https://www.alt.xyz/cert/{certificate_number}",
            f"https://www.alt.xyz/psa/{certificate_number}",
        ]
    
    def test_alt_xyz_accessibility(self, certificate_number):
        """Test if Alt.xyz URLs are accessible for a certificate"""
        urls = self.generate_alt_xyz_urls(certificate_number)
        results = []
        
        for url in urls:
            try:
                response = requests.get(url, timeout=10, allow_redirects=True)
                results.append({
                    'url': url,
                    'status_code': response.status_code,
                    'accessible': response.status_code == 200,
                    'final_url': response.url if response.url != url else None
                })
            except Exception as e:
                results.append({
                    'url': url,
                    'status_code': None,
                    'accessible': False,
                    'error': str(e)
                })
        
        return results
    
    def create_alt_xyz_integration_data(self):
        """Create comprehensive Alt.xyz integration data"""
        print("Creating Alt.xyz integration data...")
        
        integration_data = {
            'summary': {
                'total_psa_cards': len(self.psa_cards),
                'cards_with_certificates': len([c for c in self.psa_cards if c.get('psa_certificate_number')]),
                'alt_xyz_integration_ready': len([c for c in self.psa_cards if c.get('psa_certificate_number')])
            },
            'psa_cards_with_alt_xyz': [],
            'alt_xyz_url_patterns': {
                'certificate_url': 'https://alt.xyz/cert/{certificate_number}',
                'psa_url': 'https://alt.xyz/psa/{certificate_number}',
                'certificate_alt_url': 'https://www.alt.xyz/cert/{certificate_number}',
                'psa_alt_url': 'https://www.alt.xyz/psa/{certificate_number}'
            },
            'integration_instructions': {
                'step_1': 'Extract PSA certificate numbers from card pages',
                'step_2': 'Generate Alt.xyz URLs using certificate numbers',
                'step_3': 'Implement Alt.xyz API calls for sales data',
                'step_4': 'Scrape Alt.xyz for top 5 recent sales',
                'step_5': 'Integrate sales data into dashboard'
            },
            'sample_certificates': [],
            'top_5_sales_template': {
                'description': 'Template for Alt.xyz top 5 sales data',
                'fields': [
                    'sale_date',
                    'sale_price', 
                    'grade',
                    'condition',
                    'seller',
                    'buyer',
                    'auction_house'
                ]
            }
        }
        
        # Process PSA cards with certificates
        for card in self.psa_cards:
            if card.get('psa_certificate_number'):
                certificate_number = card['psa_certificate_number']
                alt_xyz_urls = self.generate_alt_xyz_urls(certificate_number)
                
                enhanced_card = {
                    'card_name': card.get('full_listing_name', ''),
                    'psa_certificate_number': certificate_number,
                    'grader': card.get('grader'),
                    'grade': card.get('grade'),
                    'current_price': card.get('current_price'),
                    'fmv': card.get('fmv'),
                    'listing_url': card.get('listing_url'),
                    'alt_xyz_urls': alt_xyz_urls,
                    'primary_alt_xyz_url': alt_xyz_urls[0] if alt_xyz_urls else None,
                    'alt_xyz_integration_status': 'Ready'
                }
                
                integration_data['psa_cards_with_alt_xyz'].append(enhanced_card)
                
                # Add to sample certificates
                if len(integration_data['sample_certificates']) < 5:
                    integration_data['sample_certificates'].append({
                        'certificate_number': certificate_number,
                        'card_name': card.get('full_listing_name', '')[:50],
                        'alt_xyz_url': alt_xyz_urls[0] if alt_xyz_urls else None
                    })
        
        return integration_data
    
    def create_dashboard_integration(self):
        """Create data structure for dashboard integration"""
        print("Creating dashboard integration data...")
        
        integration_data = self.create_alt_xyz_integration_data()
        
        # Create dashboard-ready data
        dashboard_data = {
            'psa_certificates': {
                'total_cards': integration_data['summary']['total_psa_cards'],
                'cards_with_certificates': integration_data['summary']['cards_with_certificates'],
                'integration_ready': integration_data['summary']['alt_xyz_integration_ready']
            },
            'alt_xyz_integration': {
                'status': 'Ready',
                'url_pattern': 'https://alt.xyz/cert/{certificate_number}',
                'sample_urls': integration_data['sample_certificates'],
                'integration_steps': integration_data['integration_instructions']
            },
            'enhanced_psa_cards': integration_data['psa_cards_with_alt_xyz'],
            'top_5_sales_implementation': {
                'description': 'Implementation guide for top 5 sales from Alt.xyz',
                'method_1': 'Direct Alt.xyz API calls using certificate numbers',
                'method_2': 'Web scraping Alt.xyz pages for sales history',
                'method_3': 'Integration with Alt.xyz partner API if available'
            }
        }
        
        return dashboard_data
    
    def save_integration_data(self):
        """Save Alt.xyz integration data"""
        print("Saving Alt.xyz integration data...")
        
        # Create comprehensive integration data
        integration_data = self.create_alt_xyz_integration_data()
        dashboard_data = self.create_dashboard_integration()
        
        # Save files
        with open('alt_xyz_integration_data.json', 'w', encoding='utf-8') as f:
            json.dump(integration_data, f, indent=2, ensure_ascii=False)
        
        with open('dashboard_alt_xyz_data.json', 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        
        print(f"Integration data saved:")
        print(f"  - alt_xyz_integration_data.json (comprehensive data)")
        print(f"  - dashboard_alt_xyz_data.json (dashboard integration)")
        
        return integration_data, dashboard_data

def main():
    """Main function"""
    print("Alt.xyz Integration System")
    print("=" * 50)
    
    integration = AltXYZIntegration()
    
    if not integration.psa_cards:
        print("No PSA cards found. Please run psa_certificate_extractor.py first.")
        return
    
    print(f"Loaded {len(integration.psa_cards)} PSA cards with certificates")
    
    # Create and save integration data
    integration_data, dashboard_data = integration.save_integration_data()
    
    # Print summary
    print("\n" + "="*50)
    print("ALT.XYZ INTEGRATION SUMMARY")
    print("="*50)
    print(f"Total PSA Cards: {integration_data['summary']['total_psa_cards']}")
    print(f"Cards with Certificates: {integration_data['summary']['cards_with_certificates']}")
    print(f"Alt.xyz Integration Ready: {integration_data['summary']['alt_xyz_integration_ready']}")
    
    print(f"\nSample Certificate Numbers:")
    for cert in integration_data['sample_certificates']:
        print(f"  - {cert['certificate_number']}: {cert['card_name']}")
        print(f"    Alt.xyz URL: {cert['alt_xyz_url']}")
    
    print(f"\nIntegration Steps:")
    for step, description in integration_data['integration_instructions'].items():
        print(f"  {step}: {description}")
    
    print(f"\nAlt.xyz URL Patterns:")
    for pattern_name, pattern in integration_data['alt_xyz_url_patterns'].items():
        print(f"  {pattern_name}: {pattern}")

if __name__ == "__main__":
    main()
