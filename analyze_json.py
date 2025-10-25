import json
import pprint

# Load the JSON data
with open('next_data.json', encoding='utf-8') as f:
    data = json.load(f)

print('='*70)
print('JSON DATA STRUCTURE ANALYSIS')
print('='*70)

# Check pageProps structure
page_props = data['props']['pageProps']
print(f'\nKeys in pageProps: {list(page_props.keys())}')

# Check if there are cards
if 'cards' in page_props:
    cards_data = page_props['cards']
    print(f'\nKeys in cards: {list(cards_data.keys())}')
    
    if 'cards' in cards_data:
        cards_list = cards_data['cards']
        print(f'Total cards: {len(cards_list)}')
        
        print('\n' + '='*70)
        print('FIRST CARD SAMPLE:')
        print('='*70)
        pprint.pprint(cards_list[0])

# Check for listings
if 'listings' in page_props:
    print('\n' + '='*70)
    print('FOUND LISTINGS!')
    print('='*70)
    listings = page_props['listings']
    print(f'Type: {type(listings)}')
    if isinstance(listings, list):
        print(f'Total listings: {len(listings)}')
        if listings:
            print('\nFirst listing:')
            pprint.pprint(listings[0])
    elif isinstance(listings, dict):
        print(f'Listings keys: {list(listings.keys())}')

# Search through all data
json_str = json.dumps(data, indent=2)

# Look for specific patterns
patterns = {
    'listing': json_str.lower().count('listing'),
    'price': json_str.lower().count('price'),
    'grader': json_str.lower().count('grader'),
    'psa': json_str.lower().count('psa'),
    'fmv': json_str.lower().count('fmv'),
    'grade': json_str.lower().count('grade'),
    '/card/': json_str.count('/card/'),
}

print('\n' + '='*70)
print('KEYWORD SEARCH IN JSON:')
print('='*70)
for keyword, count in patterns.items():
    print(f'{keyword}: {count} occurrences')

# Save full structure for inspection
with open('json_structure.txt', 'w', encoding='utf-8') as f:
    f.write('PAGE PROPS KEYS:\n')
    f.write(str(list(page_props.keys())))
    f.write('\n\n')
    
    for key in page_props.keys():
        f.write(f'\n\n{"="*70}\n')
        f.write(f'{key.upper()}:\n')
        f.write(f'{"="*70}\n')
        f.write(pprint.pformat(page_props[key][:5] if isinstance(page_props[key], list) else page_props[key]))

print('\nSaved full structure to: json_structure.txt')

