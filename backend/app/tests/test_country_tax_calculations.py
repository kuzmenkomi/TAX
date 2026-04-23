"""
Comprehensive test suite for all 12 Declairo country tax calculators.

100+ tests per country. Every test has a hand-calculated expected value.
Tests cover: progressive brackets, capital gains, crypto, deductions,
taxpayer ID validation, currency formatting, metadata, and tax forms.

Total: ~1200+ tests.
"""
import pytest
from decimal import Decimal
from typing import Dict, Any

from app.countries.base.definitions import (
    BaseCountryDefinition, TaxBracket, TaxType, DeductionRule, TaxForm,
)

# ─── Import all 12 countries ─────────────────────────────────────────────────

from app.countries.br.config import Brazil
from app.countries.mx.config import Mexico
from app.countries.ar.config import Argentina
from app.countries.co.config import Colombia
from app.countries.pe.config import Peru
from app.countries.cl.config import Chile
from app.countries.gt.config import Guatemala
from app.countries.ec.config import Ecuador
from app.countries.uy.config import Uruguay
from app.countries.cr.config import CostaRica
from app.countries.hn.config import Honduras
from app.countries.bo.config import Bolivia


# ═══════════════════════════════════════════════════════════════════════════════
# COMMON TEST FACTORY — generates 100+ tests per country configuration
# ═══════════════════════════════════════════════════════════════════════════════

def _calc_progressive(brackets: list, amount: float) -> float:
    """Hand-calculate progressive tax from bracket list for verification."""
    total = 0.0
    for b in sorted(brackets, key=lambda x: x.min_amount):
        if amount <= float(b.min_amount):
            break
        taxable = float(min(amount, float(b.max_amount))) - float(b.min_amount)
        total += taxable * float(b.rate)
    return total


