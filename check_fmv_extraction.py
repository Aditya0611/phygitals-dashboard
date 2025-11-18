#!/usr/bin/env python3
"""Check if FMV is being extracted"""
import json
import glob
import re

# Find latest progress file
files = glob.glob('marketplace_url_progress_page*.json')
if not files:
    print("No progress files found!")
    exit(1)

latest = max(files, key=lambda x: int(re.search(r'page(\d+)', x).group(1)) if re.search(r'page(\d+)', x) else 0)
print(f"Checking: {latest}")

with open(latest, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\nTotal cards: {len(data)}")

# Check FMV extraction
fmv_stats = {
    'with_fmv': 0,
    'fmv_alt': 0,
    'fmv_na': 0,
    'no_fmv_field': 0
}

for card in data:
    fmv = card.get('fmv', '')
    fmv_source = card.get('fmv_source', '')
    
    if fmv and fmv != 'N/A':
        fmv_stats['with_fmv'] += 1
        if fmv_source == 'alt':
            fmv_stats['fmv_alt'] += 1
    elif fmv == 'N/A':
        fmv_stats['fmv_na'] += 1
    else:
        fmv_stats['no_fmv_field'] += 1

print("\n" + "=" * 70)
print("FMV EXTRACTION STATUS")
print("=" * 70)
print(f"✅ Cards with FMV: {fmv_stats['with_fmv']} ({fmv_stats['with_fmv']/len(data)*100:.1f}%)")
print(f"   - FMV from ALT: {fmv_stats['fmv_alt']}")
print(f"⚠️  Cards with FMV = 'N/A': {fmv_stats['fmv_na']} ({fmv_stats['fmv_na']/len(data)*100:.1f}%)")
print(f"❌ Cards without FMV field: {fmv_stats['no_fmv_field']}")

# Show sample cards
print("\n" + "=" * 70)
print("SAMPLE CARDS (first 5)")
print("=" * 70)
for i, card in enumerate(data[:5], 1):
    price = card.get('current_price', 'N/A')
    fmv = card.get('fmv', 'N/A')
    fmv_source = card.get('fmv_source', '')
    name = card.get('full_listing_name', 'Unknown')[:50]
    print(f"\n{i}. {name}")
    print(f"   Price: {price}")
    print(f"   FMV: {fmv} (source: {fmv_source})")

