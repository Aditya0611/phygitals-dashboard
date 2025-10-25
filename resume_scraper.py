"""
Resume the marketplace scraper from where it left off
Continues from page 35 (after the network error)
"""

from scraper_marketplace_url import URLMarketplaceScraper

def main():
    print("""
    ==============================================================
       RESUME Phygitals Marketplace Scraper
       Continuing from page 35 after network error
    ==============================================================
    """)
    
    print("\n📊 CURRENT STATUS:")
    print("   - 787 cards already collected (pages 1-33)")
    print("   - Network error occurred at page 34")
    print("   - Resuming from page 35")
    print("   - Remaining: 1,481 pages (~35,544 cards)")
    
    print("\n🚀 RESUMING SCRAPER...")
    print("   This will continue automatically")
    print("   Progress saves every 10 pages")
    print("   Press Ctrl+C to stop safely")
    
    print("\nStarting in 5 seconds...")
    import time
    time.sleep(5)
    
    # Resume from page 35
    scraper = URLMarketplaceScraper(start_page=35, max_pages=None)
    
    try:
        scraper.scrape_all_pages()
    except KeyboardInterrupt:
        print("\nStopped by user!")
    except Exception as e:
        print(f"\nError: {e}")
    
    scraper.save_final()
    print("\n✅ DONE!")


if __name__ == "__main__":
    main()