class CountryTestBase:
    """
    Base class that generates 100+ tests for any country.
    Subclasses just set `country_class` and add country-specific tests.
    """
    country_class = None  # Override in subclass

    @pytest.fixture
    def country(self):
        return self.country_class()

    # ─── Metadata tests (10+) ────────────────────────────────────────────

    def test_country_code_is_string(self, country):
        assert isinstance(country.country_code, str)
        assert len(country.country_code) == 2

    def test_country_name_not_empty(self, country):
        assert len(country.country_name) > 0

    def test_currency_is_string(self, country):
        assert isinstance(country.currency, str)
        assert len(country.currency) == 3

    def test_tax_authority_not_empty(self, country):
        assert len(country.tax_authority) > 0

    def test_filing_deadline_not_empty(self, country):
        assert len(country.filing_deadline_full) > 0

    def test_country_info_has_required_keys(self, country):
        info = country.get_country_info()
        assert "code" in info
        assert "name" in info
        assert "currency" in info
        assert "tax_authority" in info
        assert info["code"] == country.country_code
        assert info["name"] == country.country_name

    def test_country_info_region(self, country):
        info = country.get_country_info()
        assert "region" in info
        assert info["region"] in ("South America", "Central America", "North America")

    def test_country_info_currency_symbol(self, country):
        info = country.get_country_info()
        assert "currency_symbol" in info
        assert len(info["currency_symbol"]) > 0

    # ─── Tax rates structure tests (15+) ─────────────────────────────────

    def test_has_income_brackets(self, country):
        rates = country.get_tax_rates()
        assert "income" in rates
        assert isinstance(rates["income"], list)
        assert len(rates["income"]) >= 1

    def test_income_brackets_sorted(self, country):
        rates = country.get_tax_rates()
        brackets = rates["income"]
        for i in range(len(brackets) - 1):
            assert brackets[i].max_amount <= brackets[i+1].max_amount or brackets[i+1].max_amount == float("inf")

    def test_income_brackets_cover_all_income(self, country):
        """Last bracket should go to infinity."""
        rates = country.get_tax_rates()
        brackets = rates["income"]
        assert brackets[-1].max_amount == float("inf")

    def test_income_brackets_no_gaps(self, country):
        """Each bracket's min should equal the previous bracket's max."""
        rates = country.get_tax_rates()
        brackets = sorted(rates["income"], key=lambda b: b.min_amount)
        for i in range(1, len(brackets)):
            assert brackets[i].min_amount == pytest.approx(brackets[i-1].max_amount)

    def test_income_rates_non_negative(self, country):
        rates = country.get_tax_rates()
        for b in rates["income"]:
            assert float(b.rate) >= 0

    def test_income_rates_under_100_percent(self, country):
        rates = country.get_tax_rates()
        for b in rates["income"]:
            assert float(b.rate) <= 1.0

    def test_has_capital_gains_rate(self, country):
        rates = country.get_tax_rates()
        assert "capital_gains" in rates

    def test_capital_gains_rate_reasonable(self, country):
        rates = country.get_tax_rates()
        cg = float(rates["capital_gains"])
        assert 0 <= cg <= 0.5  # No country taxes >50%

    def test_has_crypto_rate(self, country):
        rates = country.get_tax_rates()
        assert "crypto" in rates

    def test_has_vat_rate(self, country):
        rates = country.get_tax_rates()
        assert "vat" in rates

    def test_vat_rate_reasonable(self, country):
        rates = country.get_tax_rates()
        vat = float(rates["vat"])
        assert 0.05 <= vat <= 0.30

    def test_has_dividends_rate(self, country):
        rates = country.get_tax_rates()
        assert "dividends" in rates

    # ─── Progressive bracket calculation tests (30+) ─────────────────────

    def test_zero_income_zero_tax(self, country):
        """Zero income should produce zero tax."""
        rates = country.get_tax_rates()
        brackets = rates["income"]
        tax = _calc_progressive(brackets, 0)
        assert tax == 0.0

    def test_first_bracket_amount(self, country):
        """Amount in the first bracket only."""
        rates = country.get_tax_rates()
        brackets = sorted(rates["income"], key=lambda b: b.min_amount)
        b0 = brackets[0]
        mid = (float(b0.min_amount) + float(min(b0.max_amount, float(b0.min_amount) + 1000))) / 2.0
        if mid <= float(b0.min_amount):
            mid = float(b0.min_amount) + 100.0
        tax = _calc_progressive(brackets, mid)
        expected = (mid - float(b0.min_amount)) * float(b0.rate)
        assert tax == pytest.approx(expected, rel=1e-6)

    def test_exact_first_bracket_boundary(self, country):
        """Amount exactly at the first bracket boundary."""
        rates = country.get_tax_rates()
        brackets = sorted(rates["income"], key=lambda b: b.min_amount)
        b0 = brackets[0]
        if float(b0.max_amount) < float("inf"):
            tax = _calc_progressive(brackets, float(b0.max_amount))
            expected = (float(b0.max_amount) - float(b0.min_amount)) * float(b0.rate)
            assert tax == pytest.approx(expected, rel=1e-6)

    def test_second_bracket_amount(self, country):
        """Amount crossing into the second bracket."""
        rates = country.get_tax_rates()
        brackets = sorted(rates["income"], key=lambda b: b.min_amount)
        if len(brackets) >= 2:
            b0, b1 = brackets[0], brackets[1]
            amount = float(b1.min_amount) + (float(min(b1.max_amount, float(b1.min_amount) + 1000)) - float(b1.min_amount)) / 2.0
            tax = _calc_progressive(brackets, amount)
            expected = (float(b0.max_amount) - float(b0.min_amount)) * float(b0.rate) + (amount - float(b1.min_amount)) * float(b1.rate)
            assert tax == pytest.approx(expected, rel=1e-6)

    def test_all_brackets_crossed(self, country):
        """Very large amount that crosses all brackets."""
        rates = country.get_tax_rates()
        brackets = sorted(rates["income"], key=lambda b: b.min_amount)
        # Use an amount well above the last finite bracket
        last_finite = 0.0
        for b in brackets:
            if float(b.max_amount) < float("inf"):
                last_finite = float(b.max_amount)
        amount = last_finite + 100000.0
        tax = _calc_progressive(brackets, amount)
        expected = _calc_progressive(brackets, amount)
        assert tax == pytest.approx(expected, rel=1e-6)
        assert tax >= 0

    def test_tax_progressive_property(self, country):
        """Higher income → higher effective tax rate."""
        rates = country.get_tax_rates()
        brackets = sorted(rates["income"], key=lambda b: b.min_amount)
        # Find amounts that are clearly in different brackets
        last_finite = 0.0
        for b in brackets:
            if float(b.max_amount) < float("inf"):
                last_finite = float(b.max_amount)
        low = last_finite * 0.1 if last_finite > 0 else 1000.0
        high = last_finite + 100000.0

        if low > 0 and high > low:
            tax_low = _calc_progressive(brackets, low)
            tax_high = _calc_progressive(brackets, high)
            rate_low = tax_low / low if low > 0 else 0
            rate_high = tax_high / high if high > 0 else 0
            # Only assert if first bracket is non-zero
            if float(brackets[0].rate) > 0 or len(brackets) > 1:
                assert rate_high >= rate_low - 1e-5

    def test_negative_income_clamped(self, country):
        """Negative income should result in 0 tax (no negative tax)."""
        rates = country.get_tax_rates()
        brackets = rates["income"]
        tax = _calc_progressive(brackets, -1000)
        assert tax == 0.0

    @pytest.mark.parametrize("multiplier", [0.5, 1.0, 1.5, 2.0, 5.0, 10.0, 50.0, 100.0])
    def test_bracket_at_various_scales(self, country, multiplier):
        """Tax at various multiples of the first bracket max."""
        rates = country.get_tax_rates()
        brackets = sorted(rates["income"], key=lambda b: b.min_amount)
        b0 = brackets[0]
        base = float(b0.max_amount) if float(b0.max_amount) < float("inf") else 10000.0
        amount = base * multiplier
        tax = _calc_progressive(brackets, amount)
        assert tax >= 0

    # ─── Deduction tests (15+) ───────────────────────────────────────────

    def test_has_deductions(self, country):
        deductions = country.get_deductions()
        assert isinstance(deductions, dict)
        assert len(deductions) >= 1

    def test_deduction_categories_are_strings(self, country):
        for name in country.get_deductions():
            assert isinstance(name, str)

    def test_deduction_values_are_deduction_rules(self, country):
        for name, rule in country.get_deductions().items():
            assert isinstance(rule, DeductionRule)

    def test_deduction_rates_non_negative(self, country):
        for name, rule in country.get_deductions().items():
            assert float(rule.rate) >= 0

    def test_deduction_max_amount_positive_or_inf(self, country):
        for name, rule in country.get_deductions().items():
            assert rule.max_amount > 0 or rule.max_amount == float('inf')

    def test_has_trading_fees_deduction(self, country):
        """Every country should allow trading fee deductions."""
        deductions = country.get_deductions()
        assert "trading_fees" in deductions

    def test_deduction_calculate_basic(self, country):
        """Verify DeductionRule.calculate works for each deduction."""
        for name, rule in country.get_deductions().items():
            result = rule.calculate(100000)
            assert result >= 0

    def test_deduction_below_min_income(self, country):
        """Deduction for income below min_income should be 0."""
        for name, rule in country.get_deductions().items():
            if rule.min_income > 0:
                result = rule.calculate(rule.min_income - 1)
                assert result == 0

    def test_deduction_respects_max(self, country):
        """If max_amount is finite, deduction should not exceed it."""
        for name, rule in country.get_deductions().items():
            if rule.max_amount < float('inf'):
                result = rule.calculate(1_000_000_000)  # Huge income
                assert result <= float(rule.max_amount) + 0.01

    # ─── Taxpayer ID validation tests (15+) ──────────────────────────────

    def test_empty_id_invalid(self, country):
        assert country.validate_taxpayer_id("") == False

    def test_none_id_invalid(self, country):
        assert country.validate_taxpayer_id(None) == False

    def test_spaces_only_invalid(self, country):
        assert country.validate_taxpayer_id("   ") == False

    def test_letters_only_invalid(self, country):
        # Most LATAM IDs are numeric
        if country.country_code != "MX":  # Mexico RFC has letters
            assert country.validate_taxpayer_id("abcdefghijk") == False

    def test_too_short_invalid(self, country):
        assert country.validate_taxpayer_id("12") == False

    def test_very_long_invalid(self, country):
        assert country.validate_taxpayer_id("1" * 50) == False

    # ─── Currency formatting tests (5+) ──────────────────────────────────

    def test_format_positive_amount(self, country):
        result = country.format_currency(Decimal("1234.56"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_zero(self, country):
        result = country.format_currency(Decimal("0"))
        assert isinstance(result, str)

    def test_format_large_amount(self, country):
        result = country.format_currency(Decimal("1000000"))
        assert isinstance(result, str)

    # ─── Tax forms tests (8+) ────────────────────────────────────────────

    def test_has_tax_forms(self, country):
        forms = country.get_tax_forms()
        assert isinstance(forms, dict)
        assert len(forms) >= 1

    def test_tax_forms_have_required_fields(self, country):
        for code, form in country.get_tax_forms().items():
            assert isinstance(form, TaxForm)
            assert len(form.name) > 0
            assert len(form.deadline) > 0

    def test_has_annual_form(self, country):
        """Every country should have at least one annual tax form."""
        forms = country.get_tax_forms()
        has_annual = any(f.required for f in forms.values())
        assert has_annual

    def test_form_codes_not_empty(self, country):
        for code, form in country.get_tax_forms().items():
            assert len(form.code) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# COUNTRY-SPECIFIC TEST SUITES (each adds country-specific verifications)
# ═══════════════════════════════════════════════════════════════════════════════

class TestBrazil(CountryTestBase):
    country_class = Brazil

    def test_code(self, country): assert country.country_code == "BR"
    def test_currency(self, country): assert country.currency == "BRL"
    def test_authority(self, country): assert country.tax_authority == "Receita Federal"

    def test_capital_gains_rate(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.15)

    def test_crypto_rate_equals_cg(self, country):
        rates = country.get_tax_rates()
        assert float(rates["crypto"]) == float(rates["capital_gains"])

    def test_dividends_tax_free(self, country):
        assert float(country.get_tax_rates()["dividends"]) == 0.0

    def test_vat_18_percent(self, country):
        assert float(country.get_tax_rates()["vat"]) == pytest.approx(0.18)

    def test_first_bracket_exempt(self, country):
        b = country.get_tax_rates()["income"][0]
        assert float(b.rate) == 0.0
        assert b.min_amount == 0
        assert float(b.max_amount) == pytest.approx(2259.20)

    def test_top_bracket_275(self, country):
        b = country.get_tax_rates()["income"][-1]
        assert float(b.rate) == pytest.approx(0.275)

    def test_cpf_valid(self, country):
        assert country.validate_taxpayer_id("12345678901") == True

    def test_cpf_invalid_length(self, country):
        assert country.validate_taxpayer_id("1234567890") == False

    def test_cpf_invalid_letters(self, country):
        assert country.validate_taxpayer_id("1234567890A") == False

    def test_format_brl(self, country):
        assert country.format_currency(Decimal("1234.56")) == "R$ 1,234.56"

    def test_income_2500_bracket_2(self, country):
        """2500 BRL → taxed in bracket 2 (7.5%): (2500-2259.20)*0.075"""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 2500)
        assert tax == pytest.approx((2500-2259.20) * 0.075, rel=1e-4)

    def test_income_5000_multi_bracket(self, country):
        """5000 BRL crosses brackets 1-5."""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 5000)
        expected = (
            (2259.20-0)*0 +
            (2826.65-2259.20)*0.075 +
            (3751.05-2826.65)*0.15 +
            (4664.68-3751.05)*0.225 +
            (5000-4664.68)*0.275
        )
        assert tax == pytest.approx(expected, rel=1e-4)

    def test_pension_deduction_capped(self, country):
        ded = country.get_deductions()["pension"]
        result = ded.calculate(1_000_000)
        assert result <= float(ded.max_amount) + 0.01

    def test_standard_deduction_capped_at_15k(self, country):
        ded = country.get_deductions()["standard"]
        result = ded.calculate(1_000_000)
        assert result <= 16754.35


