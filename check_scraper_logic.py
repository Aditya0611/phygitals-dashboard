#!/usr/bin/env python3
"""
Check scraper logic and data quality
"""
import json
import glob
import re
from collections import Counter

print("=" * 70)
print("  SCRAPER LOGIC CHECK")
print("=" * 70)

# Find latest progress file
files = glob.glob('marketplace_url_progress_page*.json')
if not files:
    print("❌ No progress files found!")
    exit(1)

latest_file = max(files, key=lambda x: int(re.search(r'page(\d+)', x).group(1)) if re.search(r'page(\d+)', x) else 0)
print(f"\n📁 Checking: {latest_file}")

# Load data
with open(latest_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"📊 Total cards in file: {len(data)}")

# Check price extraction logic
print("\n" + "=" * 70)
print("  PRICE EXTRACTION ANALYSIS")
print("=" * 70)

issues = []
price_fmv_ratios = []
cards_with_issues = []

for i, card in enumerate(data[:50]):  # Check first 50 cards
    price_str = card.get('current_price', '')
    fmv_str = card.get('fmv', 'N/A')
    
    # Extract numeric values
    price_val = 0.0
    fmv_val = 0.0
    
    if price_str and price_str != 'Unlisted':
        try:
            price_clean = re.sub(r'[^\d.]', '', str(price_str))
            price_val = float(price_clean) if price_clean else 0.0
        except:
            pass
    
    if fmv_str and fmv_str != 'N/A':
        try:
            fmv_clean = re.sub(r'[^\d.]', '', str(fmv_str))
            fmv_val = float(fmv_clean) if fmv_clean else 0.0
        except:
            pass
    
    # Check for suspicious patterns
    if price_val > 0 and fmv_val > 0:
        ratio = price_val / fmv_val if fmv_val > 0 else 0
        
        # Flag suspicious cases: price is way higher than FMV (likely extraction error)
        if ratio > 100:  # Price is 100x FMV - very suspicious
            issues.append({
                'index': i,
                'price': price_str,
                'fmv': fmv_str,
                'ratio': ratio,
                'card': card.get('full_listing_name', 'Unknown')[:60]
            })
            cards_with_issues.append(card)
        
        price_fmv_ratios.append(ratio)

# Statistics
print(f"\n✅ Cards analyzed: {len(data[:50])}")
print(f"⚠️  Potential issues found: {len(issues)}")

if issues:
    print("\n" + "=" * 70)
    print("  ⚠️  POTENTIAL EXTRACTION ISSUES")
    print("=" * 70)
    print("\nCards where Price >> FMV (possible extraction error):")
    print("\n{:<5} {:<20} {:<20} {:<10} {:<50}".format("#", "Price", "FMV", "Ratio", "Card Name"))
    print("-" * 105)
    
    for issue in issues[:10]:  # Show first 10
        print("{:<5} {:<20} {:<20} {:<10.1f} {:<50}".format(
            issue['index'] + 1,
            issue['price'],
            issue['fmv'],
            issue['ratio'],
            issue['card']
        ))

# Price filter check
print("\n" + "=" * 70)
print("  PRICE FILTER CHECK ($100+)")
print("=" * 70)

cards_below_100 = []
cards_above_100 = []

for card in data:
    price_str = card.get('current_price', '')
    if price_str and price_str != 'Unlisted':
        try:
            price_clean = re.sub(r'[^\d.]', '', str(price_str))
            price_val = float(price_clean) if price_clean else 0.0
            if price_val < 100:
                cards_below_100.append(card)
            else:
                cards_above_100.append(card)
        except:
            pass

print(f"\n✅ Cards with price >= $100: {len(cards_above_100)}")
print(f"⚠️  Cards with price < $100: {len(cards_below_100)}")

if cards_below_100:
    print("\n⚠️  WARNING: Found cards below $100 (should be filtered out):")
    for card in cards_below_100[:5]:
        print(f"  - {card.get('current_price', 'N/A')}: {card.get('full_listing_name', 'Unknown')[:60]}")

# FMV extraction check
print("\n" + "=" * 70)
print("  FMV EXTRACTION CHECK")
print("=" * 70)

fmv_sources = Counter([card.get('fmv_source', 'none') for card in data])
print(f"\nFMV Sources:")
for source, count in fmv_sources.items():
    print(f"  {source}: {count}")

fmv_na_count = sum(1 for card in data if card.get('fmv', 'N/A') == 'N/A')
print(f"\nCards with FMV = 'N/A': {fmv_na_count}")

# Summary
print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)

if issues:
    print(f"\n⚠️  ISSUES DETECTED:")
    print(f"   - {len(issues)} cards have suspicious price/FMV ratios")
    print(f"   - This suggests possible extraction errors")
    print(f"   - Price might be extracted correctly, but FMV might be wrong")
    print(f"   - OR vice versa - need to verify on actual pages")
else:
    print(f"\n✅ No major issues detected in price extraction")

if cards_below_100:
    print(f"\n⚠️  FILTER ISSUE:")
    print(f"   - {len(cards_below_100)} cards below $100 found")
    print(f"   - Price filter might not be working correctly")
    print(f"   - OR these cards were scraped before filter was added")
else:
    print(f"\n✅ Price filter working correctly (all cards >= $100)")

print("\n" + "=" * 70)

