"""
Check scraping progress
Shows how many cards have been collected so far
"""
import json
import os
from datetime import datetime
import glob

def check_progress():
    print("\n" + "="*70)
    print("SCRAPING PROGRESS CHECKER")
    print("="*70)
    
    # Find all progress files
    progress_files = glob.glob("marketplace_url_progress_page*.json")
    
    if not progress_files:
        print("\n⏳ No progress files found yet.")
        print("   The scraper may still be starting up...")
        return
    
    # Sort by page number
    progress_files.sort(key=lambda x: int(x.split('page')[1].split('.')[0]))
    
    # Get latest progress file
    latest_file = progress_files[-1]
    page_num = int(latest_file.split('page')[1].split('.')[0])
    
    # Load data
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cards_so_far = len(data)
    total_pages = 1516
    total_cards_expected = 24254
    
    # Calculate progress
    progress_percent = (page_num / total_pages) * 100
    cards_per_page = cards_so_far / page_num
    estimated_total = int(cards_per_page * total_pages)
    
    # File info
    file_size = os.path.getsize(latest_file) / (1024 * 1024)  # MB
    file_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
    
    print(f"\n📊 CURRENT STATUS:")
    print(f"   Latest progress file: {latest_file}")
    print(f"   Last updated: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   File size: {file_size:.2f} MB")
    
    print(f"\n📈 PROGRESS:")
    print(f"   Pages completed: {page_num:,} / {total_pages:,} ({progress_percent:.1f}%)")
    print(f"   Cards collected: {cards_so_far:,}")
    print(f"   Estimated total: ~{estimated_total:,} cards")
    
    print(f"\n⏱️  TIMING:")
    pages_left = total_pages - page_num
    if page_num > 0:
        # Estimate completion time
        time_per_page = 3  # rough estimate in seconds
        minutes_left = (pages_left * time_per_page) / 60
        hours_left = minutes_left / 60
        print(f"   Estimated time remaining: {hours_left:.1f} hours ({minutes_left:.0f} minutes)")
    
    print(f"\n📁 ALL PROGRESS FILES:")
    for pf in progress_files[-5:]:  # Show last 5
        page = int(pf.split('page')[1].split('.')[0])
        size = os.path.getsize(pf) / 1024  # KB
        print(f"   - Page {page:4d}: {size:8.1f} KB")
    
    print("\n" + "="*70)
    print("Run this script again anytime to check progress!")
    print("="*70 + "\n")


if __name__ == "__main__":
    check_progress()

