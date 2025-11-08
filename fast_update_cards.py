#!/usr/bin/env python3
"""
Fast marketplace card updater.

Replaces the Selenium-only crawl with an HTTP-first pipeline that:
 1. Fetches every card listing via requests in parallel.
 2. Falls back to Selenium only when HTML parsing fails or a listing needs JS.
 3. Updates `phygitals_marketplace_complete.json` in-place.

After this completes, run:
  python advanced_filter_system.py
  python deal_intelligence_system.py
to refresh dashboard data.
"""

import concurrent.futures
import json
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from update_cards_by_url import build_driver, refresh_listing  # Selenium fallback

DATA_FILE = Path("phygitals_marketplace_complete.json")
MAX_WORKERS = 8
REQUEST_TIMEOUT = 20
SLEEP_BETWEEN_REQUESTS = 0.15  # seconds

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def load_data() -> list[Dict[str, Any]]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_FILE}")
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: list[Dict[str, Any]]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


UNLISTED_REGEXES = [
    re.compile(r"current\s+price[^$]{0,40}(?:unlisted|not\s+for\s+sale|not\s+available|n/?a)", re.IGNORECASE),
    re.compile(r"price[:\s]*(?:unlisted|not\s+for\s+sale|not\s+available|n/?a)", re.IGNORECASE),
    re.compile(r"(?:unlisted|not\s+for\s+sale|not\s+available|n/?a).{0,40}(?:price|current\s+price)", re.IGNORECASE),
    re.compile(r"listingStatus\"\s*:\s*\"UNLISTED\"", re.IGNORECASE),
]


def is_unlisted(text: str) -> bool:
    lower = text.lower()
    return any(regex.search(lower) for regex in UNLISTED_REGEXES)


