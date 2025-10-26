#!/usr/bin/env python3
"""
Advanced Filtering System for Phygitals Marketplace Data
Implements client requirements for filtering and Alt.xyz integration
"""

import json
import re
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import time

class PhygitalsFilterSystem:
    def __init__(self, data_file: str = 'phygitals_marketplace_complete.json'):
        """Initialize the filtering system with marketplace data"""
        self.data_file = data_file
        self.cards = self.load_data()
        self.filtered_cards = []
        
    def load_data(self) -> List[Dict]:
        """Load marketplace data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def parse_price(self, price_str: str) -> float:
        """Parse price string to float value"""
        if not price_str or price_str == "N/A":
            return 0.0
        # Remove $ and convert to float
        return float(re.sub(r'[^\d.]', '', str(price_str)))
    
    def extract_pokemon_name(self, full_name: str) -> str:
        """Extract Pokemon name from full listing name"""
        # Common Pokemon names to look for
        pokemon_names = [
            'Pikachu', 'Charizard', 'Blastoise', 'Venusaur', 'Mewtwo', 'Mew',
            'Lugia', 'Ho-Oh', 'Rayquaza', 'Groudon', 'Kyogre', 'Dialga',
            'Palkia', 'Giratina', 'Arceus', 'Zekrom', 'Reshiram', 'Kyurem',
            'Xerneas', 'Yveltal', 'Zygarde', 'Solgaleo', 'Lunala', 'Necrozma',
            'Zacian', 'Zamazenta', 'Eternatus', 'Calyrex', 'Koraidon', 'Miraidon'
        ]
        
        for pokemon in pokemon_names:
            if pokemon.lower() in full_name.lower():
                return pokemon
        
        # If no specific Pokemon found, try to extract from the name
        # Look for patterns like "Pokemon Name V" or "Pokemon Name EX"
        match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:V|EX|GX|VMAX|VSTAR)', full_name)
        if match:
            return match.group(1)
        
        return "Unknown"
    
    def filter_fmv_greater_than_price(self) -> List[Dict]:
        """Filter cards where FMV > current price (potential deals)"""
        deals = []
        for card in self.cards:
            current_price = self.parse_price(card.get('current_price', '0'))
            fmv = self.parse_price(card.get('fmv', '0'))
            
            if fmv > current_price and current_price > 0:
                card['potential_savings'] = fmv - current_price
                card['savings_percentage'] = ((fmv - current_price) / fmv) * 100
                deals.append(card)
        
        return sorted(deals, key=lambda x: x['potential_savings'], reverse=True)
    
    def filter_high_value_cards(self, min_value: float = 25.0) -> List[Dict]:
        """Filter cards where price OR FMV > specified value"""
        high_value = []
        for card in self.cards:
            current_price = self.parse_price(card.get('current_price', '0'))
            fmv = self.parse_price(card.get('fmv', '0'))
            
            if current_price >= min_value or fmv >= min_value:
                high_value.append(card)
        
        return sorted(high_value, key=lambda x: self.parse_price(x.get('fmv', '0')), reverse=True)
    
    def filter_by_pokemon_name(self, pokemon_names: List[str]) -> List[Dict]:
        """Filter cards by specific Pokemon names"""
        filtered = []
        for card in self.cards:
            full_name = card.get('full_listing_name', '').lower()
            pokemon_name = self.extract_pokemon_name(card.get('full_listing_name', ''))
            
            for target_pokemon in pokemon_names:
                if (target_pokemon.lower() in full_name or 
                    target_pokemon.lower() == pokemon_name.lower()):
                    filtered.append(card)
                    break
        
        return filtered
    
    def filter_by_price_range(self, min_price: float = 0.0, max_price: float = None) -> List[Dict]:
        """Filter cards by price range"""
        filtered = []
        for card in self.cards:
            current_price = self.parse_price(card.get('current_price', '0'))
            
            if current_price >= min_price:
                if max_price is None or current_price <= max_price:
                    filtered.append(card)
        
        return sorted(filtered, key=lambda x: self.parse_price(x.get('current_price', '0')), reverse=True)
    
    def get_all_cards(self) -> List[Dict]:
        """Get all cards sorted by price"""
        return sorted(self.cards, key=lambda x: self.parse_price(x.get('current_price', '0')), reverse=True)
    
    def filter_by_fmv_range(self, min_fmv: float = 0.0, max_fmv: float = None) -> List[Dict]:
        """Filter cards by FMV range"""
        filtered = []
        for card in self.cards:
            fmv = self.parse_price(card.get('fmv', '0'))
            
            if fmv >= min_fmv:
                if max_fmv is None or fmv <= max_fmv:
                    filtered.append(card)
        
        return sorted(filtered, key=lambda x: self.parse_price(x.get('fmv', '0')), reverse=True)
    
    def get_psa_cards_with_certificates(self) -> List[Dict]:
        """Get all PSA graded cards with certificate information"""
        psa_cards = []
        for card in self.cards:
            if card.get('grader', '').upper() == 'PSA':
                # Add certificate information
                card['certificate_type'] = 'PSA'
                card['certificate_number'] = card.get('card_number', 'N/A')
                card['certificate_url'] = f"https://www.psacard.com/cert/{card.get('card_number', '')}"
                psa_cards.append(card)
        
        return psa_cards
    
    def investigate_alt_xyz_links(self, sample_size: int = 10) -> Dict[str, Any]:
        """Investigate how cards might link to Alt.xyz for FMV data"""
        print("Investigating Alt.xyz integration possibilities...")
        
        # Sample cards for investigation
        sample_cards = self.cards[:sample_size]
        alt_xyz_info = {
            'total_investigated': len(sample_cards),
            'potential_links': [],
            'fmv_sources': [],
            'integration_possibilities': []
        }
        
        for card in sample_cards:
            # Check if FMV data might come from Alt.xyz
            fmv = card.get('fmv', '')
            current_price = card.get('current_price', '')
            
            if fmv and fmv != 'N/A':
                alt_xyz_info['fmv_sources'].append({
                    'card_name': card.get('full_listing_name', ''),
                    'fmv': fmv,
                    'current_price': current_price,
                    'potential_alt_link': f"https://alt.xyz/search?q={card.get('pokemon_name', '')}"
                })
        
        # Add integration possibilities
        alt_xyz_info['integration_possibilities'] = [
            "1. Direct API integration with Alt.xyz for real-time FMV data",
            "2. Web scraping Alt.xyz for historical sales data",
            "3. Batch processing to get FMV for all cards",
            "4. Real-time price comparison between Phygitals and Alt.xyz"
        ]
        
        return alt_xyz_info
    
    def get_top_sales_simulation(self, card: Dict) -> List[Dict]:
        """Simulate getting top 5 sales from Alt.xyz (placeholder implementation)"""
        # This would integrate with Alt.xyz API in a real implementation
        pokemon_name = self.extract_pokemon_name(card.get('full_listing_name', ''))
        grade = card.get('grade', '')
        grader = card.get('grader', '')
        
        # Simulated top sales data (in real implementation, this would come from Alt.xyz API)
        simulated_sales = [
            {
                'sale_date': '2024-10-15',
                'price': '$' + str(float(self.parse_price(card.get('fmv', '0')) * 1.1)),
                'grade': grade,
                'grader': grader,
                'condition': 'Near Mint',
                'source': 'Alt.xyz'
            },
            {
                'sale_date': '2024-10-10',
                'price': '$' + str(float(self.parse_price(card.get('fmv', '0')) * 0.95)),
                'grade': grade,
                'grader': grader,
                'condition': 'Near Mint',
                'source': 'Alt.xyz'
            },
            {
                'sale_date': '2024-10-05',
                'price': '$' + str(float(self.parse_price(card.get('fmv', '0')) * 1.05)),
                'grade': grade,
                'grader': grader,
                'condition': 'Near Mint',
                'source': 'Alt.xyz'
            },
            {
                'sale_date': '2024-09-28',
                'price': '$' + str(float(self.parse_price(card.get('fmv', '0')) * 0.9)),
                'grade': grade,
                'grader': grader,
                'condition': 'Near Mint',
                'source': 'Alt.xyz'
            },
            {
                'sale_date': '2024-09-20',
                'price': '$' + str(float(self.parse_price(card.get('fmv', '0')) * 1.15)),
                'grade': grade,
                'grader': grader,
                'condition': 'Near Mint',
                'source': 'Alt.xyz'
            }
        ]
        
        return simulated_sales
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive filtering report"""
        print("Generating comprehensive filtering report...")
        
        # Apply all filters
        deals = self.filter_fmv_greater_than_price()
        high_value = self.filter_high_value_cards(25.0)
        psa_cards = self.get_psa_cards_with_certificates()
        all_cards = self.get_all_cards()
        price_range_10_plus = self.filter_by_price_range(10.0)
        fmv_25_plus = self.filter_by_fmv_range(25.0)
        alt_xyz_info = self.investigate_alt_xyz_links()
        
        # Get top Pokemon names
        pokemon_counts = {}
        for card in self.cards:
            pokemon = self.extract_pokemon_name(card.get('full_listing_name', ''))
            pokemon_counts[pokemon] = pokemon_counts.get(pokemon, 0) + 1
        
        top_pokemon = sorted(pokemon_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        report = {
            'summary': {
                'total_cards': len(self.cards),
                'deals_found': len(deals),
                'high_value_cards': len(high_value),
                'psa_cards': len(psa_cards),
                'price_range_10_plus': len(price_range_10_plus),
                'fmv_25_plus': len(fmv_25_plus),
                'top_pokemon': top_pokemon
            },
            'deals': deals[:20],  # Top 20 deals
            'high_value_cards': high_value[:20],  # Top 20 high-value cards
            'all_cards': all_cards[:20],  # Top 20 all cards
            'price_range_10_plus': price_range_10_plus[:20],  # Top 20 cards $10+
            'fmv_25_plus': fmv_25_plus[:20],  # Top 20 cards FMV $25+
            'psa_cards_with_certificates': psa_cards[:20],  # Top 20 PSA cards
            'alt_xyz_integration': alt_xyz_info,
            'pokemon_breakdown': dict(top_pokemon)
        }
        
        return report
    
    def save_filtered_data(self, output_file: str = 'filtered_marketplace_data.json'):
        """Save filtered data to JSON file"""
        report = self.generate_comprehensive_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Filtered data saved to {output_file}")
        return report

def main():
    """Main function to run the filtering system"""
    print("Starting Phygitals Advanced Filtering System")
    print("=" * 60)
    
    # Initialize the filtering system
    filter_system = PhygitalsFilterSystem()
    
    if not filter_system.cards:
        print("No data found. Please ensure phygitals_marketplace_complete.json exists.")
        return
    
    print(f"Loaded {len(filter_system.cards)} cards for analysis")
    
    # Generate comprehensive report
    report = filter_system.save_filtered_data()
    
    # Display summary
    print("\nFILTERING RESULTS SUMMARY")
    print("=" * 40)
    print(f"Total Cards Analyzed: {report['summary']['total_cards']}")
    print(f"Deals Found (FMV > Price): {report['summary']['deals_found']}")
    print(f"High-Value Cards (>$250): {report['summary']['high_value_cards']}")
    print(f"PSA Cards with Certificates: {report['summary']['psa_cards']}")
    
    print("\nTOP POKEMON BY FREQUENCY")
    print("=" * 30)
    for pokemon, count in report['summary']['top_pokemon'][:5]:
        print(f"{pokemon}: {count} cards")
    
    print("\nTOP DEALS (FMV > Current Price)")
    print("=" * 35)
    for i, deal in enumerate(report['deals'][:5], 1):
        savings = deal.get('potential_savings', 0)
        percentage = deal.get('savings_percentage', 0)
        print(f"{i}. {deal.get('full_listing_name', '')[:50]}...")
        print(f"   Savings: ${savings:.2f} ({percentage:.1f}%)")
        print(f"   FMV: {deal.get('fmv')} | Price: {deal.get('current_price')}")
        print()
    
    print("Filtering complete! Check 'filtered_marketplace_data.json' for detailed results.")

if __name__ == "__main__":
    main()
