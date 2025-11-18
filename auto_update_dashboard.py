import time
import os
import json
import shutil
import subprocess
import sys
from datetime import datetime

def get_latest_progress_file():
    """Finds the latest marketplace progress JSON file."""
    data_dir = os.getcwd()
    progress_files = [f for f in os.listdir(data_dir) 
                     if f.startswith('marketplace_url_progress_page') and f.endswith('.json')]
    
    if not progress_files:
        return None, None

    latest_file = None
    latest_mtime = 0

    for f_name in progress_files:
        f_path = os.path.join(data_dir, f_name)
        mtime = os.path.getmtime(f_path)
        if mtime > latest_mtime:
            latest_mtime = mtime
            latest_file = f_path
    
    return latest_file, datetime.fromtimestamp(latest_mtime)

def update_main_data_file(progress_file_path):
    """Merge-first update: run atomic merge + FMV update instead of raw copy."""
    try:
        # For logging visibility, still print which progress file triggered the run
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ▷ Triggered by {os.path.basename(progress_file_path)}")

        # Run the atomic pipeline which:
        # 1) merges all historical + current progress files
        # 2) recalculates/cleans FMV
        # 3) updates filters and deal intelligence
        result = subprocess.run([sys.executable, 'atomic_merge_and_update.py'], capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout.strip())
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Atomic merge + FMV update completed")
            return True
        else:
            # If atomic pipeline fails, fall back to raw copy so the dashboard still moves forward
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ Atomic merge failed, falling back to raw copy. Details: {result.stderr}")
            shutil.copy(progress_file_path, 'phygitals_marketplace_complete.json')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Copied {os.path.basename(progress_file_path)} to phygitals_marketplace_complete.json")
            return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Error during merge-first update: {e}")
        return False

def run_filtering_system():
    """Runs the advanced filtering system to update filtered_marketplace_data.json."""
    try:
        result = subprocess.run([sys.executable, 'run_filters.py'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Filtering system completed")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Filtering system failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Error running filtering system: {e}")
        return False

def generate_psa_analysis():
    """Generates PSA deals analysis."""
    try:
        # Load filtered data
        with open('filtered_marketplace_data.json', 'r', encoding='utf-8') as f:
            filtered_data = json.load(f)

        deals = filtered_data.get('deals', [])
        all_cards = filtered_data.get('all_cards', [])
        affordable_source = filtered_data.get('affordable_psa_deals', [])

        def parse_price(price_str):
            if not price_str or price_str == "N/A":
                return 0.0
            return float(price_str.replace('$', '').replace(',', ''))

        affordable_deals = []
        premium_deals = []

        # Prefer affordable deals directly from filtered data (already PSA + price range + FMV>Price)
        for deal in affordable_source:
            price = parse_price(deal.get('current_price', '0'))
            fmv = parse_price(deal.get('fmv', '0'))
            affordable_deals.append({
                'name': deal.get('full_listing_name', deal.get('pokemon_name', '')),
                'price': price,
                'fmv': fmv,
                'savings': (fmv - price) if fmv > 0 else 0,
                'savings_pct': ((fmv - price) / fmv * 100) if fmv > 0 else 0,
                'cert': deal.get('psa_certificate_number', deal.get('certificate_number', 'N/A')),
                'url': deal.get('listing_url', ''),
                'grade': deal.get('grade', ''),
                'pokemon_name': deal.get('pokemon_name', '')
            })

        # Build premium deals (PSA, $100-$300) from general deals list
        for deal in deals:
            grader = deal.get('grader', '').upper()
            price = parse_price(deal.get('current_price', '0'))
            fmv = parse_price(deal.get('fmv', '0'))
            
            if grader == 'PSA':
                savings = fmv - price if fmv > 0 else 0
                savings_pct = (savings / fmv * 100) if fmv > 0 else 0
                
                psa_deal = {
                    'name': deal.get('full_listing_name', ''),
                    'price': price,
                    'fmv': fmv,
                    'savings': savings,
                    'savings_pct': savings_pct,
                    'cert': deal.get('psa_certificate_number', 'N/A'),
                    'url': deal.get('listing_url', ''),
                    'grade': deal.get('grade', ''),
                    'pokemon_name': deal.get('pokemon_name', '')
                }
                
                if 100 <= price <= 300:
                    premium_deals.append(psa_deal)

        total_psa = len([c for c in all_cards if c.get('grader', '').upper() == 'PSA'])

        psa_data = {
            'affordable_deals': affordable_deals,
            'premium_deals': premium_deals,
            'all_psa_deals': affordable_deals + premium_deals,
            'summary': {
                'total_psa_cards': total_psa,
                'psa_deals_found': len(affordable_deals) + len(premium_deals),
                'affordable_count': len(affordable_deals),
                'premium_count': len(premium_deals)
            }
        }

        with open('psa_deals_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(psa_data, f, indent=2, ensure_ascii=False)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ PSA analysis updated ({len(affordable_deals)} affordable, {len(premium_deals)} premium)")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Error generating PSA analysis: {e}")
        return False

def generate_deal_intelligence():
    """Generates deal intelligence analysis."""
    try:
        result = subprocess.run([sys.executable, 'deal_intelligence_system.py'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Deal intelligence updated")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Deal intelligence failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Error running deal intelligence: {e}")
        return False

def main():
    print("=" * 60)
    print("  AUTO-UPDATE DASHBOARD MONITOR")
    print("=" * 60)
    print("Monitoring scraper progress and auto-updating dashboard...")
    print("Press Ctrl+C to stop\n")
    
    last_updated_progress_file = None
    
    try:
        while True:
            latest_file, latest_mtime = get_latest_progress_file()
            
            if latest_file and latest_file != last_updated_progress_file:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 New scraper progress detected!")
                print(f"    File: {os.path.basename(latest_file)}")
                print(f"    Modified: {latest_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if update_main_data_file(latest_file):
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Running filtering system...")
                    if run_filtering_system():
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Generating PSA analysis...")
                        if generate_psa_analysis():
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Generating deal intelligence...")
                            if generate_deal_intelligence():
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Dashboard updated!")
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] 💡 Refresh your browser at http://localhost:3002")
                                last_updated_progress_file = latest_file
            
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print("\n\n[STOPPED] Dashboard monitor stopped by user")
    except Exception as e:
        print(f"\n\n[ERROR] Monitor error: {e}")

if __name__ == "__main__":
    main()