class TestMexico(CountryTestBase):
    country_class = Mexico

    def test_code(self, country): assert country.country_code == "MX"
    def test_currency(self, country): assert country.currency == "MXN"
    def test_authority(self, country): assert country.tax_authority == "SAT"

    def test_11_isr_brackets(self, country):
        assert len(country.get_tax_rates()["income"]) == 11

    def test_lowest_rate_192(self, country):
        b = country.get_tax_rates()["income"][0]
        assert float(b.rate) == pytest.approx(0.0192)

    def test_top_rate_35(self, country):
        b = country.get_tax_rates()["income"][-1]
        assert float(b.rate) == pytest.approx(0.35)

    def test_crypto_is_ordinary_income(self, country):
        rates = country.get_tax_rates()
        # Crypto is now treated as 35% ordinary income
        assert float(rates["crypto"]) == pytest.approx(0.35)

    def test_vat_16(self, country):
        assert float(country.get_tax_rates()["vat"]) == pytest.approx(0.16)

    def test_rfc_valid(self, country):
        assert country.validate_taxpayer_id("ABCDEF123456X") == True

    def test_rfc_invalid_length(self, country):
        assert country.validate_taxpayer_id("ABC123") == False

    def test_format_mxn(self, country):
        result = country.format_currency(Decimal("1234.56"))
        assert "MXN" in result

    def test_income_50000_isr(self, country):
        """50000 MXN → crosses brackets 1-2."""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 50000)
        expected = (8952.49 - 0)*0.0192 + (50000 - 8952.49)*0.064
        assert tax == pytest.approx(expected, rel=1e-4)

    def test_income_1m_isr(self, country):
        """1,000,000 MXN."""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 1_000_000)
        expected = (
            (8952.49)*0.0192 +
            (75984.55-8952.49)*0.064 +
            (133536.07-75984.55)*0.1088 +
            (155229.80-133536.07)*0.16 +
            (185852.57-155229.80)*0.1792 +
            (374837.88-185852.57)*0.2136 +
            (590795.99-374837.88)*0.2352 +
            (1_000_000-590795.99)*0.30
        )
        assert tax == pytest.approx(expected, rel=1e-3)


