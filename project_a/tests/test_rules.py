"""
Pytest test suite for Indian Income Tax Calculator FY 2024-25.

Loads test cases from test_cases.json and official_verified.json,
runs each through the RulesCalculator, and asserts rupee-exact matches
on taxable_income and total_tax for both old and new regimes.
"""

import json
import os
import pytest

# ============================================================
# Load test data
# ============================================================
TEST_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_json(filename):
    path = os.path.join(TEST_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

ALL_CASES = _load_json('test_cases.json')
OFFICIAL_CASES = _load_json('official_verified.json')

# Build category index
CASES_BY_CATEGORY = {}
for case in ALL_CASES:
    cat = case['category']
    CASES_BY_CATEGORY.setdefault(cat, []).append(case)

# ============================================================
# Import the calculator under test
# ============================================================
try:
    from project_a.impl_rules.calculator import RulesCalculator
    CALCULATOR_AVAILABLE = True
except ImportError:
    CALCULATOR_AVAILABLE = False


# ============================================================
# Helper to run a single case through the calculator
# ============================================================
def _run_calculator(case, regime):
    """Run a test case through the calculator and return results dict."""
    calc = RulesCalculator()
    inp = case['input']
    result = calc.compute(inp, regime=regime)
    return result


# ============================================================
# Parametrize helpers
# ============================================================
def _case_ids(cases):
    """Generate pytest IDs from test cases."""
    return [f"{c['id']}-{c['description'][:50]}" for c in cases]


# ============================================================
# TESTS: All cases - Old Regime
# ============================================================
@pytest.mark.skipif(not CALCULATOR_AVAILABLE,
                    reason="RulesCalculator not available")
@pytest.mark.parametrize("case", ALL_CASES, ids=_case_ids(ALL_CASES))
class TestOldRegimeAll:
    """Test old regime calculations for all 210 cases."""

    def test_taxable_income(self, case):
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']['taxable_income']
        assert result['taxable_income'] == expected, (
            f"[{case['id']}] Old regime taxable_income: "
            f"got {result['taxable_income']}, expected {expected}"
        )

    def test_total_tax(self, case):
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']['total_tax']
        assert result['total_tax'] == expected, (
            f"[{case['id']}] Old regime total_tax: "
            f"got {result['total_tax']}, expected {expected}"
        )

    def test_tax_before_rebate(self, case):
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']['tax_before_rebate']
        assert result['tax_before_rebate'] == expected, (
            f"[{case['id']}] Old regime tax_before_rebate: "
            f"got {result['tax_before_rebate']}, expected {expected}"
        )

    def test_rebate(self, case):
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']['rebate_87a']
        assert result['rebate_87a'] == expected, (
            f"[{case['id']}] Old regime rebate_87a: "
            f"got {result['rebate_87a']}, expected {expected}"
        )

    def test_surcharge(self, case):
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']['surcharge']
        assert result['surcharge'] == expected, (
            f"[{case['id']}] Old regime surcharge: "
            f"got {result['surcharge']}, expected {expected}"
        )

    def test_cess(self, case):
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']['cess']
        assert result['cess'] == expected, (
            f"[{case['id']}] Old regime cess: "
            f"got {result['cess']}, expected {expected}"
        )


# ============================================================
# TESTS: All cases - New Regime
# ============================================================
@pytest.mark.skipif(not CALCULATOR_AVAILABLE,
                    reason="RulesCalculator not available")
@pytest.mark.parametrize("case", ALL_CASES, ids=_case_ids(ALL_CASES))
class TestNewRegimeAll:
    """Test new regime calculations for all 210 cases."""

    def test_taxable_income(self, case):
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']['taxable_income']
        assert result['taxable_income'] == expected, (
            f"[{case['id']}] New regime taxable_income: "
            f"got {result['taxable_income']}, expected {expected}"
        )

    def test_total_tax(self, case):
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']['total_tax']
        assert result['total_tax'] == expected, (
            f"[{case['id']}] New regime total_tax: "
            f"got {result['total_tax']}, expected {expected}"
        )

    def test_tax_before_rebate(self, case):
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']['tax_before_rebate']
        assert result['tax_before_rebate'] == expected

    def test_rebate(self, case):
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']['rebate_87a']
        assert result['rebate_87a'] == expected

    def test_surcharge(self, case):
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']['surcharge']
        assert result['surcharge'] == expected

    def test_cess(self, case):
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']['cess']
        assert result['cess'] == expected


# ============================================================
# TESTS: By category (parametrized)
# ============================================================
CATEGORIES = [
    'basic', 'slab_boundary_old', 'slab_boundary_new',
    'standard_deduction', 'hra', 'deductions', 'home_loan',
    'rebate_87a', 'surcharge', 'comprehensive', 'senior_citizen',
    'zero_minimal', 'high_income', 'edge_case',
]


@pytest.mark.skipif(not CALCULATOR_AVAILABLE,
                    reason="RulesCalculator not available")
@pytest.mark.parametrize("category", CATEGORIES)
def test_category_old_regime(category):
    """Verify all cases in a category pass for old regime."""
    cases = CASES_BY_CATEGORY.get(category, [])
    assert len(cases) > 0, f"No cases found for category '{category}'"
    failures = []
    for case in cases:
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']
        if result['taxable_income'] != expected['taxable_income']:
            failures.append(
                f"{case['id']}: taxable_income "
                f"{result['taxable_income']} != {expected['taxable_income']}"
            )
        if result['total_tax'] != expected['total_tax']:
            failures.append(
                f"{case['id']}: total_tax "
                f"{result['total_tax']} != {expected['total_tax']}"
            )
    assert not failures, (
        f"Old regime failures in '{category}':\n" + "\n".join(failures)
    )


@pytest.mark.skipif(not CALCULATOR_AVAILABLE,
                    reason="RulesCalculator not available")
@pytest.mark.parametrize("category", CATEGORIES)
def test_category_new_regime(category):
    """Verify all cases in a category pass for new regime."""
    cases = CASES_BY_CATEGORY.get(category, [])
    assert len(cases) > 0, f"No cases found for category '{category}'"
    failures = []
    for case in cases:
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']
        if result['taxable_income'] != expected['taxable_income']:
            failures.append(
                f"{case['id']}: taxable_income "
                f"{result['taxable_income']} != {expected['taxable_income']}"
            )
        if result['total_tax'] != expected['total_tax']:
            failures.append(
                f"{case['id']}: total_tax "
                f"{result['total_tax']} != {expected['total_tax']}"
            )
    assert not failures, (
        f"New regime failures in '{category}':\n" + "\n".join(failures)
    )


# ============================================================
# TESTS: Official verified cases
# ============================================================
@pytest.mark.skipif(not CALCULATOR_AVAILABLE,
                    reason="RulesCalculator not available")
@pytest.mark.parametrize("case", OFFICIAL_CASES,
                         ids=[c['id'] for c in OFFICIAL_CASES])
class TestOfficialVerified:
    """Test cases verified against official IT department calculator."""

    def test_old_regime_total(self, case):
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']['total_tax']
        assert result['total_tax'] == expected, (
            f"[{case['id']}] Official verified old regime total_tax: "
            f"got {result['total_tax']}, expected {expected}"
        )

    def test_new_regime_total(self, case):
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']['total_tax']
        assert result['total_tax'] == expected, (
            f"[{case['id']}] Official verified new regime total_tax: "
            f"got {result['total_tax']}, expected {expected}"
        )

    def test_old_regime_taxable(self, case):
        result = _run_calculator(case, 'old')
        expected = case['expected_old_regime']['taxable_income']
        assert result['taxable_income'] == expected

    def test_new_regime_taxable(self, case):
        result = _run_calculator(case, 'new')
        expected = case['expected_new_regime']['taxable_income']
        assert result['taxable_income'] == expected


# ============================================================
# TESTS: Edge case specific assertions
# ============================================================
@pytest.mark.skipif(not CALCULATOR_AVAILABLE,
                    reason="RulesCalculator not available")
class TestEdgeCaseAssertions:
    """Targeted assertions for known edge case behaviors."""

    def _find(self, tc_id):
        return next(c for c in ALL_CASES if c['id'] == tc_id)

    def test_zero_income_zero_tax(self):
        """TC181: Zero income should produce zero tax in both regimes."""
        case = self._find('TC181')
        old_r = _run_calculator(case, 'old')
        new_r = _run_calculator(case, 'new')
        assert old_r['total_tax'] == 0
        assert new_r['total_tax'] == 0
        assert old_r['taxable_income'] == 0
        assert new_r['taxable_income'] == 0

    def test_rebate_cliff_old(self):
        """At old taxable 500001, tax should jump from 0 to ~13000."""
        at_limit = self._find('TC111')  # taxable = 500000
        above = self._find('TC112')     # taxable = 500001
        old_at = _run_calculator(at_limit, 'old')
        old_above = _run_calculator(above, 'old')
        assert old_at['total_tax'] == 0, "Tax at rebate limit should be 0"
        assert old_above['total_tax'] > 0, "Tax above rebate limit should be > 0"

    def test_rebate_cliff_new(self):
        """At new taxable 700001, tax should jump from 0 to ~26000."""
        at_limit = self._find('TC121')  # new taxable = 700000
        above = self._find('TC122')     # new taxable = 700001
        new_at = _run_calculator(at_limit, 'new')
        new_above = _run_calculator(above, 'new')
        assert new_at['total_tax'] == 0, "Tax at rebate limit should be 0"
        assert new_above['total_tax'] > 0, "Tax above rebate limit should be > 0"

    def test_surcharge_marginal_relief(self):
        """TC132: Just above 50L, surcharge should be minimal (marginal relief)."""
        case = self._find('TC132')
        old_r = _run_calculator(case, 'old')
        assert old_r['surcharge'] <= 2, (
            f"Surcharge at 50L+1 should be <=2 (marginal relief), "
            f"got {old_r['surcharge']}"
        )

    def test_new_regime_surcharge_cap(self):
        """TC143: New regime surcharge capped at 25% vs old 37%."""
        case = self._find('TC143')
        old_r = _run_calculator(case, 'old')
        new_r = _run_calculator(case, 'new')
        # New regime surcharge rate should not exceed 25%
        if new_r['total_tax'] - new_r['cess'] > 0:
            new_net = new_r['total_tax'] - new_r['cess'] - new_r['surcharge']
            if new_net > 0:
                effective_sc_rate = new_r['surcharge'] / new_net
                assert effective_sc_rate <= 0.2501, (
                    f"New regime surcharge rate {effective_sc_rate:.4f} exceeds 25%"
                )

    def test_super_senior_exemption(self):
        """TC178: Super senior (80+) with 5L income should pay zero tax in old."""
        case = self._find('TC178')
        old_r = _run_calculator(case, 'old')
        assert old_r['total_tax'] == 0, (
            "Super senior with 5L income: old regime tax should be 0"
        )

    def test_standard_deduction_capped(self):
        """TC051: When salary < SD, deduction should equal salary."""
        case = self._find('TC051')  # salary 30000
        old_r = _run_calculator(case, 'old')
        new_r = _run_calculator(case, 'new')
        assert old_r['taxable_income'] == 0
        assert new_r['taxable_income'] == 0

    def test_hra_zero_when_no_rent(self):
        """TC068: HRA exemption should be 0 when rent = 0."""
        case = self._find('TC068')
        old_r = _run_calculator(case, 'old')
        # Without HRA exemption: taxable = 1000000 - 50000 = 950000
        assert old_r['taxable_income'] == 950000

    def test_deductions_dont_exceed_income(self):
        """TC201: When deductions exceed income, taxable = 0."""
        case = self._find('TC201')
        old_r = _run_calculator(case, 'old')
        assert old_r['taxable_income'] == 0
        assert old_r['total_tax'] == 0

    def test_new_regime_ignores_deductions(self):
        """TC099: New regime should ignore 80C/80D/home loan."""
        case_with_ded = self._find('TC099')  # 12L with all deductions
        case_no_ded = self._find('TC012')    # 10L no deductions (different gross)
        new_ded = _run_calculator(case_with_ded, 'new')
        # New regime taxable = gross - 75000 regardless of deductions
        assert new_ded['taxable_income'] == 1200000 - 75000


# ============================================================
# TESTS: Data integrity
# ============================================================
class TestDataIntegrity:
    """Validate the test data files themselves."""

    def test_case_count(self):
        assert len(ALL_CASES) >= 200, f"Need 200+ cases, got {len(ALL_CASES)}"

    def test_official_count(self):
        assert len(OFFICIAL_CASES) >= 30, (
            f"Need 30+ official cases, got {len(OFFICIAL_CASES)}"
        )

    def test_unique_ids(self):
        ids = [c['id'] for c in ALL_CASES]
        assert len(ids) == len(set(ids)), "Duplicate test case IDs found"

    def test_all_categories_present(self):
        cats = set(c['category'] for c in ALL_CASES)
        required = {
            'basic', 'slab_boundary_old', 'slab_boundary_new',
            'standard_deduction', 'hra', 'deductions', 'home_loan',
            'rebate_87a', 'surcharge', 'comprehensive', 'senior_citizen',
            'zero_minimal', 'high_income', 'edge_case',
        }
        missing = required - cats
        assert not missing, f"Missing categories: {missing}"

    def test_required_fields_in_input(self):
        required = {'gross_salary', 'basic_salary', 'age', 'financial_year'}
        for case in ALL_CASES:
            for field in required:
                assert field in case['input'], (
                    f"{case['id']} missing input field '{field}'"
                )

    def test_required_fields_in_expected(self):
        required = {'taxable_income', 'tax_before_rebate', 'rebate_87a',
                     'surcharge', 'cess', 'total_tax'}
        for case in ALL_CASES:
            for regime in ('expected_old_regime', 'expected_new_regime'):
                for field in required:
                    assert field in case[regime], (
                        f"{case['id']} missing {regime}.{field}"
                    )

    def test_total_tax_consistency(self):
        """total_tax should equal (tax-rebate) + surcharge + cess."""
        for case in ALL_CASES:
            for regime_key in ('expected_old_regime', 'expected_new_regime'):
                e = case[regime_key]
                net = max(0, e['tax_before_rebate'] - e['rebate_87a'])
                expected_total = net + e['surcharge'] + e['cess']
                assert e['total_tax'] == expected_total, (
                    f"{case['id']} {regime_key}: total_tax {e['total_tax']} "
                    f"!= {net} + {e['surcharge']} + {e['cess']} = {expected_total}"
                )

    def test_non_negative_values(self):
        for case in ALL_CASES:
            for regime_key in ('expected_old_regime', 'expected_new_regime'):
                e = case[regime_key]
                for k, v in e.items():
                    assert v >= 0, (
                        f"{case['id']} {regime_key}.{k} = {v} is negative"
                    )

    def test_official_verified_flag(self):
        for case in OFFICIAL_CASES:
            assert case.get('verified_against_official') is True

    def test_nl_inputs_exist(self):
        nl_path = os.path.join(TEST_DIR, 'nl_inputs.json')
        assert os.path.exists(nl_path), "nl_inputs.json not found"
        with open(nl_path) as f:
            nl = json.load(f)
        assert len(nl) >= 50, f"Need 50+ NL inputs, got {len(nl)}"

    def test_nl_input_structure(self):
        nl_path = os.path.join(TEST_DIR, 'nl_inputs.json')
        with open(nl_path) as f:
            nl = json.load(f)
        for item in nl:
            assert 'id' in item
            assert 'input_text' in item
            assert 'expected_fields' in item
            assert 'style' in item

    def test_nl_style_coverage(self):
        nl_path = os.path.join(TEST_DIR, 'nl_inputs.json')
        with open(nl_path) as f:
            nl = json.load(f)
        styles = [item['style'] for item in nl]
        assert styles.count('formal_english') >= 10
        assert styles.count('hinglish') >= 8
        assert styles.count('incomplete') >= 8
        assert styles.count('contradictory') >= 4
        assert styles.count('casual') >= 4


# ============================================================
# Run with: pytest test_rules.py -v
# ============================================================
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

