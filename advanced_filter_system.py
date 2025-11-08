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
import os

class PhygitalsFilterSystem:
    def __init__(self, data_file: str = 'phygitals_marketplace_complete.json'):
        """Initialize the filtering system with marketplace data"""
        self.data_file = data_file
        self.cards = self.load_data()
        self.cards = self.clean_listed_cards(self.cards)
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
        if not price_str or str(price_str).strip() in {"", "N/A"}:
            return 0.0
        # Remove $ and convert to float
        cleaned = re.sub(r'[^\d.-]', '', str(price_str))
        if cleaned in {"", "-", ".", "-.", "-0"}:
            return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def is_listed(self, card: Dict) -> bool:
        """Return True only for actively listed cards with a positive price and valid link."""
        has_url = bool(card.get('listing_url') or card.get('card_url') or card.get('url') or card.get('link'))
        price_raw = str(card.get('current_price') or card.get('price') or '').strip()
        price_txt = price_raw.lower()
        price_val = self.parse_price(price_raw)
        status_fields = [card.get('status'), card.get('listing_status'), card.get('availability'), card.get('state')]
        status_joined = ' | '.join([str(s).lower() for s in status_fields if s])
        boolean_flags = [card.get('listed'), card.get('is_listed'), card.get('available'), card.get('isAvailable')]
        flagged_false = any(v is False for v in boolean_flags)
        unlisted = (
            'unlisted' in status_joined or 'not listed' in status_joined or 'delisted' in status_joined or
            'inactive' in status_joined or 'unavailable' in status_joined or 'sold' in status_joined or
            'out of stock' in status_joined or 'unlisted' in price_txt or 'not for sale' in price_txt or flagged_false
        )
        # Optional local URL blocklist
        try:
            block_path = os.path.join(os.getcwd(), 'unlisted_blocklist.json')
            blocked = set()
            if os.path.exists(block_path):
                arr = json.load(open(block_path, 'r', encoding='utf-8'))
                if isinstance(arr, list):
                    blocked = set(str(x) for x in arr)
            url = str(card.get('listing_url') or card.get('card_url') or card.get('url') or card.get('link') or '')
            if url in blocked:
                return False
        except Exception:
            pass
        return has_url and price_val > 0 and not unlisted

    def clean_listed_cards(self, cards: List[Dict]) -> List[Dict]:
        """Filter input dataset to only include actively listed cards."""
        return [c for c in cards if self.is_listed(c)]

    def get_display_fmv(self, card: Dict) -> float:
        """ALT-first FMV for filtering and UI.
        Prefer any ALT field or existing FMV labeled as ALT; otherwise use card.fmv.
        If no ALT exists in the dataset, attempt a quick HTML sniff of the listing
        page to extract "FMV by ALT" and cache it on the card for next runs.
        """
        # Drop known bad FMVs
        if str(card.get('fmv_source', '')).lower() == 'grade_multiplier':
            return 0.0

        # 1) Prefer cached/explicit ALT fields
        fmv_raw = str(card.get('fmv', '') or '')
        if '2023' in fmv_raw:  # malformed concatenation like "189.002023"
            return 0.0

        alt_candidates = [
            card.get('alt_fmv'), card.get('alt_value'), card.get('alt_estimate'),
            card.get('alt_price'), card.get('fmv_alt'), card.get('alt'),
            # ephemeral cache from HTML sniff (set below)
            card.get('_alt_fmv_cached')
        ]
        for v in alt_candidates:
            val = self.parse_price(v or '')
            if val > 0:
                return val

        # 2) If fmv_source mentions alt, trust fmv
        if str(card.get('fmv_source', '')).lower().find('alt') != -1:
            val = self.parse_price(card.get('fmv', '0'))
            if val > 0:
                return val

        # 3) Try a lightweight HTML read of the listing to locate "FMV by ALT"
        listing_url = str(card.get('listing_url') or card.get('card_url') or card.get('url') or card.get('link') or '')
        if listing_url and not card.get('_alt_sniff_attempted'):
            try:
                resp = requests.get(listing_url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
                })
                if resp.ok:
                    text = resp.text
                    # Look for a section mentioning FMV and a $ amount nearby
                    # Examples: "FMV by ALT", "FMV by \uALT", etc.
                    snippet_idx = text.lower().find('fmv')
                    if snippet_idx != -1:
                        window = text[max(0, snippet_idx-200):snippet_idx+200]
                        m = re.search(r"\$\s*([0-9]+(?:\.[0-9]{2})?)", window)
                        if m:
                            alt_val = m.group(1)
                            val = self.parse_price(alt_val)
                            if val > 0:
                                # Cache onto card so subsequent calls are fast
                                card['_alt_fmv_cached'] = f"${val:.2f}"
                                card['_alt_sniff_attempted'] = True
                                return val
                card['_alt_sniff_attempted'] = True
            except Exception:
                # Network or parsing errors are non-fatal; just mark attempted
                card['_alt_sniff_attempted'] = True

        # 4) Fall back to provided FMV
        return self.parse_price(card.get('fmv', '0'))
    
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
            fmv = self.get_display_fmv(card)
            
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
            fmv = self.get_display_fmv(card)
            
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
            fmv = self.get_display_fmv(card)
            
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
    
    def get_affordable_psa_deals(self, min_price: float = 10.0, max_price: float = 15.0) -> List[Dict]:
        """
        Get affordable PSA deals in the $10-$15 range where FMV > Current Price
        Logic matches the dashboard screenshot: PSA cards only, price range $10-$15, FMV > Current Price
        """
        affordable_psa_deals = []
        
        for card in self.cards:
            # Must be PSA graded
            if card.get('grader', '').upper() != 'PSA':
                continue
                
            current_price = self.parse_price(card.get('current_price', '0'))
            fmv = self.get_display_fmv(card)
            
            # Check if current price is in range $10-$15
            if min_price <= current_price <= max_price:
                # Check if FMV > Current Price (deal condition)
                if fmv > current_price and fmv > 0:
                    # Calculate savings
                    potential_savings = fmv - current_price
                    savings_percentage = (potential_savings / fmv) * 100
                    
                    # Add deal information
                    card['potential_savings'] = potential_savings
                    card['savings_percentage'] = savings_percentage
                    card['deal_type'] = 'Affordable PSA Deal'
                    card['price_range'] = f'${min_price}-${max_price}'
                    
                    affordable_psa_deals.append(card)
        
        # Sort by savings percentage (highest first)
        return sorted(affordable_psa_deals, key=lambda x: x['savings_percentage'], reverse=True)
    
    def get_psa_deals_by_price_range(self, price_ranges: List[tuple]) -> Dict[str, List[Dict]]:
        """
        Get PSA deals organized by different price ranges
        price_ranges: List of tuples like [(10, 15), (15, 25), (25, 50)]
        """
        psa_deals_by_range = {}
        
        for min_price, max_price in price_ranges:
            range_name = f"PSA Deals (${min_price}-${max_price})"
            deals = self.get_affordable_psa_deals(min_price, max_price)
            psa_deals_by_range[range_name] = deals
        
        return psa_deals_by_range
    
    def get_all_price_tier_deals(self) -> Dict[str, List[Dict]]:
        """
        Get deals organized by comprehensive price tiers:
        $300+, $200-$300, $100-$200, $50-$100, $25-$50, $10-$25, Under $10
        """
        all_tier_deals = {}
        
        # Define price tiers
        price_tiers = [
            (300, float('inf'), "Premium Deals ($300+)"),
            (200, 300, "High-Value Deals ($200-$300)"),
            (100, 200, "Mid-Range Deals ($100-$200)"),
            (50, 100, "Budget Deals ($50-$100)"),
            (25, 50, "Affordable Deals ($25-$50)"),
            (10, 25, "Budget-Friendly Deals ($10-$25)"),
            (0, 10, "Entry-Level Deals (Under $10)")
        ]
        
        for min_price, max_price, tier_name in price_tiers:
            tier_deals = []
            
            for card in self.cards:
                # Must be PSA graded
                if card.get('grader', '').upper() != 'PSA':
                    continue
                    
                current_price = self.parse_price(card.get('current_price', '0'))
                fmv = self.get_display_fmv(card)
                
                # Check if current price is in this tier
                if min_price <= current_price <= max_price:
                    # Check if FMV > Current Price (deal condition)
                    if fmv > current_price and fmv > 0:
                        # Calculate savings
                        potential_savings = fmv - current_price
                        savings_percentage = (potential_savings / fmv) * 100
                        
                        # Add deal information
                        deal_card = card.copy()
                        deal_card['potential_savings'] = potential_savings
                        deal_card['savings_percentage'] = savings_percentage
                        deal_card['deal_type'] = tier_name
                        deal_card['price_tier'] = f'${min_price}-${max_price}' if max_price != float('inf') else f'${min_price}+'
                        
                        tier_deals.append(deal_card)
            
            # Sort by savings percentage (highest first)
            tier_deals.sort(key=lambda x: x['savings_percentage'], reverse=True)
            all_tier_deals[tier_name] = tier_deals
        
        return all_tier_deals
    
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
        affordable_psa_deals = self.get_affordable_psa_deals(10.0, 15.0)  # $10-$15 range
        psa_deals_by_range = self.get_psa_deals_by_price_range([(10, 15), (15, 25), (25, 50)])
        all_price_tier_deals = self.get_all_price_tier_deals()  # All price tiers
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
        
        # Calculate summary for all price tiers
        price_tier_summary = {}
        for tier_name, tier_deals in all_price_tier_deals.items():
            price_tier_summary[tier_name] = len(tier_deals)
        
        report = {
            'summary': {
                'total_cards': len(self.cards),
                'deals_found': len(deals),
                'high_value_cards': len(high_value),
                'psa_cards': len(psa_cards),
                'affordable_psa_deals': len(affordable_psa_deals),
                'price_range_10_plus': len(price_range_10_plus),
                'fmv_25_plus': len(fmv_25_plus),
                'top_pokemon': top_pokemon,
                'price_tier_summary': price_tier_summary
            },
            'deals': deals[:20],  # Top 20 deals
            'high_value_cards': high_value[:20],  # Top 20 high-value cards
            'affordable_psa_deals': affordable_psa_deals[:20],  # Top 20 affordable PSA deals ($10-$15)
            'psa_deals_by_range': psa_deals_by_range,  # PSA deals organized by price ranges
            'all_price_tier_deals': all_price_tier_deals,  # All price tier deals
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
    print(f"Affordable PSA Deals ($10-$15): {report['summary']['affordable_psa_deals']}")
    
    print("\nPSA DEALS BY PRICE TIER")
    print("=" * 40)
    for tier_name, count in report['summary']['price_tier_summary'].items():
        print(f"{tier_name}: {count} deals")
    
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
    
    print("\nAFFORDABLE PSA DEALS ($10-$15)")
    print("=" * 35)
    for i, deal in enumerate(report['affordable_psa_deals'][:5], 1):
        savings = deal.get('potential_savings', 0)
        percentage = deal.get('savings_percentage', 0)
        grade = deal.get('grade', 'N/A')
        print(f"{i}. {deal.get('pokemon_name', 'Unknown')} PSA {grade}")
        print(f"   Price: {deal.get('current_price')} | FMV: {deal.get('fmv')}")
        print(f"   Savings: ${savings:.2f} ({percentage:.1f}%)")
        print()
    
    print("Filtering complete! Check 'filtered_marketplace_data.json' for detailed results.")

if __name__ == "__main__":
    main()
