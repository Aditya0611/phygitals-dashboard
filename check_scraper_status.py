#!/usr/bin/env python3
"""
Check Background Scraper Status
Shows current status of the background scraper
"""

import json
import os
from datetime import datetime

def check_scraper_status():
    """Check the current status of the scraper"""
    print("🔍 Phygitals Scraper Status Check")
    print("=" * 50)
    
    # Check if data file exists
    data_file = 'phygitals_marketplace_complete.json'
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get file modification time
            mod_time = os.path.getmtime(data_file)
            mod_datetime = datetime.fromtimestamp(mod_time)
            
            # Calculate time since last update
            now = datetime.now()
            time_diff = now - mod_datetime
            hours_ago = time_diff.total_seconds() / 3600
            
            print(f"📊 Total Cards: {len(data)}")
            print(f"📅 Last Updated: {mod_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ Hours Ago: {hours_ago:.1f}")
            
            if hours_ago < 1:
                print("✅ Status: FRESH (Updated within last hour)")
            elif hours_ago < 6:
                print("⚠️  Status: RECENT (Updated within last 6 hours)")
            else:
                print("❌ Status: STALE (Data is old)")
            
            # Show sample data
            if data:
                print(f"\n📋 Sample Card:")
                sample = data[0]
                print(f"   Name: {sample.get('full_listing_name', 'N/A')}")
                print(f"   Grader: {sample.get('grader', 'N/A')}")
                print(f"   Grade: {sample.get('grade', 'N/A')}")
                print(f"   Price: {sample.get('price', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error reading data file: {e}")
    else:
        print("❌ No data file found")
        print("💡 Run the background scraper to start collecting data")
    
    print("\n" + "=" * 50)
    print("💡 To start background scraping:")
    print("   python run_background_scraper.py")
    print("   or double-click: start_background_scraper.bat")

if __name__ == "__main__":
    check_scraper_status()
