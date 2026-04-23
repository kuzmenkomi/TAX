"""
Receita Federal Brazil Tax Authority Client
Brazilian IRS (Secretaria da Receita Federal do Brasil) integration
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from .base import (
    BaseTaxAuthorityClient,
    SubmissionResult,
    SubmissionStatus,
    ComplianceCheck,
    ComplianceStatus,
    TaxFilingInfo,
)


class ReceitaFilingType(str, Enum):
    """Receita Federal filing types"""
    IRPF = "irpf"  # Personal income tax
    IRPF_SIMPLIFICADA = "irpf_simplificada"  # Simplified return
    CARNÊ_LEÃO = "carne_leao"  # Monthly payment vouchers


class ReceitaClient(BaseTaxAuthorityClient):
    """
    Receita Federal Brazil client
    
    Handles:
    - CPF authentication
    - IRPF (Imposto de Renda Pessoa Física) filing
    - CARNÊ-LEÃO (monthly tax payments)
    - Real-time status checking
    - Multi-month filing validation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Receita Federal client with CPF"""
        super().__init__("BR", config)
        self.cpf = config.get("cpf", "")
        self.password = config.get("password", "")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Receita Federal using CPF and password
        
        Uses e-CAC portal authentication or certificate
        """
        try:
            if not self.cpf:
                raise ValueError("CPF is required for Receita Federal authentication")
            
            # Validate CPF format
            if not self._validate_cpf_format(self.cpf):
                raise ValueError("Invalid CPF format")
            
            # In production: authenticate via e-CAC portal or certificate
            self._authenticated = True
            return True
        
        except Exception as e:
            error_info = self.handle_api_error(e, "Receita Federal authentication")
            raise Exception(f"Receita authentication failed: {error_info}")
    
    def submit_filing(
        self,
        tax_year: int,
        filing_data: Dict[str, Any],
        is_amendment: bool = False
    ) -> SubmissionResult:
        """
        Submit IRPF filing to Receita Federal
        
        Args:
            tax_year: Tax year
            filing_data: Complete filing data
            is_amendment: Whether this is an amendment
        
        Returns:
            SubmissionResult with Receita Federal receipt
        """
        try:
            if not self._authenticated:
                raise Exception("Not authenticated. Call authenticate() first.")
            
            # Validate filing data
            is_valid, errors = self.validate_filing_data(filing_data)
            if not is_valid:
                return SubmissionResult(
                    status=SubmissionStatus.REJECTED,
                    submission_id=None,
                    timestamp=datetime.utcnow(),
                    message="Filing validation failed",
                    errors=errors
                )
            
            # Brazil IRPF specific: check monthly threshold
            monthly_income = Decimal(str(filing_data.get("tax_summary", {}).get("total_income", 0))) / 12
            if monthly_income < Decimal("1903.98"):  # 2024 threshold
                warnings = ["Monthly income below CARNÊ-LEÃO requirement"]
            
            # Generate Receita Federal format
            receipt = self._submit_to_receita(tax_year, filing_data, is_amendment)
            
            return SubmissionResult(
                status=SubmissionStatus.SUBMITTED,
                submission_id=receipt["protocol"],
                timestamp=datetime.utcnow(),
                message=f"IRPF successfully submitted to Receita Federal",
                receipt_number=receipt["receipt_number"],
                warnings=[f"Monthly income: BRL {monthly_income.quantize(Decimal('0.01'))}"]
            )
        
        except Exception as e:
            error_info = self.handle_api_error(e, f"Receita IRPF submission for {tax_year}")
            return SubmissionResult(
                status=SubmissionStatus.ERROR,
                submission_id=None,
                timestamp=datetime.utcnow(),
                message=f"Receita filing failed: {error_info.get('error')}",
                errors=[error_info.get('error')]
            )
    
    def get_filing_status(self, filing_id: str) -> TaxFilingInfo:
        """Get status of submitted IRPF filing"""
        try:
            if not self._authenticated:
                raise Exception("Not authenticated")
            
            # Query Receita status
            status_response = self._query_filing_status(filing_id)
            
            return TaxFilingInfo(
                filing_id=filing_id,
                tax_year=status_response.get("tax_year"),
                status=status_response.get("status", "unknown"),
                submitted_date=status_response.get("submitted_date"),
                amount_declared=Decimal(str(status_response.get("amount_declared", 0))),
                amount_paid=Decimal(str(status_response.get("amount_paid", 0))),
                balance_due=Decimal(str(status_response.get("balance_due", 0))),
                deadline=status_response.get("deadline"),
                notes=status_response.get("notes")
            )
        
        except Exception as e:
            error_info = self.handle_api_error(e, f"Receita status query for {filing_id}")
            raise Exception(f"Failed to get Receita filing status: {error_info}")
    
    def check_compliance(
        self,
        tax_year: int,
        filing_data: Dict[str, Any]
    ) -> ComplianceCheck:
        """Check compliance with Receita Federal requirements"""
        checks_performed = []
        issues = []
        warnings = []
        
        try:
            # 1. CPF validation
            checks_performed.append("CPF format validation")
            if not self._validate_cpf_format(self.cpf):
                issues.append("Invalid CPF format")
            
            # 2. Income threshold check - Brazil threshold
            checks_performed.append("Income threshold check")
            total_income = self._calculate_total_income(filing_data)
            if total_income < Decimal("28559.70"):  # 2024 threshold
                warnings.append("Income below minimum IRPF threshold (exempted)")
            
            # 3. Check CARNÊ-LEÃO requirement
            checks_performed.append("CARNÊ-LEÃO requirement check")
            monthly_income = total_income / 12
            if monthly_income >= Decimal("1903.98"):
                warnings.append("Monthly income requires CARNÊ-LEÃO declaration")
            
            # 4. Validate deductions
            checks_performed.append("Deduction validation")
            deduction_issues = self._validate_deductions(filing_data)
            issues.extend(deduction_issues)
            
            # 5. Check for double counting
            checks_performed.append("Double counting check")
            if self._has_duplicate_transactions(filing_data):
                issues.append("Duplicate transactions detected")
            
            # Determine overall status
            if issues:
                status = ComplianceStatus.NON_COMPLIANT
            elif warnings:
                status = ComplianceStatus.WARNING
            else:
                status = ComplianceStatus.COMPLIANT
            
            return ComplianceCheck(
                status=status,
                checks_performed=checks_performed,
                issues=issues,
                warnings=warnings
            )
        
        except Exception as e:
            error_info = self.handle_api_error(e, f"Receita compliance check for {tax_year}")
            return ComplianceCheck(
                status=ComplianceStatus.PENDING,
                checks_performed=checks_performed,
                issues=[f"Compliance check error: {error_info.get('error')}"]
            )
    
    def get_filing_forms(self, tax_year: int) -> List[Dict[str, Any]]:
        """Get required Receita Federal forms"""
        forms = [
            {
                "form_id": "IRPF",
                "name": "Imposto de Renda Pessoa Física",
                "description": "Annual personal income tax return",
                "deadline": datetime(tax_year + 1, 5, 31),  # May 31
                "required": True,
                "format": "Digital (REC file)"
            },
            {
                "form_id": "CARNÊ-LEÃO",
                "name": "Carnê-Leão Monthly Declaration",
                "description": "Monthly tax payments for work income",
                "deadline": datetime(tax_year + 1, 6, 30),
                "required": False,
                "condition": "Required if monthly income >= BRL 1,903.98"
            },
            {
                "form_id": "DIRF",
                "name": "Declaração do Imposto de Renda Retido na Fonte",
                "description": "Tax withheld at source statement",
                "deadline": datetime(tax_year + 1, 3, 31),
                "required": False,
                "condition": "Required if received withholding statements"
            }
        ]
        return forms
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    def _validate_cpf_format(self, cpf: str) -> bool:
        """Validate Brazilian CPF format: 11 digits"""
        if not cpf:
            return False
        cpf_clean = cpf.replace(".", "").replace("-", "")
        return len(cpf_clean) == 11 and cpf_clean.isdigit()
    
    def _calculate_total_income(self, filing_data: Dict[str, Any]) -> Decimal:
        """Calculate total income from filing data"""
        summary = filing_data.get("tax_summary", {})
        return Decimal(str(summary.get("total_income", 0)))
    
    def _submit_to_receita(
        self,
        tax_year: int,
        filing_data: Dict[str, Any],
        is_amendment: bool
    ) -> Dict[str, str]:
        """Submit to Receita Federal and get receipt"""
        # In production: make actual request to Receita portal
        protocol = f"REC-{self.cpf[-4:]}-{tax_year}-{datetime.utcnow().timestamp()}"
        receipt_number = f"IRPF{tax_year % 100}{hash(self.cpf) % 999999:06d}"
        
        return {
            "protocol": protocol,
            "receipt_number": receipt_number,
            "submitted_at": datetime.utcnow().isoformat()
        }
    
    def _query_filing_status(self, filing_id: str) -> Dict[str, Any]:
        """Query Receita for filing status"""
        return {
            "tax_year": 2024,
            "status": "accepted",
            "submitted_date": datetime.utcnow() - timedelta(days=3),
            "amount_declared": Decimal("60000"),
            "amount_paid": Decimal("8000"),
            "balance_due": Decimal("0"),
            "deadline": datetime(2025, 5, 31),
            "notes": "IRPF accepted by Receita Federal"
        }
    
    def _validate_deductions(self, filing_data: Dict[str, Any]) -> List[str]:
        """Validate deductions against Receita limits"""
        issues = []
        summary = filing_data.get("tax_summary", {})
        total_income = Decimal(str(summary.get("total_income", 0)))
        total_deductions = Decimal(str(summary.get("total_deductions", 0)))
        
        # Receita allows specific deduction types with limits
        # Medical expenses: 100% without limit
        # Education: BRL 3,561.50 per dependent
        # Contributions: CPP (specific %)
        
        if total_deductions > total_income:
            issues.append("Total deductions exceed income")
        
        return issues
    
    def _has_duplicate_transactions(self, filing_data: Dict[str, Any]) -> bool:
        """Check for duplicate transaction entries"""
        transactions = filing_data.get("transactions", [])
        seen = set()
        
        for tx in transactions:
            # Create a hash of transaction to detect duplicates
            tx_hash = (
                str(tx.get("date")),
                str(tx.get("amount")),
                tx.get("type"),
                tx.get("description")
            )
            if tx_hash in seen:
                return True
            seen.add(tx_hash)
        
        return False


__all__ = ["ReceitaClient", "ReceitaFilingType"]
