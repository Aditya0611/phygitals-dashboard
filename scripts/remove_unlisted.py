#!/usr/bin/env python3
"""
Remove unlisted/not-for-sale cards from the master dataset and rebuild the filtered data.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / 'phygitals_marketplace_complete.json'
FILTERED = ROOT / 'filtered_marketplace_data.json'


def parse_price(value: str) -> float:
    if not value:
        return 0.0
    return float(re.sub(r'[^\d.]', '', str(value)) or 0)


def is_listed(card: dict) -> bool:
    # Check URL blocklist first
    try:
        blocklist_path = ROOT / 'unlisted_blocklist.json'
        if blocklist_path.exists():
            blocked = set(json.loads(blocklist_path.read_text(encoding='utf-8')))
            url = str(card.get('listing_url') or card.get('card_url') or card.get('url') or card.get('link') or '')
            if url in blocked:
                return False
    except Exception:
        pass
    
    has_url = bool(card.get('listing_url') or card.get('card_url') or card.get('url') or card.get('link'))
    price_raw = str(card.get('current_price') or card.get('price') or '').strip()
    price_txt = price_raw.lower()
    price_val = parse_price(price_raw)
    
    # Check if price text explicitly says "Unlisted" or "Not For Sale"
    if 'unlisted' in price_txt or 'not for sale' in price_txt:
        return False
    
    status_fields = [card.get('status'), card.get('listing_status'), card.get('availability'), card.get('state')]
    status_joined = ' | '.join([str(s).lower() for s in status_fields if s])
    boolean_flags = [card.get('listed'), card.get('is_listed'), card.get('available'), card.get('isAvailable')]
    flagged_false = any(v is False for v in boolean_flags)
    unlisted = (
        'unlisted' in status_joined or 'not listed' in status_joined or 'delisted' in status_joined or
        'inactive' in status_joined or 'unavailable' in status_joined or 'sold' in status_joined or
        'out of stock' in status_joined or flagged_false
    )
    return has_url and price_val > 0 and not unlisted


def main():
    if not MAIN.exists():
        print('Main data file not found:', MAIN)
        return 1
    data = json.loads(MAIN.read_text(encoding='utf-8'))
    before = len(data)
    data = [c for c in data if is_listed(c)]
    after = len(data)
    MAIN.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Removed {before - after} unlisted cards. Kept {after}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


