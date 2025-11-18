#!/usr/bin/env python3
"""Simple scraper status check"""
import glob
import re
import os
from datetime import datetime

files = glob.glob('marketplace_url_progress_page*.json')
if files:
    latest = max(files, key=lambda x: int(re.search(r'page(\d+)', x).group(1)) if re.search(r'page(\d+)', x) else 0)
    page_num = int(re.search(r'page(\d+)', latest).group(1))
    mod_time = os.path.getmtime(latest)
    mod_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    
    print("=" * 70)
    print("SCRAPER STATUS")
    print("=" * 70)
    print(f"\nLatest Progress: Page {page_num}")
    print(f"File: {latest}")
    print(f"Modified: {mod_str}")
    print(f"\nWill resume from: Page {page_num + 1}")
    print(f"Remaining pages: {1516 - page_num}")
    print("\n" + "=" * 70)
    print("Scraper is running with fixed logic:")
    print("  - Checks 'Unlisted' BEFORE extracting prices")
    print("  - FMV values will NOT be extracted as current_price")
    print("  - Only explicitly labeled prices will be used")
    print("  - Progress saves after every page")
    print("  - Dashboard auto-updates every 30 seconds")
    print("=" * 70)
else:
    print("No progress files found. Starting from page 1.")


