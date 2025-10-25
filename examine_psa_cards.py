#!/usr/bin/env python3
"""
Examine PSA card data structure
"""

import json

def examine_psa_cards():
    # Load data
    with open('phygitals_marketplace_complete.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get PSA cards
    psa_cards = [card for card in data if card.get('grader') == 'PSA']
    
    print(f"Found {len(psa_cards)} PSA cards")
    print("\nSample PSA card names:")
    
    for i, card in enumerate(psa_cards[:10], 1):
        name = card.get('full_listing_name', '')
        print(f"{i}. {name}")
    
    print("\nSample PSA card data structure:")
    if psa_cards:
        sample_card = psa_cards[0]
        for key, value in sample_card.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    examine_psa_cards()
