#!/usr/bin/env python3
"""
PSA Certificate and Alt.xyz Analysis
Analyzes existing data to understand PSA certificates and Alt.xyz integration
"""

import json
import re
from collections import Counter

class PSAAnalyzer:
    def __init__(self, data_file='phygitals_marketplace_complete.json'):
        self.data_file = data_file
        self.cards = self.load_data()
        
    def load_data(self):
        """Load marketplace data"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def extract_psa_certificate_patterns(self):
        """Extract PSA certificate number patterns from card names"""
        psa_cards = [card for card in self.cards if card.get('grader') == 'PSA']
        print(f"Analyzing {len(psa_cards)} PSA cards for certificate patterns...")
        
        certificate_patterns = []
        enhanced_psa_cards = []
        
        for card in psa_cards:
            listing_name = card.get('full_listing_name', '')
            
            # Enhanced card data
            enhanced_card = card.copy()
            enhanced_card['psa_certificate_number'] = None
            enhanced_card['certificate_patterns_found'] = []
            
            # Look for various PSA certificate patterns
            patterns = [
                (r'PSA\s*(\d{8,})', 'PSA_8_digits'),
                (r'PSA\s*(\d{4,7})', 'PSA_4_7_digits'),
                (r'Cert\s*#?\s*(\d{8,})', 'Cert_8_digits'),
                (r'Certificate\s*#?\s*(\d{8,})', 'Certificate_8_digits'),
                (r'#(\d{8,})', 'Hash_8_digits'),
                (r'(\d{8,})', 'Any_8_digits'),
            ]
            
            for pattern, pattern_name in patterns:
                matches = re.findall(pattern, listing_name, re.IGNORECASE)
                if matches:
                    enhanced_card['certificate_patterns_found'].append({
                        'pattern': pattern_name,
                        'matches': matches
                    })
                    if not enhanced_card['psa_certificate_number']:
                        enhanced_card['psa_certificate_number'] = matches[0]
            
            enhanced_psa_cards.append(enhanced_card)
        
        return enhanced_psa_cards
    
    def analyze_fmv_sources(self):
        """Analyze how FMV data is sourced"""
        print("\nAnalyzing FMV data sources...")
        
        fmv_analysis = {
            'cards_with_fmv': 0,
            'fmv_vs_price_analysis': [],
            'potential_alt_xyz_indicators': []
        }
        
        for card in self.cards:
            fmv = card.get('fmv', '')
            price = card.get('current_price', '')
            
            if fmv and price:
                fmv_analysis['cards_with_fmv'] += 1
                
                # Extract numeric values
                fmv_num = self.extract_price(fmv)
                price_num = self.extract_price(price)
                
                if fmv_num and price_num:
                    fmv_analysis['fmv_vs_price_analysis'].append({
                        'card_name': card.get('full_listing_name', ''),
                        'current_price': price_num,
                        'fmv': fmv_num,
                        'difference': fmv_num - price_num,
                        'percentage_diff': ((fmv_num - price_num) / price_num * 100) if price_num > 0 else 0
                    })
        
        return fmv_analysis
    
    def extract_price(self, price_str):
        """Extract numeric price from string"""
        if not price_str:
            return None
        
        # Remove $ and commas, extract number
        price_clean = re.sub(r'[^\d.]', '', str(price_str))
        try:
            return float(price_clean)
        except:
            return None
    
    def generate_alt_xyz_integration_report(self):
        """Generate report on Alt.xyz integration possibilities"""
        print("\nGenerating Alt.xyz integration report...")
        
        enhanced_psa_cards = self.extract_psa_certificate_patterns()
        
        # Analyze certificate patterns
        pattern_counts = Counter()
        for card in enhanced_psa_cards:
            for pattern_info in card.get('certificate_patterns_found', []):
                pattern_counts[pattern_info['pattern']] += 1
        
        # Generate Alt.xyz URLs for cards with certificates
        alt_xyz_integration = {
            'total_psa_cards': len(enhanced_psa_cards),
            'cards_with_certificates': len([c for c in enhanced_psa_cards if c.get('psa_certificate_number')]),
            'certificate_patterns': dict(pattern_counts),
            'alt_xyz_url_examples': [],
            'integration_recommendations': []
        }
        
        # Generate example Alt.xyz URLs
        for card in enhanced_psa_cards[:5]:  # First 5 cards as examples
            if card.get('psa_certificate_number'):
                cert_num = card['psa_certificate_number']
                alt_xyz_urls = [
                    f"https://alt.xyz/cert/{cert_num}",
                    f"https://alt.xyz/psa/{cert_num}",
                    f"https://alt.xyz/certificate/{cert_num}",
                ]
                alt_xyz_integration['alt_xyz_url_examples'].append({
                    'card_name': card.get('full_listing_name', ''),
                    'certificate_number': cert_num,
                    'alt_xyz_urls': alt_xyz_urls
                })
        
        # Integration recommendations
        alt_xyz_integration['integration_recommendations'] = [
            "1. PSA Certificate Extraction: Use regex patterns to extract certificate numbers from listing names",
            "2. Alt.xyz URL Generation: Create URLs using pattern https://alt.xyz/cert/{certificate_number}",
            "3. API Integration: Implement Alt.xyz API calls to fetch recent sales data",
            "4. Data Enhancement: Add Alt.xyz sales history to card data",
            "5. Top 5 Sales: Scrape Alt.xyz for recent sales of each PSA card"
        ]
        
        return alt_xyz_integration
    
    def create_enhanced_dashboard_data(self):
        """Create enhanced data for dashboard with PSA certificates and Alt.xyz integration"""
        print("\nCreating enhanced dashboard data...")
        
        enhanced_psa_cards = self.extract_psa_certificate_patterns()
        fmv_analysis = self.analyze_fmv_sources()
        alt_xyz_report = self.generate_alt_xyz_integration_report()
        
        # Create enhanced data structure
        enhanced_data = {
            'summary': {
                'total_cards': len(self.cards),
                'psa_cards': len(enhanced_psa_cards),
                'cards_with_certificates': len([c for c in enhanced_psa_cards if c.get('psa_certificate_number')]),
                'cards_with_fmv': fmv_analysis['cards_with_fmv'],
                'alt_xyz_integration_ready': len([c for c in enhanced_psa_cards if c.get('psa_certificate_number')])
            },
            'psa_cards_with_certificates': [
                {
                    'card_name': card.get('full_listing_name', ''),
                    'psa_certificate_number': card.get('psa_certificate_number'),
                    'grader': card.get('grader'),
                    'grade': card.get('grade'),
                    'current_price': card.get('current_price'),
                    'fmv': card.get('fmv'),
                    'alt_xyz_urls': [
                        f"https://alt.xyz/cert/{card.get('psa_certificate_number')}",
                        f"https://alt.xyz/psa/{card.get('psa_certificate_number')}"
                    ] if card.get('psa_certificate_number') else []
                }
                for card in enhanced_psa_cards if card.get('psa_certificate_number')
            ],
            'alt_xyz_integration': alt_xyz_report,
            'fmv_analysis': fmv_analysis,
            'integration_status': {
                'psa_certificate_extraction': 'Ready',
                'alt_xyz_url_generation': 'Ready', 
                'alt_xyz_api_integration': 'Needs Implementation',
                'top_5_sales_scraping': 'Needs Implementation'
            }
        }
        
        return enhanced_data
    
    def save_results(self):
        """Save analysis results"""
        print("\nSaving analysis results...")
        
        enhanced_data = self.create_enhanced_dashboard_data()
        
        # Save enhanced data
        with open('enhanced_psa_alt_xyz_data.json', 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        # Save detailed PSA cards
        enhanced_psa_cards = self.extract_psa_certificate_patterns()
        with open('detailed_psa_cards.json', 'w', encoding='utf-8') as f:
            json.dump(enhanced_psa_cards, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved:")
        print(f"  - enhanced_psa_alt_xyz_data.json (dashboard data)")
        print(f"  - detailed_psa_cards.json (detailed PSA cards)")
        
        return enhanced_data

def main():
    """Main analysis function"""
    print("PSA Certificate and Alt.xyz Integration Analysis")
    print("=" * 60)
    
    analyzer = PSAAnalyzer()
    
    if not analyzer.cards:
        print("No cards found in data file")
        return
    
    print(f"Loaded {len(analyzer.cards)} cards for analysis")
    
    # Run analysis
    enhanced_data = analyzer.save_results()
    
    # Print summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total Cards: {enhanced_data['summary']['total_cards']}")
    print(f"PSA Cards: {enhanced_data['summary']['psa_cards']}")
    print(f"Cards with Certificates: {enhanced_data['summary']['cards_with_certificates']}")
    print(f"Cards with FMV: {enhanced_data['summary']['cards_with_fmv']}")
    print(f"Alt.xyz Integration Ready: {enhanced_data['summary']['alt_xyz_integration_ready']}")
    
    print("\nPSA Certificate Patterns Found:")
    for pattern, count in enhanced_data['alt_xyz_integration']['certificate_patterns'].items():
        print(f"  {pattern}: {count}")
    
    print("\nIntegration Recommendations:")
    for rec in enhanced_data['alt_xyz_integration']['integration_recommendations']:
        print(f"  {rec}")
    
    print("\nSample PSA Cards with Certificates:")
    for i, card in enumerate(enhanced_data['psa_cards_with_certificates'][:3], 1):
        print(f"  {i}. {card['card_name'][:50]}...")
        print(f"     Certificate: {card['psa_certificate_number']}")
        print(f"     Alt.xyz URLs: {len(card['alt_xyz_urls'])} generated")

if __name__ == "__main__":
    main()