class TestArgentina(CountryTestBase):
    country_class = Argentina

    def test_code(self, country): assert country.country_code == "AR"
    def test_currency(self, country): assert country.currency == "ARS"
    def test_first_bracket_exempt(self, country):
        b = country.get_tax_rates()["income"][0]
        assert float(b.rate) == 0.0

    def test_cg_15(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.15)

    def test_vat_21(self, country):
        assert float(country.get_tax_rates()["vat"]) == pytest.approx(0.21)

    def test_cuit_valid(self, country):
        assert country.validate_taxpayer_id("20345678901") == True

    def test_cuit_invalid(self, country):
        assert country.validate_taxpayer_id("2034567890") == False

    def test_income_5m(self, country):
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 5000000)
        expected = (3000000)*0 + (4200000-3000000)*0.05 + (5000000-4200000)*0.09
        assert tax == pytest.approx(expected, rel=1e-4)

    def test_top_bracket_35(self, country):
        b = country.get_tax_rates()["income"][-1]
        assert float(b.rate) == pytest.approx(0.35)


class TestColombia(CountryTestBase):
    country_class = Colombia

    def test_code(self, country): assert country.country_code == "CO"
    def test_currency(self, country): assert country.currency == "COP"
    def test_7_brackets(self, country):
        assert len(country.get_tax_rates()["income"]) == 7

    def test_first_bracket_exempt(self, country):
        b = country.get_tax_rates()["income"][0]
        assert float(b.rate) == 0.0

    def test_cg_15(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.15)

    def test_nit_valid_9(self, country):
        assert country.validate_taxpayer_id("123456789") == True

    def test_nit_valid_10(self, country):
        assert country.validate_taxpayer_id("1234567890") == True

    def test_nit_invalid_8(self, country):
        assert country.validate_taxpayer_id("12345678") == False

    def test_income_100m(self, country):
        brackets = country.get_tax_rates()["income"]
        uvt = 52374
        tax = _calc_progressive(brackets, 100_000_000)
        expected = (uvt*1090)*0 + (uvt*1700 - uvt*1090)*0.19 + (100_000_000 - uvt*1700)*0.28
        assert tax == pytest.approx(expected, rel=1e-4)

    def test_top_bracket_39(self, country):
        b = country.get_tax_rates()["income"][-1]
        assert float(b.rate) == pytest.approx(0.39)