def extract_price_and_fmv(page_text: str, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (price, fmv, fmv_source) strings."""
    if is_unlisted(page_text):
        return "Unlisted", None, None

    price = None

    # Look for explicit "Current price: $xx.xx"
    match = re.search(r"current\s+price[:\s]*\$?([\d,]+\.?\d*)", page_text, re.IGNORECASE)
    if match:
        try:
            price_val = float(match.group(1).replace(",", ""))
            if 0.01 <= price_val <= 10000:
                price = f"${price_val:.2f}"
        except ValueError:
            pass

    if price is None:
        # Generic "Price: $xx.xx"
        match = re.search(r"(?:^|\n|>)\s*price[:\s]*\$?([\d,]+\.?\d*)", page_text, re.IGNORECASE)
        if match:
            try:
                price_val = float(match.group(1).replace(",", ""))
                if 0.01 <= price_val <= 10000:
                    price = f"${price_val:.2f}"
            except ValueError:
                pass

    if price is None:
        # Inspect DOM nodes that contain dollar amounts
        for elem in soup.find_all(string=re.compile(r"\$[\d,]+\.?\d{2}")):
            parent_text = elem.parent.get_text(separator=" ").lower() if elem.parent else ""
            if any(keyword in parent_text for keyword in ("current price", "price", "buy now", "add to cart")):
                match = re.search(r"\$([\d,]+\.?\d{2})", elem)
                if match:
                    try:
                        price_val = float(match.group(1).replace(",", ""))
                        if 0.01 <= price_val <= 10000:
                            price = f"${price_val:.2f}"
                            break
                    except ValueError:
                        continue

    # FMV from inline JSON
    fmv = None
    fmv_source = None
    json_match = re.search(r'"altFmv"\s*:\s*"([\d,]+\.?\d*)"', page_text)
    if json_match:
        try:
            fmv_val = float(json_match.group(1).replace(",", ""))
            if fmv_val > 0:
                fmv = f"${fmv_val:.2f}"
                fmv_source = "alt"
        except ValueError:
            pass

    if fmv is None:
        fmv_match = re.search(r"fmv\s+by[^$]{0,40}\$([\d,]+\.\d{2})", page_text, re.IGNORECASE)
        if fmv_match:
            try:
                fmv_val = float(fmv_match.group(1).replace(",", ""))
                if fmv_val > 0:
                    fmv = f"${fmv_val:.2f}"
                    fmv_source = "alt"
            except ValueError:
                pass

    return price, fmv, fmv_source


def fetch_card_http(card: Dict[str, Any]) -> Dict[str, Any]:
    """HTTP-only fetch. Returns details dict with potential updates."""
    url = card.get("listing_url")
    if not url:
        return {"status": "missing-url"}

    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        return {"status": "http-error", "error": str(exc)}

    status_code = response.status_code
    if status_code == 404:
        return {"status": "not-found"}

    if status_code >= 500:
        return {"status": "server-error", "code": status_code}

    if status_code >= 400:
        return {"status": "http-error", "code": status_code}

    page_text = response.text

    if is_unlisted(page_text):
        return {"status": "unlisted"}

    soup = BeautifulSoup(page_text, "html.parser")

    price, fmv, fmv_source = extract_price_and_fmv(page_text, soup)

    if price is None and fmv is None:
        return {"status": "needs-fallback"}  # HTML parsing failed; try Selenium

    updates: Dict[str, Any] = {"status": "ok"}

    if price:
        updates["current_price"] = price
    if fmv:
        updates["fmv"] = fmv
        if fmv_source:
            updates["fmv_source"] = fmv_source

    return updates


def process_card(index: int, card: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper for executor."""
    result = fetch_card_http(card)
    result["index"] = index
    return result


def main():
    data = load_data()
    print(f"Loaded {len(data):,} cards.")
    print(f"Using up to {MAX_WORKERS} HTTP workers with timeout={REQUEST_TIMEOUT}s.\n")

    start_time = time.time()
    fallback_indices: list[int] = []
    unlisted_indices: list[int] = []
    errors: list[Tuple[int, Dict[str, Any]]] = []
    updates_applied = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for idx, card in enumerate(data):
            futures.append(executor.submit(process_card, idx, card))
            time.sleep(SLEEP_BETWEEN_REQUESTS)

        processed = 0
        last_report = 0

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            idx = result["index"]
            card = data[idx]
            status = result.get("status")

            processed += 1
            if processed - last_report >= 50:
                last_report = processed
                print(f"Processed {processed:,}/{len(data):,} cards...")

            if status == "ok":
                updated_fields = []
                if "current_price" in result and result["current_price"] != card.get("current_price"):
                    card["current_price"] = result["current_price"]
                    updated_fields.append(f"price -> {result['current_price']}")
                if "fmv" in result and result["fmv"] != card.get("fmv"):
                    card["fmv"] = result["fmv"]
                    updated_fields.append(f"fmv -> {result['fmv']}")
                    if "fmv_source" in result:
                        card["fmv_source"] = result["fmv_source"]

                if updated_fields:
                    card["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    updates_applied += 1
                continue

            if status == "unlisted":
                card["current_price"] = "Unlisted"
                card["listing_status"] = "unavailable"
                card["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
                unlisted_indices.append(idx)
                continue

            if status == "not-found":
                card["current_price"] = "Unlisted"
                card["listing_status"] = "not-found"
                card["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
                unlisted_indices.append(idx)
                continue

            if status == "needs-fallback":
                fallback_indices.append(idx)
                continue

            errors.append((idx, result))

    duration = time.time() - start_time
    print(f"\nHTTP pass complete in {duration/60:.2f} minutes.")
    print(f"  Updates applied : {updates_applied}")
    print(f"  Marked unlisted : {len(unlisted_indices)}")
    print(f"  Pending fallback: {len(fallback_indices)}")
    if errors:
        print(f"  HTTP errors     : {len(errors)} (see logs)")

    # Selenium fallback for tricky listings
    if fallback_indices:
        print("\nStarting Selenium fallback for remaining listings...")
        driver = build_driver()
        try:
            for idx in fallback_indices:
                card = data[idx]
                try:
                    refresh_listing(driver, card)
                except Exception as exc:
                    print(f"  ❌ Fallback failed for {card.get('listing_url')}: {exc}")
        finally:
            driver.quit()

    save_data(data)
    print("\n✅ Data saved to phygitals_marketplace_complete.json")
    print("Run `python advanced_filter_system.py` and `python deal_intelligence_system.py` when ready.")


if __name__ == "__main__":
    main()

