#!/usr/bin/env python3
"""
Enhanced Deal Intelligence System
Combines Phygitals listings with ALT.xyz market data to find "crazy deals"
"""

import json
import re
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class DealIntelligenceSystem:
    def __init__(self, data_file: str = 'phygitals_marketplace_complete.json'):
        self.data_file = data_file
        self.cards = self.load_data()
        
    def load_data(self) -> List[Dict]:
        """Load marketplace data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                raw_cards = json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return []

        if not isinstance(raw_cards, list):
            return []

        cleaned_cards: List[Dict] = []
        seen_keys = set()

        for card in raw_cards:
            if not isinstance(card, dict):
                continue

            normalized_name = self.normalize_name(card.get('full_listing_name') or card.get('pokemon_name') or '')
            grader = str(card.get('grader', '')).upper().strip()
            grade = str(card.get('grade', '')).strip()
            price_value = self.parse_price(card.get('current_price'))
            fmv_value = self.parse_price(card.get('fmv'))

            dedupe_key = (normalized_name, grader, grade, round(price_value, 2), round(fmv_value, 2))
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)

            card['current_price_value'] = price_value
            card['fmv_value'] = fmv_value

            cleaned_cards.append(card)

        return cleaned_cards
    
    def parse_price(self, price_str: Any) -> float:
        """Parse price string to float value"""
        if price_str is None:
            return 0.0

        numeric_part = re.sub(r'[^\d.-]', '', str(price_str)).strip()
        if not numeric_part or numeric_part in {'.', '-', '-.', '-0'}:
            return 0.0

        try:
            return float(numeric_part)
        except ValueError:
            return 0.0

    def normalize_name(self, value: str) -> str:
        if not value:
            return ''
        normalized = re.sub(r'\s+', ' ', value).strip().lower()
        return normalized
    
    def calculate_deal_score(self, card: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive deal score combining multiple factors:
        - Savings percentage and absolute amount
        - Recent sales velocity (if available)
        - Grade quality bonus
        - Set/popularity bonus
        - Market momentum
        """
        current_price = card.get('current_price_value')
        if current_price is None:
            current_price = self.parse_price(card.get('current_price', '0'))

        fmv = card.get('fmv_value')
        if fmv is None:
            fmv = self.parse_price(card.get('fmv', '0'))

        # Guard against unrealistic/dirty FMVs: ignore if >$500 or >3x current price
        if fmv > 500 or (current_price > 0 and fmv > current_price * 3):
            fmv = 0.0
        
        if current_price <= 0:
            return {'deal_score': 0, 'deal_tier': 'No Deal'}
        
        # For cards with price >= $50, use more flexible scoring
        # Don't strictly require FMV > price, but still prefer it
        is_premium_card = current_price >= 50
        
        if not is_premium_card:
            # For cards < $50, still require FMV > price to be a deal
            if fmv <= current_price:
                return {'deal_score': 0, 'deal_tier': 'No Deal'}
        
        # Enforce stricter FMV source rules for premium graded cards
        # But for premium cards (>= $50), be more flexible
        fmv_source = str(card.get('fmv_source', '')).lower()
        grader = card.get('grader', '').upper()
        try:
            grade_val_for_source = float(str(card.get('grade', '0')))
        except:
            grade_val_for_source = 0.0

        # For high-grade (9+) PSA/CGC/BGS, only accept FMV from real market (unless premium card)
        if grade_val_for_source >= 9 and grader in ('PSA', 'CGC', 'BGS') and not is_premium_card:
            allowed_sources = {'similar_cards', 'alt_verified', 'alt_only_high_grade'}
            if fmv_source not in allowed_sources:
                return {'deal_score': 0, 'deal_tier': 'No Deal'}

        # In general, ignore pure grade_multiplier FMVs (unless premium card)
        if fmv_source == 'grade_multiplier' and not is_premium_card:
            return {'deal_score': 0, 'deal_tier': 'No Deal'}

        # Core savings metrics
        # For premium cards (>= $50), handle cases where FMV might be <= price
        if fmv > 0:
            absolute_savings = fmv - current_price
            savings_percentage = (absolute_savings / fmv) * 100 if fmv > 0 else 0
        else:
            # If no FMV, use price as value indicator for premium cards
            absolute_savings = 0
            savings_percentage = 0
        
        # For premium cards, give base score even without FMV > price
        # Score based on card quality, grade, and price point
        if is_premium_card and fmv <= current_price and fmv > 0:
            # Still a valuable card, just use smaller positive value
            absolute_savings = max(0, (fmv * 0.95) - current_price)  # Give small buffer
            savings_percentage = (absolute_savings / current_price) * 100 if current_price > 0 else 0
        elif is_premium_card and fmv == 0:
            # No FMV data, but it's premium priced - give base score
            absolute_savings = 0
            savings_percentage = 0
        
        # Grade will be used directly in grade_score calculation below
        grade = card.get('grade', '0')
        
        # Set/popularity bonus
        card_name = card.get('full_listing_name', '').lower()
        pokemon_name = card.get('pokemon_name', '').lower()
        popularity_bonus = 0
        
        high_demand_keywords = [
            'charizard', 'blastoise', 'venusaur', 'pikachu', 'mewtwo', 'mew',
            'first edition', 'shadowless', 'base set', 'jungle', 'fossil',
            'japanese', 'promo', 'anniversary'
        ]
        
        for keyword in high_demand_keywords:
            if keyword in card_name or keyword in pokemon_name:
                popularity_bonus += 0.1
        
        # Market momentum (simulated - would integrate with ALT.xyz API)
        momentum_bonus = 0
        if absolute_savings > 100:  # High absolute savings
            momentum_bonus += 0.2
        elif absolute_savings > 50:
            momentum_bonus += 0.1
        
        # Calculate final deal score (0-100 scale)
        # Scoring factors for determining excellent deals:
        # 1. Savings component (FMV vs Price) - 40% weight
        # 2. Grade quality (PSA/CGC/BGS grades) - 30% weight  
        # 3. Card popularity/rarity - 15% weight
        # 4. Price point (higher value cards) - 10% weight
        # 5. FMV reliability (source quality) - 5% weight
        
        # 1. Savings Component (0-40 points)
        if absolute_savings > 0:
            savings_score = min(savings_percentage * 0.8, 25) + min(absolute_savings / 3, 15)
        elif fmv > 0 and fmv >= current_price * 0.8:
            # Close to FMV - still valuable, but not a "deal"
            savings_score = 5  # Small bonus for fair pricing
        else:
            # No savings or FMV much lower - still premium card, base score
            savings_score = 2  # Minimal score for premium cards without savings
        
        # 2. Grade Component (0-30 points)
        # Convert grade bonus to score points
        # PSA 10 = 30 points, PSA 9 = 25 points, PSA 8 = 20 points
        # BGS 9.5 = 28 points, BGS 9 = 22 points
        # CGC 10 = 25 points, CGC 9 = 18 points
        try:
            if grader == 'PSA':
                grade_val = float(grade)
                if grade_val >= 10:
                    grade_score = 30
                elif grade_val >= 9:
                    grade_score = 25
                elif grade_val >= 8:
                    grade_score = 20
                elif grade_val >= 7:
                    grade_score = 15
                else:
                    grade_score = 10
            elif grader == 'BGS':
                grade_val = float(grade)
                if grade_val >= 9.5:
                    grade_score = 28
                elif grade_val >= 9.0:
                    grade_score = 22
                elif grade_val >= 8.5:
                    grade_score = 18
                else:
                    grade_score = 12
            elif grader == 'CGC':
                grade_val = float(grade)
                if grade_val >= 10:
                    grade_score = 25
                elif grade_val >= 9:
                    grade_score = 18
                elif grade_val >= 8:
                    grade_score = 15
                else:
                    grade_score = 10
            else:
                # Ungraded or other grader
                grade_score = 5
        except (ValueError, TypeError):
            grade_score = 5
        
        # 3. Popularity Component (0-15 points)
        # Count how many high-demand keywords are present
        keyword_count = 0
        for keyword in high_demand_keywords:
            if keyword in card_name or keyword in pokemon_name:
                keyword_count += 1
        
        # Score based on keyword count: more keywords = higher score
        if keyword_count >= 3:
            popularity_score = 15  # Maximum for highly popular cards
        elif keyword_count == 2:
            popularity_score = 10
        elif keyword_count == 1:
            popularity_score = 5
        else:
            popularity_score = 0
        
        # 4. Price Point Component (0-10 points)
        # Higher value cards get more points (capped at $200+)
        if current_price >= 200:
            price_score = 10
        elif current_price >= 100:
            price_score = 7
        elif current_price >= 50:
            price_score = 5
        else:
            price_score = 0
        
        # 5. FMV Source Reliability (0-5 points)
        fmv_source_score = 0
        if fmv_source in ['alt', 'alt_verified', 'similar_cards']:
            fmv_source_score = 5
        elif fmv_source in ['alt_only_high_grade']:
            fmv_source_score = 4
        elif fmv_source:
            fmv_source_score = 2
        
        # Total deal score
        deal_score = savings_score + grade_score + popularity_score + price_score + fmv_source_score
        
        # For premium cards, minimum base score if it's a high-grade popular card
        if is_premium_card and grade_score >= 20 and popularity_score >= 10:
            deal_score = max(deal_score, 30)  # Ensure high-grade popular cards score well
        
        # Tiering based on comprehensive deal score
        # CRAZY DEAL: Score >= 50 (outstanding deals with high savings + quality)
        # EXCELLENT DEAL: Score >= 35 (great deals with good savings + quality)
        # GOOD DEAL: Score >= 25 (decent deals with some savings + quality)
        # FAIR DEAL: Score >= 15 (premium cards without significant savings)
        # No Deal: Score < 15
        
        if is_premium_card:
            # Premium card tiering based on score
            if deal_score >= 50 or (savings_percentage >= 15 and absolute_savings >= 25):
                deal_tier = "CRAZY DEAL"
            elif deal_score >= 35 or (savings_percentage >= 10 and absolute_savings >= 15):
                deal_tier = "EXCELLENT DEAL"
            elif deal_score >= 25 or (savings_percentage >= 5 and absolute_savings >= 10):
                deal_tier = "GOOD DEAL"
            elif deal_score >= 15:
                deal_tier = "FAIR DEAL"
            else:
                deal_tier = "No Deal"
        else:
            # Regular tiering for cards < $50
            if savings_percentage >= 20 or absolute_savings >= 40:
                deal_tier = "CRAZY DEAL"
            elif savings_percentage >= 15 or absolute_savings >= 25:
                deal_tier = "EXCELLENT DEAL"
            elif savings_percentage >= 10 or absolute_savings >= 15:
                deal_tier = "GOOD DEAL"
            else:
                deal_tier = "FAIR DEAL"
        
        return {
            'deal_score': round(deal_score, 2),
            'deal_tier': deal_tier,
            'absolute_savings': absolute_savings,
            'savings_percentage': savings_percentage,
            'savings_score': round(savings_score, 2),
            'grade_score': round(grade_score, 2),
            'popularity_score': round(popularity_score, 2),
            'price_score': round(price_score, 2),
            'fmv_source_score': round(fmv_source_score, 2),
            'momentum_bonus': momentum_bonus
        }
    
    def find_crazy_deals(self) -> List[Dict]:
        """Find the best deals using comprehensive scoring - only cards above $50"""
        crazy_deals = []
        
        for card in self.cards:
            # Filter: Only include cards with value (current price or FMV) above $50
            current_price = card.get('current_price_value')
            if current_price is None:
                current_price = self.parse_price(card.get('current_price', '0'))
            
            fmv = card.get('fmv_value')
            if fmv is None:
                fmv = self.parse_price(card.get('fmv', '0'))
            
            # Filter: Only include cards with current price >= $50
            # This ensures we're showing premium-priced cards, focusing on valuable listings
            # Cards priced below $50 are not considered premium enough for these deal sections
            if current_price < 50:
                continue
            
            deal_analysis = self.calculate_deal_score(card)
            
            if deal_analysis['deal_score'] > 0:
                # Add deal analysis to card data
                card_with_deal = card.copy()
                card_with_deal.update(deal_analysis)
                
                # Add additional intelligence
                card_with_deal['upside_potential'] = deal_analysis['absolute_savings']
                card_with_deal['market_momentum'] = "HIGH" if deal_analysis['deal_score'] >= 60 else "MEDIUM" if deal_analysis['deal_score'] >= 40 else "LOW"
                
                crazy_deals.append(card_with_deal)
        
        # Sort by deal score (highest first)
        deduped_deals = self.dedupe_deals(crazy_deals)
        return sorted(deduped_deals, key=lambda x: x['deal_score'], reverse=True)
    
    def get_deals_by_tier(self) -> Dict[str, List[Dict]]:
        """Organize deals by price tiers with intelligence scoring"""
        price_tiers = [
            (300, float('inf'), "Premium Deals ($300+)"),
            (200, 300, "High-Value Deals ($200-$300)"),
            (100, 200, "Mid-Range Deals ($100-$200)"),
            (50, 100, "Budget Deals ($50-$100)"),
            (25, 50, "Affordable Deals ($25-$50)"),
            (10, 25, "Budget-Friendly Deals ($10-$25)"),
            (0, 10, "Entry-Level Deals (Under $10)")
        ]
        
        tiered_deals = {}
        all_deals = self.find_crazy_deals()
        
        for min_price, max_price, tier_name in price_tiers:
            tier_deals = [
                deal for deal in all_deals 
                if min_price <= self.parse_price(deal.get('current_price', '0')) <= max_price
            ]
            tiered_deals[tier_name] = tier_deals
        
        return tiered_deals
    
    def generate_intelligence_report(self) -> Dict[str, Any]:
        """Generate comprehensive intelligence report"""
        all_deals = self.find_crazy_deals()
        tiered_deals = self.get_deals_by_tier()
        
        # Count deals by tier
        tier_counts = {tier: len(deals) for tier, deals in tiered_deals.items()}
        
        # Find top deals based on actual tier classification
        # Sort all deals by score first (they're already sorted, but ensure it)
        all_deals_sorted = sorted(all_deals, key=lambda x: x['deal_score'], reverse=True)
        
        # Ensure all deals are above $50 (extra safety filter)
        def is_price_above_50(deal):
            price = self.parse_price(deal.get('current_price', '0'))
            return price >= 50
        
        # Filter all deals to ensure price >= $50
        all_deals_sorted = [deal for deal in all_deals_sorted if is_price_above_50(deal)]
        
        # Get deals by tier (already classified in calculate_deal_score)
        # Ensure all deals shown are above $50
        top_crazy_deals = [deal for deal in all_deals_sorted if deal['deal_tier'] == 'CRAZY DEAL' and is_price_above_50(deal)][:10]
        top_excellent_deals = [deal for deal in all_deals_sorted if deal['deal_tier'] == 'EXCELLENT DEAL' and is_price_above_50(deal)][:10]
        
        # If not enough CRAZY DEALS, promote top EXCELLENT DEALS (still filtering for >= $50)
        if len(top_crazy_deals) < 5 and len(top_excellent_deals) > 0:
            needed = 5 - len(top_crazy_deals)
            promoted = [deal for deal in top_excellent_deals[:needed] if is_price_above_50(deal)]
            top_crazy_deals.extend(promoted)
            # Update tiers for promoted deals
            for deal in promoted:
                deal['deal_tier'] = 'CRAZY DEAL'
            top_excellent_deals = [deal for deal in top_excellent_deals if deal not in promoted]
        
        # If not enough EXCELLENT DEALS, promote top GOOD DEALS (still filtering for >= $50)
        if len(top_excellent_deals) < 10:
            good_deals = [deal for deal in all_deals_sorted if deal['deal_tier'] == 'GOOD DEAL' and is_price_above_50(deal)]
            needed = 10 - len(top_excellent_deals)
            promoted = good_deals[:needed]
            top_excellent_deals.extend(promoted)
            # Update tiers for promoted deals
            for deal in promoted:
                deal['deal_tier'] = 'EXCELLENT DEAL'
        
        # Final filter: Ensure all deals in report are above $50
        def final_price_filter(deal):
            price = self.parse_price(deal.get('current_price', '0'))
            return price >= 50
        
        top_crazy_deals = [deal for deal in top_crazy_deals if final_price_filter(deal)]
        top_excellent_deals = [deal for deal in top_excellent_deals if final_price_filter(deal)]
        all_deals_filtered = [deal for deal in all_deals[:50] if final_price_filter(deal)]
        
        # Filter tiered deals to only include deals >= $50
        tiered_deals_filtered = {}
        for tier_name, tier_deals in tiered_deals.items():
            tiered_deals_filtered[tier_name] = [deal for deal in tier_deals if final_price_filter(deal)]
        
        report = {
            'summary': {
                'total_cards_analyzed': len(self.cards),
                'total_deals_found': len([d for d in all_deals if final_price_filter(d)]),
                'crazy_deals': len(top_crazy_deals),
                'excellent_deals': len(top_excellent_deals),
                'tier_counts': {tier: len(deals) for tier, deals in tiered_deals_filtered.items()},
                'last_updated': datetime.now().isoformat(),
                'min_price_filter': '$50.00'
            },
            'top_crazy_deals': self.dedupe_deals(top_crazy_deals),
            'top_excellent_deals': self.dedupe_deals(top_excellent_deals),
            'tiered_deals': tiered_deals_filtered,
            'all_deals': all_deals_filtered  # Top 50 deals, all above $50
        }
        
        return report
    
    def save_intelligence_data(self, output_file: str = 'deal_intelligence.json'):
        """Save intelligence data to JSON file"""
        report = self.generate_intelligence_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Deal intelligence saved to {output_file}")
        return report

    def dedupe_deals(self, deals: List[Dict]) -> List[Dict]:
        """Remove duplicate deals that refer to the same listing and pricing"""
        unique_deals: List[Dict] = []
        seen = set()

        for deal in deals:
            normalized_name = self.normalize_name(deal.get('full_listing_name') or deal.get('pokemon_name') or '')
            grader = str(deal.get('grader', '')).upper().strip()
            grade = str(deal.get('grade', '')).strip()
            current_price = self.parse_price(deal.get('current_price'))
            fmv = self.parse_price(deal.get('fmv'))
            deal_tier = deal.get('deal_tier', '')

            dedupe_key = (
                normalized_name,
                grader,
                grade,
                round(current_price, 2),
                round(fmv, 2),
                deal_tier
            )

            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            unique_deals.append(deal)

        return unique_deals

