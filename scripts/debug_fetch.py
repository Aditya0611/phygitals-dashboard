#!/usr/bin/env python3
import argparse
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def main(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    print("Status:", resp.status_code)
    print("\n--- Preview ---\n")
    print(resp.text[:2000])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch a URL with scraper headers and print the first 2KB.")
    parser.add_argument("url")
    args = parser.parse_args()
    main(args.url)

