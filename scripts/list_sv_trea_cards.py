#!/usr/bin/env python3
import json
import argparse
from pathlib import Path


def main(prefix: str, data_file: Path):
    if not data_file.exists():
        print(f"Data file not found: {data_file}")
        return

    with data_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    matches = [
        card for card in data
        if card.get("listing_url", "").startswith(prefix)
    ]

    if not matches:
        print(f"No listings found with prefix: {prefix}")
        return

    print(f"Found {len(matches)} matching listings:\n")
    for card in matches:
        print(f"Listing URL : {card.get('listing_url')}")
        print(f"  Name       : {card.get('full_listing_name')}")
        print(f"  Price      : {card.get('current_price')}")
        print(f"  FMV        : {card.get('fmv')}")
        print(f"  FMV Source : {card.get('fmv_source')}")
        print(f"  Last Update: {card.get('last_updated')}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="List cards whose URLs start with the provided prefix."
    )
    parser.add_argument(
        "prefix",
        help="URL prefix to match (e.g. https://www.phygitals.com/card/2023-pokemon-japanese-sv-trea)",
    )
    parser.add_argument(
        "--data-file",
        default="phygitals_marketplace_complete.json",
        help="Path to the marketplace data file (default: phygitals_marketplace_complete.json)",
    )
    args = parser.parse_args()

    main(args.prefix, Path(args.data_file))

