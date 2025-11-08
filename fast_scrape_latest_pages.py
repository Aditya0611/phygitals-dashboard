#!/usr/bin/env python3
"""
Fast scraper for marketplace pages.

Fetches one or more marketplace pages using HTTP requests (no Selenium) and
scrapes the listings concurrently. Outputs a JSON file containing the combined
card data so it can be merged into the main dataset or inspected separately.

Usage:
  python fast_scrape_latest_pages.py --start-page 1 --pages 5 --output latest_pages.json
"""

import argparse
import concurrent.futures
import json
import re
import time
from pathlib import Path
from typing import Iterable, List, Dict, Any

import requests
from bs4 import BeautifulSoup

from fast_update_cards import (
    HEADERS,
    REQUEST_TIMEOUT,
    extract_price_and_fmv,
    is_unlisted,
)

MARKETPLACE_URL = "https://www.phygitals.com/marketplace"
DEFAULT_OUTPUT = "latest_marketplace_pages.json"
CARD_URL_PATTERN = re.compile(r"https://www\.phygitals\.com/card/[A-Za-z0-9\-_]+")


def fetch_marketplace_page(page: int) -> str:
    params = {"page": page}
    response = requests.get(MARKETPLACE_URL, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def extract_card_urls(page_html: str) -> List[str]:
    urls = set(CARD_URL_PATTERN.findall(page_html))
    return sorted(urls)


def scrape_card(url: str) -> Dict[str, Any]:
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    status = response.status_code
    entry: Dict[str, Any] = {
        "listing_url": url,
        "current_price": "Unlisted",
        "fmv": "N/A",
        "fmv_source": "",
        "last_updated": None,
    }

    if status == 404:
        entry["listing_status"] = "not-found"
        return entry

    if status >= 500:
        entry["listing_status"] = f"server-{status}"
        return entry

    if status >= 400:
        entry["listing_status"] = f"http-{status}"
        return entry

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    entry["full_listing_name"] = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

    if is_unlisted(html):
        entry["listing_status"] = "unlisted"
        return entry

    price, fmv, fmv_source = extract_price_and_fmv(html, soup)
    if price:
        entry["current_price"] = price
    if fmv:
        entry["fmv"] = fmv
        entry["fmv_source"] = fmv_source or ""
    entry["listing_status"] = "active"
    entry["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return entry


def scrape_pages(start_page: int, pages: int, max_workers: int) -> List[Dict[str, Any]]:
    all_urls: List[str] = []

    for page in range(start_page, start_page + pages):
        print(f"Fetching page {page}...")
        try:
            html = fetch_marketplace_page(page)
        except Exception as exc:
            print(f"  ❌ Failed to fetch marketplace page {page}: {exc}")
            continue
        urls = extract_card_urls(html)
        print(f"  Found {len(urls)} card URLs on page {page}.")
        all_urls.extend(urls)

    print(f"\nTotal card URLs gathered: {len(all_urls)}")
    if not all_urls:
        return []

    results: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_card, url): url for url in all_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                card_data = future.result()
            except Exception as exc:
                print(f"  ❌ Error scraping {url}: {exc}")
                continue
            results.append(card_data)

    return results


def main():
    parser = argparse.ArgumentParser(description="Scrape marketplace pages quickly without Selenium.")
    parser.add_argument("--start-page", type=int, default=1, help="Marketplace page to start from (default: 1).")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to scrape (default: 1).")
    parser.add_argument("--workers", type=int, default=8, help="Max concurrent card fetches (default: 8).")
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_OUTPUT), help="Output JSON file path.")
    args = parser.parse_args()

    start = time.time()
    cards = scrape_pages(args.start_page, args.pages, args.workers)
    duration = time.time() - start

    if not cards:
        print("No cards scraped.")
        return

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(cards)} cards to {args.output} in {duration/60:.2f} minutes.")


if __name__ == "__main__":
    main()

