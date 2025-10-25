#!/usr/bin/env python3
"""
Windows Service Wrapper for Background Scraper
Runs the scraper as a background service
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def run_background_scraper():
    """Run the background scraper as a subprocess"""
    print("Starting Background Scraper Service")
    print("=" * 50)
    print("This will run continuously in the background")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Run the background scraper
        process = subprocess.Popen([
            sys.executable, 'background_scraper.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"Background scraper started (PID: {process.pid})")
        print("Dashboard will update automatically with new data")
        print("Scraper runs every hour and saves data every 5 minutes")
        print("\nPress Ctrl+C to stop the service...")
        
        # Monitor the process
        while True:
            time.sleep(10)
            
            # Check if process is still running
            if process.poll() is not None:
                print("Background scraper stopped unexpectedly")
                stdout, stderr = process.communicate()
                if stderr:
                    print(f"Error: {stderr}")
                break
                
    except KeyboardInterrupt:
        print("\nStopping background scraper...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print("Background scraper stopped")
    except Exception as e:
        print(f"Error running background scraper: {e}")

if __name__ == "__main__":
    run_background_scraper()