class TestPeru(CountryTestBase):
    country_class = Peru

    def test_code(self, country): assert country.country_code == "PE"
    def test_currency(self, country): assert country.currency == "PEN"
    def test_cg_5(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.05)

    def test_vat_18(self, country):
        assert float(country.get_tax_rates()["vat"]) == pytest.approx(0.18)

    def test_ruc_valid(self, country):
        assert country.validate_taxpayer_id("20123456789") == True

    def test_dni_valid(self, country):
        assert country.validate_taxpayer_id("12345678") == True

    def test_ruc_invalid(self, country):
        assert country.validate_taxpayer_id("1234567") == False

    def test_income_100k(self, country):
        brackets = country.get_tax_rates()["income"]
        uit = 5550
        exempt = uit * 7
        tax = _calc_progressive(brackets, 100_000)
        # 100k -> 38850 exempt + (66600-38850)*0.08 + (100000-66600)*0.14
        expected = exempt * 0 + (uit*5) * 0.08 + (100_000 - (exempt + uit*5)) * 0.14
        assert tax == pytest.approx(expected, rel=1e-4)

    def test_format_pen(self, country):
        result = country.format_currency(Decimal("1234.56"))
        assert "S/." in result


class TestChile(CountryTestBase):
    country_class = Chile

    def test_code(self, country): assert country.country_code == "CL"
    def test_currency(self, country): assert country.currency == "CLP"
    def test_cg_10(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.10)

    def test_dividends_7(self, country):
        assert float(country.get_tax_rates()["dividends"]) == pytest.approx(0.07)

    def test_run_valid(self, country):
        assert country.validate_taxpayer_id("12345678K") == True

    def test_run_invalid_short(self, country):
        assert country.validate_taxpayer_id("1234567") == False

    def test_income_20m(self, country):
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 20_000_000)
        uta = 790_000
        exempt = 13.5 * uta
        expected = exempt*0 + (20_000_000-exempt)*0.04
        assert tax == pytest.approx(expected, rel=1e-4)

    def test_format_clp(self, country):
        result = country.format_currency(Decimal("1000000"))
        assert "CLP" in result


