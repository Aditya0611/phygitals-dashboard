#!/usr/bin/env python3
"""
Clear all dashboard data files
This will empty all JSON data files used by the dashboard
"""
import json
import os
import glob

print("=" * 70)
print("  CLEARING ALL DASHBOARD DATA")
print("=" * 70)

files_cleared = []
files_created = []

# 1. Clear main data file
main_data_file = 'phygitals_marketplace_complete.json'
if os.path.exists(main_data_file):
    with open(main_data_file, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2, ensure_ascii=False)
    files_cleared.append(main_data_file)
    print(f"✓ Cleared: {main_data_file}")
else:
    with open(main_data_file, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2, ensure_ascii=False)
    files_created.append(main_data_file)
    print(f"✓ Created empty: {main_data_file}")

# 2. Clear all progress files
progress_files = glob.glob('marketplace_url_progress_page*.json')
if progress_files:
    for file in progress_files:
        try:
            os.remove(file)
            files_cleared.append(file)
        except Exception as e:
            print(f"⚠️  Could not delete {file}: {e}")
    print(f"✓ Deleted {len(progress_files)} progress files")
else:
    print("✓ No progress files to delete")

# 3. Clear filtered data file
filtered_file = 'filtered_marketplace_data.json'
empty_filtered = {
    "summary": {
        "total_cards": 0,
        "deals_found": 0,
        "high_value_cards": 0,
        "psa_cards": 0,
        "affordable_psa_deals": 0,
        "price_range_10_plus": 0,
        "fmv_25_plus": 0,
        "top_pokemon": [],
        "price_tier_summary": {}
    },
    "deals": [],
    "high_value_cards": [],
    "affordable_psa_deals": [],
    "psa_deals_by_range": {},
    "all_price_tier_deals": {},
    "all_cards": [],
    "price_range_10_plus": [],
    "fmv_25_plus": [],
    "psa_cards_with_certificates": [],
    "alt_xyz_integration": {
        "total_investigated": 0,
        "potential_links": [],
        "fmv_sources": [],
        "integration_possibilities": []
    }
}

with open(filtered_file, 'w', encoding='utf-8') as f:
    json.dump(empty_filtered, f, indent=2, ensure_ascii=False)
files_cleared.append(filtered_file)
print(f"✓ Cleared: {filtered_file}")

# 4. Clear deal intelligence file
deal_intel_file = 'deal_intelligence.json'
empty_deal_intel = {
    "summary": {
        "total_cards_analyzed": 0,
        "total_deals_found": 0,
        "crazy_deals": 0,
        "excellent_deals": 0,
        "tier_counts": {},
        "last_updated": "",
        "min_price_filter": "$50.00"
    },
    "top_crazy_deals": [],
    "top_excellent_deals": [],
    "tiered_deals": {},
    "all_deals": []
}

with open(deal_intel_file, 'w', encoding='utf-8') as f:
    json.dump(empty_deal_intel, f, indent=2, ensure_ascii=False)
files_cleared.append(deal_intel_file)
print(f"✓ Cleared: {deal_intel_file}")

# 5. Clear PSA deals analysis file
psa_deals_file = 'psa_deals_analysis.json'
empty_psa_deals = {
    "affordable_deals": [],
    "premium_deals": [],
    "summary": {
        "total_psa_cards": 0,
        "psa_deals_found": 0,
        "affordable_count": 0,
        "premium_count": 0
    }
}

with open(psa_deals_file, 'w', encoding='utf-8') as f:
    json.dump(empty_psa_deals, f, indent=2, ensure_ascii=False)
files_cleared.append(psa_deals_file)
print(f"✓ Cleared: {psa_deals_file}")

# 6. Clear dashboard Alt.xyz data
alt_xyz_file = 'dashboard_alt_xyz_data.json'
empty_alt_xyz = {
    "summary": {
        "total_cards": 0,
        "cards_with_alt_data": 0
    },
    "cards": []
}

with open(alt_xyz_file, 'w', encoding='utf-8') as f:
    json.dump(empty_alt_xyz, f, indent=2, ensure_ascii=False)
files_cleared.append(alt_xyz_file)
print(f"✓ Cleared: {alt_xyz_file}")

print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)
print(f"✓ Files cleared: {len(files_cleared)}")
print(f"✓ Files created: {len(files_created)}")
print(f"✓ Progress files deleted: {len(progress_files)}")
print("\n✅ All dashboard data has been cleared!")
print("\nThe dashboard will now show:")
print("  - 0 cards")
print("  - Empty statistics")
print("  - No deals or filtered data")
print("\n💡 Refresh your browser to see the empty dashboard")
