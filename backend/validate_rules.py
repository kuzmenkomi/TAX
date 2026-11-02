"""Final validation: all countries 2026 + two-layer architecture test"""
import sys
sys.path.insert(0, ".")

from app.countries import CountryRegistry
from app.countries.base.tax_rule_engine import TaxRuleEngine

print("=== RULE VERSIONS (all must be 2026) ===")
versions = TaxRuleEngine.list_rule_versions()
all_ok = True
for code, year in sorted(versions.items()):
    ok = year == "2026"
    if not ok:
        all_ok = False
    print(f"  {code}: {year}  {'OK' if ok else 'WRONG !!!'}")

print()
if all_ok:
    print("ALL COUNTRIES ARE AT 2026 RULES")
else:
    print("SOME COUNTRIES ARE NOT 2026 - CHECK ABOVE")

print()
print("=== TWO-LAYER TEST: US data_year=2024, rules_version=2026 ===")
r = TaxRuleEngine.apply(
    country_code="US",
    tax_year=2024,
    capital_gains=30000,
    staking_income=5000,
    holding_period_days=400,
)
print("  data year  :", r["tax_year"])
print("  rules year :", r["rules_version"])
print("  country    :", r["country_name"])
print("  OK         :", r["tax_year"] == 2024 and r["rules_version"] == "2026")

print()
print("=== TWO-LAYER TEST: BR data_year=2023, rules_version=2026 ===")
r2 = TaxRuleEngine.apply(
    country_code="BR",
    tax_year=2023,
    capital_gains=50000,
    gross_income=80000,
)
print("  data year  :", r2["tax_year"])
print("  rules year :", r2["rules_version"])
print("  currency   :", r2["currency"])
print("  OK         :", r2["tax_year"] == 2023 and r2["rules_version"] == "2026")

print()
print("=== ALL REGISTERED COUNTRIES ===")
print(" ", CountryRegistry.list_codes())
print()
print("TOTAL:", len(CountryRegistry.list_codes()), "countries")