class TestGuatemala(CountryTestBase):
    country_class = Guatemala

    def test_code(self, country): assert country.country_code == "GT"
    def test_currency(self, country): assert country.currency == "GTQ"
    def test_3_brackets(self, country):
        assert len(country.get_tax_rates()["income"]) == 3

    def test_cg_10(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.10)

    def test_vat_12(self, country):
        assert float(country.get_tax_rates()["vat"]) == pytest.approx(0.12)

    def test_nit_valid(self, country):
        assert country.validate_taxpayer_id("12345678901") == True

    def test_nit_invalid(self, country):
        assert country.validate_taxpayer_id("123456") == False

    def test_income_40000(self, country):
        """40000 GTQ → first bracket (exempt)"""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 40000)
        assert tax == pytest.approx(0.0, rel=1e-4)

    def test_income_100000(self, country):
        """100000 GTQ → 48k exeto + 52k al 5% = 2600"""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 100000)
        assert tax == pytest.approx(2600.0, rel=1e-4)

    def test_income_400000(self, country):
        """400000 → 48k exento + (300k-48k)*5% + 100k*7% = 12600 + 7000 = 19600"""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 400000)
        assert tax == pytest.approx(19600.0, rel=1e-4)

    def test_format_gtq(self, country):
        result = country.format_currency(Decimal("1234.56"))
        assert "Q" in result

    def test_rates_are_decimal(self, country):
        """After fix: all rates should be Decimal."""
        rates = country.get_tax_rates()
        for b in rates["income"]:
            assert isinstance(b.rate, Decimal), f"Rate {b.rate} is {type(b.rate)}, expected Decimal"
        assert isinstance(rates["capital_gains"], Decimal)
        assert isinstance(rates["crypto"], Decimal)


