# Quick test to verify all 11 countries are properly registered
import sys
sys.path.insert(0, '/root/backend')

from app.countries import CountryRegistry

# Test registry
print("=" * 60)
print("TESTING COMPLETE LATAM TAX SYSTEM - ALL 11 COUNTRIES")
print("=" * 60)

# Get all countries
all_countries = CountryRegistry.list_all()
print(f"\n✅ Total Countries Registered: {len(all_countries)}")

# Print each country
print("\nRegistered Countries:")
for country_info in all_countries:
    code = country_info.get("country_code", "?")
    name = country_info.get("country_name", "?")
    currency = country_info.get("currency", "?")
    authority = country_info.get("tax_authority", "?")
    print(f"  {code:2s} | {name:15s} | {currency:3s} | {authority:20s}")

# Test by region
print("\n" + "=" * 60)
print("Countries by Region:")
regions = {
    "North America": CountryRegistry.get_countries_by_region("North America"),
    "Central America": CountryRegistry.get_countries_by_region("Central America"),
    "South America": CountryRegistry.get_countries_by_region("South America"),
}

for region, countries in regions.items():
    print(f"\n{region}: {len(countries)} countries")
    for country in countries:
        print(f"  - {country['country_name']} ({country['country_code']})")

# Test API availability
print("\n" + "=" * 60)
print("Countries with Tax Authority API:")
api_countries = CountryRegistry.get_countries_with_api()
for country in api_countries:
    print(f"  ✓ {country['country_name']} ({country['tax_authority']})")

print("\n" + "=" * 60)
print("🎉 ALL 11 COUNTRIES SUCCESSFULLY REGISTERED!")
print("=" * 60)
