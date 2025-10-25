#!/usr/bin/env python3
"""
Monitor Background Scraper Progress
Shows real-time progress of the background scraper
"""

import time
import json
import os
from datetime import datetime

def monitor_scraper():
    """Monitor the background scraper progress"""
    print("Monitoring Background Scraper Progress")
    print("=" * 50)
    print("Press Ctrl+C to stop monitoring")
    print("=" * 50)
    
    last_count = 0
    start_time = datetime.now()
    
    try:
        while True:
            # Check if data file exists and get stats
            data_file = 'phygitals_marketplace_complete.json'
            if os.path.exists(data_file):
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    current_count = len(data)
                    mod_time = os.path.getmtime(data_file)
                    mod_datetime = datetime.fromtimestamp(mod_time)
                    
                    # Calculate progress
                    time_elapsed = datetime.now() - start_time
                    new_cards = current_count - last_count
                    
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Status Update:")
                    print(f"  Total Cards: {current_count}")
                    print(f"  Last Updated: {mod_datetime.strftime('%H:%M:%S')}")
                    print(f"  New Cards: +{new_cards}")
                    print(f"  Time Elapsed: {time_elapsed}")
                    
                    last_count = current_count
                    
                except Exception as e:
                    print(f"Error reading data: {e}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for data file...")
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

if __name__ == "__main__":
    monitor_scraper()