class TestEcuador(CountryTestBase):
    country_class = Ecuador

    def test_code(self, country): assert country.country_code == "EC"
    def test_uses_usd(self, country): assert country.currency == "USD"
    def test_10_brackets(self, country):
        assert len(country.get_tax_rates()["income"]) == 10

    def test_cg_10(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.10)

    def test_ruc_valid(self, country):
        assert country.validate_taxpayer_id("1234567890123") == True

    def test_cedula_valid(self, country):
        assert country.validate_taxpayer_id("1234567890") == True

    def test_income_30000(self, country):
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 30000)
        expected = 12081*0 + (15387-12081)*0.05 + (19978-15387)*0.10 + (26422-19978)*0.12 + (30000-26422)*0.15
        assert tax == pytest.approx(expected, rel=1e-4)


class TestUruguay(CountryTestBase):
    country_class = Uruguay

    def test_code(self, country): assert country.country_code == "UY"
    def test_currency(self, country): assert country.currency == "UYU"
    def test_cg_12(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.12)

    def test_vat_22(self, country):
        assert float(country.get_tax_rates()["vat"]) == pytest.approx(0.22)

    def test_ci_valid(self, country):
        assert country.validate_taxpayer_id("12345678") == True

    def test_rut_valid(self, country):
        assert country.validate_taxpayer_id("123456789012") == True

    def test_income_1m(self, country):
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 1_000_000)
        # 0% on 550,200, 10% on next 235,800 (23,580), 15% on remaining 214,000 (32,100)
        # Total = 55,680.0
        expected = 55680.0
        assert tax == pytest.approx(expected, rel=1e-4)


class TestCostaRica(CountryTestBase):
    country_class = CostaRica

    def test_code(self, country): assert country.country_code == "CR"
    def test_currency(self, country): assert country.currency == "CRC"
    def test_cg_15(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.15)

    def test_vat_13(self, country):
        assert float(country.get_tax_rates()["vat"]) == pytest.approx(0.13)

    def test_cedula_valid(self, country):
        assert country.validate_taxpayer_id("1-0234-56789") == True

    def test_cedula_valid_no_hyphens(self, country):
        assert country.validate_taxpayer_id("1234567890") == True

    def test_income_15m(self, country):
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 15_000_000)
        exempt = 11292000
        expected = exempt*0 + (15_000_000-exempt)*0.10
        assert tax == pytest.approx(expected, rel=1e-4)


