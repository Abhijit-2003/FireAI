import json
with open(r'd:\FireAI\project_a\tests\test_cases.json') as f:
    cases = json.load(f)

# Spot check surcharge cases
for c in cases:
    if c['category'] == 'surcharge':
        o = c['expected_old_regime']
        n = c['expected_new_regime']
        tid = c['id']
        desc = c['description'][:55]
        print(f"{tid}: {desc}")
        print(f"  OLD: taxable={o['taxable_income']} tax={o['tax_before_rebate']} sc={o['surcharge']} cess={o['cess']} total={o['total_tax']}")
        print(f"  NEW: taxable={n['taxable_income']} tax={n['tax_before_rebate']} sc={n['surcharge']} cess={n['cess']} total={n['total_tax']}")

# Check rebate cliff
print("\n--- Rebate cliff checks ---")
for c in cases:
    if c['id'] in ['TC111','TC112','TC113','TC121','TC122','TC123']:
        o = c['expected_old_regime']
        n = c['expected_new_regime']
        print(f"{c['id']}: {c['description'][:55]}")
        print(f"  OLD: taxable={o['taxable_income']} rebate={o['rebate_87a']} total={o['total_tax']}")
        print(f"  NEW: taxable={n['taxable_income']} rebate={n['rebate_87a']} total={n['total_tax']}")

# File sizes
import os
for f in ['test_cases.json', 'official_verified.json']:
    sz = os.path.getsize(os.path.join(r'd:\FireAI\project_a\tests', f))
    print(f"\n{f}: {sz/1024:.1f} KB")

