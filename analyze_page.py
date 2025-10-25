from bs4 import BeautifulSoup

# Read the debug HTML
html = open('debug_cards_pokemon_1.html', encoding='utf-8').read()

print('='*70)
print('HTML ANALYSIS')
print('='*70)
print(f'File size: {len(html):,} bytes')

print('\nSearching for keywords...')
keywords = ['card', 'listing', 'marketplace', 'price', 'psa', 'grade', '/card/', 'href']
for kw in keywords:
    count = html.lower().count(kw.lower())
    print(f'  {kw}: {count} times')

soup = BeautifulSoup(html, 'html.parser')

# Find all links
all_links = soup.find_all('a', href=True)
print(f'\nTotal links found: {len(all_links)}')

print('\nAll link hrefs:')
for i, a in enumerate(all_links[:20], 1):
    href = a.get('href')
    text = a.get_text(strip=True)[:50]
    try:
        print(f'  {i}. {href} - "{text}"')
    except:
        print(f'  {i}. {href}')

# Look for Next.js data
print('\nLooking for Next.js data/scripts...')
scripts = soup.find_all('script')
print(f'Found {len(scripts)} script tags')

# Check for __NEXT_DATA__
for script in scripts:
    if '__NEXT_DATA__' in str(script):
        print('\nFound __NEXT_DATA__! (JSON data embedded in page)')
        script_text = script.get_text()
        
        # Try to extract and parse JSON
        import json
        import re
        match = re.search(r'__NEXT_DATA__"\s*type="application/json">(.+?)</script>', html, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(1))
                print('Successfully parsed JSON data!')
                print(f'Keys: {list(json_data.keys())}')
                
                # Save to file for inspection
                with open('next_data.json', 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2)
                print('Saved to: next_data.json')
            except Exception as e:
                print(f'Error parsing JSON: {e}')
        break

# Look for price elements
print('\nLooking for price-related elements...')
price_pattern = r'\$[\d,]+\.?\d*'
import re
prices = re.findall(price_pattern, html)
print(f'Found {len(prices)} potential prices: {prices[:10]}')