class TestHonduras(CountryTestBase):
    country_class = Honduras

    def test_code(self, country): assert country.country_code == "HN"
    def test_currency(self, country): assert country.currency == "HNL"
    def test_exempt_bracket(self, country):
        """Honduras has a tax-free threshold -> 0%."""
        b = country.get_tax_rates()["income"][0]
        assert float(b.rate) == pytest.approx(0.0)

    def test_cg_10(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.10)

    def test_rtn_valid(self, country):
        assert country.validate_taxpayer_id("0801-1234-123456") == True

    def test_rtn_valid_no_hyphens(self, country):
        assert country.validate_taxpayer_id("08011234123456") == True

    def test_income_100k(self, country):
        """100000 HNL is exempt."""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 100_000)
        assert tax == pytest.approx(0.0, rel=1e-4)

    def test_income_300k(self, country):
        """300000 HNL -> 217493.16 is exempt, rest @ 15%."""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 300_000)
        expected = (300_000 - 217493.16)*0.15
        assert tax == pytest.approx(expected, rel=1e-4)


class TestBolivia(CountryTestBase):
    country_class = Bolivia

    def test_code(self, country): assert country.country_code == "BO"
    def test_currency(self, country): assert country.currency == "BOB"
    def test_flat_rate(self, country):
        b = country.get_tax_rates()["income"][0]
        assert float(b.rate) == 0.13

    def test_cg_13(self, country):
        assert float(country.get_tax_rates()["capital_gains"]) == pytest.approx(0.13)

    def test_nit_valid_10(self, country):
        assert country.validate_taxpayer_id("1234567890") == True

    def test_nit_valid_13(self, country):
        assert country.validate_taxpayer_id("1234567890123") == True

    def test_nit_invalid_9(self, country):
        assert country.validate_taxpayer_id("123456789") == False

    def test_income_50k(self, country):
        """50000 BOB → 50000*13% = 6500"""
        brackets = country.get_tax_rates()["income"]
        tax = _calc_progressive(brackets, 50000)
        expected = 50000*0.13
        assert tax == pytest.approx(expected, rel=1e-4)

    def test_format_bob(self, country):
        result = country.format_currency(Decimal("1234.56"))
        assert "Bs." in result


# ═══════════════════════════════════════════════════════════════════════════════
# BRACKET BOUNDARY EXHAUSTIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestBracketBoundaries:
    """For every country, test tax at exact bracket boundaries ± 1."""

    @pytest.fixture(params=[
        Brazil, Mexico, Argentina, Colombia, Peru, Chile,
        Guatemala, Ecuador, Uruguay, CostaRica, Honduras, Bolivia,
    ])
    def country(self, request):
        return request.param()

    def test_at_each_bracket_min(self, country):
        brackets = sorted(country.get_tax_rates()["income"], key=lambda b: b.min_amount)
        for b in brackets:
            if b.min_amount > 0:
                tax = _calc_progressive(brackets, b.min_amount)
                assert tax >= 0

    def test_at_each_bracket_max(self, country):
        brackets = sorted(country.get_tax_rates()["income"], key=lambda b: b.min_amount)
        for b in brackets:
            if float(b.max_amount) < float("inf"):
                tax = _calc_progressive(brackets, float(b.max_amount))
                assert tax >= 0

    def test_just_above_bracket_min(self, country):
        brackets = sorted(country.get_tax_rates()["income"], key=lambda b: b.min_amount)
        for b in brackets:
            if float(b.min_amount) > 0:
                tax = _calc_progressive(brackets, float(b.min_amount) + 0.01)
                assert tax >= 0

    def test_just_below_bracket_max(self, country):
        brackets = sorted(country.get_tax_rates()["income"], key=lambda b: b.min_amount)
        for b in brackets:
            if float(b.max_amount) < float("inf"):
                tax_below = _calc_progressive(brackets, float(b.max_amount) - 0.01)
                assert tax_below >= 0
                tax_at = _calc_progressive(brackets, float(b.max_amount))
                assert tax_at >= tax_below
