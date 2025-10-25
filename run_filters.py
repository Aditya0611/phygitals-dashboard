#!/usr/bin/env python3
"""
Run Advanced Filtering System
Automatically runs the filtering system and updates the dashboard
"""

import subprocess
import sys
import os
from datetime import datetime

def run_filtering_system():
    """Run the advanced filtering system"""
    print("🚀 Running Advanced Filtering System")
    print("=" * 50)
    
    try:
        # Run the filtering system
        result = subprocess.run([
            sys.executable, 'advanced_filter_system.py'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ Filtering system completed successfully!")
            print("\n📊 Results Summary:")
            print(result.stdout)
            
            # Check if filtered data was created
            if os.path.exists('filtered_marketplace_data.json'):
                print("\n✅ Filtered data saved to 'filtered_marketplace_data.json'")
                print("🔄 Dashboard will now show advanced filtering options")
            else:
                print("❌ Filtered data file not found")
                
        else:
            print("❌ Filtering system failed:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running filtering system: {e}")

def main():
    """Main function"""
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if main data file exists
    if not os.path.exists('phygitals_marketplace_complete.json'):
        print("❌ Main data file not found. Please run the scraper first.")
        return
    
    # Run the filtering system
    run_filtering_system()
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 Next steps:")
    print("1. Refresh your dashboard at http://localhost:3001")
    print("2. Use the Advanced Filters section to explore deals")
    print("3. Filter by FMV > Price, High Value cards, or PSA cards")

if __name__ == "__main__":
    main()
