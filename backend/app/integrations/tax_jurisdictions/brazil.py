"""
Brazil Tax Jurisdiction Implementation
IRPF (Imposto de Renda Pessoa Física) - Personal Income Tax
"""
from typing import List, Dict
from decimal import Decimal
from datetime import datetime
from .base import BaseTaxJurisdiction, TaxCalculationResult, CapitalGain
from .calculator import TaxCalculator


class BrazilTaxJurisdiction(BaseTaxJurisdiction):
    """
    Brazil tax jurisdiction
    - IRPF: Progressive income tax (7.5% - 27.5%)
    - Capital Gains: 15% fixed (monthly threshold: BRL 20,000)
    - IVA: Not applicable (VAT is ICMS/PIS/COFINS)
    - Crypto: Classified as "Renda Variável" (variable income)
    - Forms: DIRPF (annual), RFB e-CAC
    """
    
    # Jurisdiction metadata
    code = "BR"
    name = "Brazil"
    currency = "BRL"
    vat_rate = Decimal("0")  # VAT is ICMS, not IVA; ICMS rates vary by state
    tax_rate = Decimal("0.15")  # 15% capital gains fixed
    holding_period_days = 365
    
    # IRPF Progressive rates 2024
    IRPF_RATES = [
        {"min": 0, "max": 22847.76, "rate": Decimal("0")},              # Exempt
        {"min": 22847.76, "max": 34192.64, "rate": Decimal("0.075")},   # 7.5%
        {"min": 34192.64, "max": 68385.38, "rate": Decimal("0.15")},    # 15%
        {"min": 68385.38, "max": 102577.98, "rate": Decimal("0.225")},  # 22.5%
        {"min": 102577.98, "max": float("inf"), "rate": Decimal("0.275")} # 27.5% top rate
    ]
    
    # Capital Gains Tax (fixed)
    CAPITAL_GAINS_TAX_RATE = Decimal("0.15")  # 15% fixed rate
    CAPITAL_GAINS_MONTHLY_THRESHOLD = Decimal("20000")  # BRL 20,000
    
    def calculate_capital_gains_tax(
        self,
        gains: List[CapitalGain],
        calculation_method: str = "fifo"
    ) -> TaxCalculationResult:
        """
        Calculate capital gains tax (Renda Variável)
        
        Brazil: 15% fixed tax on monthly gains exceeding BRL 20,000
        Only months with gains > BRL 20,000 are taxed
        
        Args:
            gains: List of capital gain transactions
            calculation_method: 'fifo', 'lifo', or 'average_cost'
        
        Returns:
            TaxCalculationResult with capital gains tax
        """
        # Group gains by month
        monthly_gains = self._group_gains_by_month(gains)
        
        # Calculate tax only on months exceeding threshold
        total_tax = Decimal("0")
        total_gain = Decimal("0")
        taxable_months = []
        
        for month, month_gain in monthly_gains.items():
            total_gain += month_gain
            
            if month_gain > self.CAPITAL_GAINS_MONTHLY_THRESHOLD:
                tax = month_gain * self.CAPITAL_GAINS_TAX_RATE
                total_tax += tax
                taxable_months.append(f"{month}: BRL {month_gain:.2f} → Tax: BRL {tax:.2f}")
        
        notes = f"Monthly threshold: BRL {self.CAPITAL_GAINS_MONTHLY_THRESHOLD}\n"
        notes += f"Taxable months: {len(taxable_months)}\n"
        notes += "\n".join(taxable_months)
        
        return TaxCalculationResult(
            transaction_type="capital_gains",
            amount=total_gain,
            tax_category="renda_variavel",
            tax_rate=self.CAPITAL_GAINS_TAX_RATE,
            calculated_tax=total_tax,
            notes=notes
        )
    
    def calculate_ordinary_income_tax(
        self,
        income_amount: Decimal
    ) -> TaxCalculationResult:
        """
        Calculate IRPF on ordinary income
        
        Using progressive rates for staking, mining, airdrops
        
        Args:
            income_amount: Total income amount in BRL
        
        Returns:
            TaxCalculationResult with IRPF calculation
        """
        irpf_tax = TaxCalculator.apply_progressive_rates(income_amount, self.IRPF_RATES)
        
        return TaxCalculationResult(
            transaction_type="income",
            amount=income_amount,
            tax_category="renda_ordinaria",
            tax_rate=self._calculate_average_rate(income_amount),
            calculated_tax=irpf_tax,
            notes="IRPF on staking/mining/airdrops income"
        )
    
    def calculate_vat_tax(
        self,
        transaction_value: Decimal,
        transaction_type: str
    ) -> TaxCalculationResult:
        """
        Calculate ICMS/VAT-equivalent
        
        Brazil uses ICMS (state VAT), PIS, and COFINS instead of IVA
        For crypto trading, only IRPF applies
        
        Args:
            transaction_value: Value of transaction
            transaction_type: Type of transaction
        
        Returns:
            TaxCalculationResult (zero for now, crypto trading exempt)
        """
        # Crypto trading is typically not subject to ICMS
        return TaxCalculationResult(
            transaction_type="vat",
            amount=transaction_value,
            tax_category="icms_exempt",
            tax_rate=Decimal("0"),
            calculated_tax=Decimal("0"),
            notes="Crypto trading not subject to ICMS/COFINS"
        )
    
    def calculate_fee_deduction(
        self,
        fee_amount: Decimal
    ) -> Decimal:
        """
        Calculate deductible fees
        
        Trading fees are fully deductible from gains
        
        Args:
            fee_amount: Fee amount in BRL
        
        Returns:
            Deductible amount
        """
        return fee_amount
    
    def apply_progressive_rates(
        self,
        taxable_amount: Decimal
    ) -> Decimal:
        """
        Apply progressive IRPF rates
        
        Args:
            taxable_amount: Taxable income amount
        
        Returns:
            Calculated IRPF tax
        """
        return TaxCalculator.apply_progressive_rates(taxable_amount, self.IRPF_RATES)
    
    def _group_gains_by_month(self, gains: List[CapitalGain]) -> Dict[str, Decimal]:
        """
        Group capital gains by month
        
        Args:
            gains: List of CapitalGain objects
        
        Returns:
            Dictionary of {YYYY-MM: total_gain}
        """
        monthly = {}
        
        for gain in gains:
            month_key = f"{gain.sell_date.year}-{gain.sell_date.month:02d}"
            
            if month_key not in monthly:
                monthly[month_key] = Decimal("0")
            
            monthly[month_key] += gain.gain_amount
        
        return monthly
    
    def _calculate_average_rate(self, amount: Decimal) -> Decimal:
        """
        Calculate average tax rate for given amount
        
        Args:
            amount: Amount to calculate effective rate for
        
        Returns:
            Effective tax rate as percentage
        """
        if amount == 0:
            return Decimal("0")
        
        tax = TaxCalculator.apply_progressive_rates(amount, self.IRPF_RATES)
        rate = (tax / amount * 100).quantize(Decimal("0.01"))
        return rate
    
    def get_forex_gains_tax(self, forex_gains: Decimal) -> Decimal:
        """
        Calculate tax on forex gains (currency appreciation)
        
        Brazil: 1% tax on USD appreciation (buy-side gains only)
        
        Args:
            forex_gains: Forex gain amount in BRL
        
        Returns:
            Calculated forex tax
        """
        forex_tax_rate = Decimal("0.01")  # 1%
        return forex_gains * forex_tax_rate
    
    def get_form_requirements(self) -> Dict:
        """
        Get required tax forms for filing
        
        Returns:
            Dictionary of required forms
        """
        return {
            "primary_form": "DIRPF (Declaração de Ajuste Anual)",
            "schedules": [
                "Renda Variável (Variable Income)",
                "Operações Realizadas (Transaction Records)",
                "Ganho de Capital (Capital Gains)",
                "Aplicações Financeiras (Financial Applications)"
            ],
            "required_docs": [
                "CPF (Cadastro de Pessoa Física)",
                "Proof of residence",
                "Brokerage statements",
                "Bank statements"
            ]
        }
    
    def get_filing_deadline(self, year: int) -> str:
        """
        Get tax filing deadline
        
        Brazil: April 30th of following year
        
        Args:
            year: Tax year
        
        Returns:
            Filing deadline as string
        """
        return f"April 30, {year + 1}"
    
    def get_jurisdiction_info(self) -> Dict:
        """Get jurisdiction information"""
        return {
            "code": self.code,
            "name": self.name,
            "currency": self.currency,
            "vat_rate": float(self.vat_rate),
            "capital_gains_rate": float(self.CAPITAL_GAINS_TAX_RATE),
            "capital_gains_threshold": float(self.CAPITAL_GAINS_MONTHLY_THRESHOLD),
            "filing_frequency": "yearly",
            "filing_authority": "Receita Federal do Brasil",
            "forms_required": self.get_form_requirements(),
            "holding_period_days": self.holding_period_days
        }
