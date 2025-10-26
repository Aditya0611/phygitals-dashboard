import time
import os
from datetime import datetime

def monitor_scraper():
    print("🔍 Background Scraper Monitor")
    print("=" * 50)
    print("Monitoring scraper progress...")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 50)
    
    last_count = 0
    last_update = None
    
    try:
        while True:
            # Check if data file exists
            if os.path.exists('phygitals_marketplace_complete.json'):
                # Get file modification time
                mtime = os.path.getmtime('phygitals_marketplace_complete.json')
                current_update = datetime.fromtimestamp(mtime)
                
                # Count cards (quick method)
                with open('phygitals_marketplace_complete.json', 'r', encoding='utf-8') as f:
                    content = f.read()
                    card_count = content.count('"listing_url"')
                
                # Show progress if changed
                if card_count != last_count or current_update != last_update:
                    print(f"\n📊 {datetime.now().strftime('%H:%M:%S')} - Cards: {card_count}")
                    print(f"📅 Last Update: {current_update.strftime('%H:%M:%S')}")
                    
                    if card_count > last_count:
                        print(f"✅ +{card_count - last_count} new cards found!")
                    
                    last_count = card_count
                    last_update = current_update
                else:
                    print(".", end="", flush=True)
            else:
                print("❌ No data file found")
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n📊 Final Status:")
        print(f"   Total Cards: {last_count}")
        print(f"   Last Update: {last_update.strftime('%H:%M:%S') if last_update else 'N/A'}")
        print("\n✅ Monitoring stopped")

if __name__ == "__main__":
    monitor_scraper()