def main():
    """Main function to run deal intelligence system"""
    print("=" * 60)
    print("  DEAL INTELLIGENCE SYSTEM")
    print("=" * 60)
    print("Analyzing Phygitals listings for CRAZY DEALS...")
    
    intelligence = DealIntelligenceSystem()
    
    if not intelligence.cards:
        print("No data found. Please ensure phygitals_marketplace_complete.json exists.")
        return
    
    print(f"Analyzing {len(intelligence.cards)} cards...")
    
    # Generate intelligence report
    report = intelligence.save_intelligence_data()
    
    # Display summary
    print("\nINTELLIGENCE SUMMARY")
    print("=" * 30)
    print(f"Total Cards Analyzed: {report['summary']['total_cards_analyzed']}")
    print(f"Total Deals Found: {report['summary']['total_deals_found']}")
    print(f"CRAZY DEALS: {report['summary']['crazy_deals']}")
    print(f"EXCELLENT DEALS: {report['summary']['excellent_deals']}")
    
    print("\nDEALS BY PRICE TIER")
    print("=" * 25)
    for tier, count in report['summary']['tier_counts'].items():
        print(f"{tier}: {count} deals")
    
    print("\nTOP CRAZY DEALS")
    print("=" * 20)
    for i, deal in enumerate(report['top_crazy_deals'][:5], 1):
        print(f"{i}. {deal.get('pokemon_name', 'Unknown')} - {deal['deal_tier']}")
        print(f"   Score: {deal['deal_score']} | Price: ${deal['current_price']} | FMV: ${deal['fmv']}")
        print(f"   Upside: ${deal['upside_potential']:.2f} ({deal['savings_percentage']:.1f}%)")
        print()
    
    print("Deal intelligence complete! Check 'deal_intelligence.json' for detailed results.")

if __name__ == "__main__":
    main()
