import pandas as pd
import json

# Load the data
df = pd.read_excel('phygitals_listings_150pokemon.xlsx')

print("\n" + "="*70)
print("MARKETPLACE DATA SUMMARY - First 150 Pokemon")
print("="*70)
print(f"Total listings collected: {len(df)}")
print(f"Total Pokemon covered: {df['pokemon_name'].nunique()}")
print(f"\nGenerations covered: {sorted(df['generation'].unique())}")
print(f"\nColumns in spreadsheet:")
for col in df.columns:
    print(f"  - {col}")

print("\n" + "="*70)
print("SAMPLE DATA (first 15 listings):")
print("="*70)
print(df[['pokemon_name', 'listing_name', 'listing_price', 'pokemon_url']].head(15).to_string(index=False))

print("\n" + "="*70)
print("TOP 10 POKEMON BY NUMBER OF LISTINGS:")
print("="*70)
top_pokemon = df['pokemon_name'].value_counts().head(10)
for pokemon, count in top_pokemon.items():
    print(f"  {pokemon}: {count} listings")

print("\n" + "="*70)
print("FILES CREATED:")
print("="*70)
print("  1. phygitals_listings_150pokemon.xlsx (Excel - MAIN FILE)")
print("  2. phygitals_listings_150pokemon.csv (CSV - Alternative)")
print("="*70)

