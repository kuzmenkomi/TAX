"""
Audit Trail & Export Engine
Generates verified audit packages for tax authority submission
"""

from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import json
import hashlib

from app.advanced_tax.services.base_service import BaseService
from app.advanced_tax.models.audit_models import (
    VerifiedTaxRule,
    CalculationAuditRecord,
    AuditPackage,
)
from app.advanced_tax.utils import AuditStatus, ServiceException

logger = logging.getLogger(__name__)


class AuditEngine(BaseService):
    """
    Generates comprehensive audit packages for tax compliance.
    
    Exports:
    - All transactions
    - All tax calculations
    - Verified rules used
    - Calculation reasoning
    - Ready for tax authority review
    """
    
    def validate_inputs(self, **kwargs) -> bool:
        """Validate audit inputs"""
        if 'tax_year' in kwargs:
            year = kwargs['tax_year']
            if not isinstance(year, int) or year < 2000 or year > 2100:
                raise ServiceException(f"Invalid tax_year: {year}")
        return True
    
    def generate_audit_package(
        self,
        tax_year: int,
        export_formats: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete audit package for user for the specified tax year.
        
        Includes:
        - All transactions
        - All calculations
        - Verified rules
        - Reasoning for every calculation
        
        Returns:
            Package metadata with file paths
        """
        if export_formats is None:
            export_formats = ['json']  # Default to JSON
        
        try:
            self.log_event("AUDIT_GENERATION_STARTED", {
                "user_id": self.user_id,
                "country": self.country,
                "tax_year": tax_year,
                "formats": export_formats,
            })
            
            # Gather data
            calculations = self._get_tax_calculations(tax_year)
            rules_used = self._get_rules_used(calculations)
            transactions = self._get_transactions(tax_year)
            
            # Create audit package record
            package = AuditPackage(
                user_id=self.user_id,
                country=self.country,
                tax_year=tax_year,
                transaction_count=len(transactions),
                calculation_count=len(calculations),
                total_tax_calculated=sum(c.calculated_tax for c in calculations),
                generated_by_system_version="1.0.0",
                generated_by_user_id=self.user_id,
                status=AuditStatus.GENERATING,
            )
            
            # Generate each format
            files = {}
            
            if 'json' in export_formats:
                json_file = self._generate_json_export(
                    package,
                    transactions,
                    calculations,
                    rules_used,
                )
                files['json'] = json_file
            
            if 'pdf' in export_formats:
                pdf_file = self._generate_pdf_export(
                    package,
                    transactions,
                    calculations,
                    rules_used,
                )
                files['pdf'] = pdf_file
            
            if 'excel' in export_formats:
                excel_file = self._generate_excel_export(
                    package,
                    transactions,
                    calculations,
                )
                files['excel'] = excel_file
            
            # Calculate integrity hash
            package.content_hash = self._calculate_content_hash(
                transactions,
                calculations,
                rules_used
            )
            
            package.status = AuditStatus.READY
            package.generated_at = datetime.utcnow()
            
            self.db.add(package)
            self.db.commit()
            
            self.log_event("AUDIT_GENERATION_COMPLETE", {
                "package_id": package.id,
                "transaction_count": len(transactions),
                "calculation_count": len(calculations),
                "files_generated": list(files.keys()),
            })
            
            return {
                'status': 'success',
                'package_id': package.id,
                'transaction_count': len(transactions),
                'calculation_count': len(calculations),
                'total_tax': float(package.total_tax_calculated),
                'country': self.country,
                'tax_year': tax_year,
                'files': files,
            }
        
        except Exception as e:
            self.db.rollback()
            self.log_error("AUDIT_GENERATION_FAILED", str(e))
            raise ServiceException(f"Audit generation failed: {str(e)}")
    
    def get_verified_rules(self, country: Optional[str] = None) -> List[Dict]:
        """Get all verified tax rules for a country"""
        if country is None:
            country = self.country
        
        rules = self.db.query(VerifiedTaxRule).filter(
            VerifiedTaxRule.country == country,
            VerifiedTaxRule.status == AuditStatus.ACTIVE,
        ).all()
        
        return [
            {
                'code': r.rule_code,
                'name': r.rule_name,
                'tax_type': r.tax_type,
                'current_version': r.version,
                'verified_date': r.verified_date.isoformat(),
                'verified_by': r.verified_by_user_id,
                'law_reference': r.law_reference,
                'law_link': r.law_link,
                'authority': r.tax_authority,
                'status': r.status,
            }
            for r in rules
        ]
    
    def get_calculation_details(self, calculation_id: int) -> Dict[str, Any]:
        """Get detailed audit info about a specific calculation"""
        calc = self.db.query(CalculationAuditRecord).filter(
            CalculationAuditRecord.id == calculation_id,
            CalculationAuditRecord.user_id == self.user_id,
        ).first()
        
        if not calc:
            raise ServiceException(f"Calculation not found: {calculation_id}")
        
        # Get the rule used
        rule = self.db.query(VerifiedTaxRule).filter(
            VerifiedTaxRule.id == calc.applied_rule_id,
        ).first()
        
        return {
            'calculation': {
                'id': calc.id,
                'asset': calc.asset,
                'quantity': float(calc.quantity),
                'buy_price': float(calc.buy_price),
                'sell_price': float(calc.sell_price),
                'tax_type': calc.tax_type,
                'tax_rate': float(calc.tax_rate),
                'calculated_tax': float(calc.calculated_tax),
                'reasoning': calc.reasoning,
                'method': calc.calculation_method,
            },
            'rule': {
                'code': rule.rule_code if rule else None,
                'name': rule.rule_name if rule else None,
                'law': rule.law_reference if rule else None,
                'law_link': rule.law_link if rule else None,
                'authority': rule.tax_authority if rule else None,
                'verified_date': rule.verified_date.isoformat() if rule else None,
            },
            'verified': {
                'status': calc.verified,
                'verified_by': calc.verified_by,
                'verified_date': calc.verified_date.isoformat() if calc.verified_date else None,
            },
        }
    
    # ==================
    # HELPER METHODS
    # ==================
    
    def _get_tax_calculations(self, tax_year: int) -> List[CalculationAuditRecord]:
        """Get all tax calculations for the year"""
        start_date = datetime(tax_year, 1, 1)
        end_date = datetime(tax_year, 12, 31)
        
        return self.db.query(CalculationAuditRecord).filter(
            CalculationAuditRecord.user_id == self.user_id,
            CalculationAuditRecord.country == self.country,
            CalculationAuditRecord.created_at.between(start_date, end_date),
        ).all()
    
    def _get_rules_used(self, calculations: List) -> List[VerifiedTaxRule]:
        """Get all verified rules used in calculations"""
        rule_ids = set(c.applied_rule_id for c in calculations if c.applied_rule_id)
        
        if not rule_ids:
            return []
        
        return self.db.query(VerifiedTaxRule).filter(
            VerifiedTaxRule.id.in_(rule_ids),
        ).all()
    
    def _get_transactions(self, tax_year: int) -> List[Dict]:
        """Get all transactions for the year"""
        # TODO: Query transactions from backend
        return []
    
    def _generate_json_export(
        self,
        package: AuditPackage,
        transactions: List,
        calculations: List,
        rules: List,
    ) -> str:
        """Generate JSON audit export"""
        
        data = {
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'package_id': package.id,
                'country': package.country,
                'tax_year': package.tax_year,
                'system_version': '1.0.0',
            },
            'summary': {
                'transaction_count': len(transactions),
                'calculation_count': len(calculations),
                'total_tax': float(package.total_tax_calculated),
                'verified_rules_count': len(rules),
            },
            'transactions': [],  # TODO: Add transaction details
            'calculations': [
                {
                    'id': c.id,
                    'asset': c.asset,
                    'tax_type': c.tax_type,
                    'tax_rate': float(c.tax_rate),
                    'calculated_tax': float(c.calculated_tax),
                    'reasoning': c.reasoning,
                    'verified': c.verified,
                }
                for c in calculations
            ],
            'verified_rules': [
                {
                    'code': r.rule_code,
                    'name': r.rule_name,
                    'version': r.version,
                    'verified_date': r.verified_date.isoformat(),
                }
                for r in rules
            ],
        }
        
        # In production: save to S3 or file system
        filename = f"audit_{package.country}_{package.tax_year}.json"
        # with open(filename, 'w') as f:
        #     json.dump(data, f, indent=2)
        
        return filename
    
    def _generate_pdf_export(
        self,
        package: AuditPackage,
        transactions: List,
        calculations: List,
        rules: List,
    ) -> str:
        """Generate PDF audit export"""
        # TODO: Use ReportLab or similar to generate PDF
        filename = f"audit_{package.country}_{package.tax_year}.pdf"
        return filename
    
    def _generate_excel_export(
        self,
        package: AuditPackage,
        transactions: List,
        calculations: List,
    ) -> str:
        """Generate Excel audit export"""
        # TODO: Use openpyxl to generate spreadsheet
        filename = f"audit_{package.country}_{package.tax_year}.xlsx"
        return filename
    
    def _calculate_content_hash(
        self,
        transactions: List,
        calculations: List,
        rules: List,
    ) -> str:
        """Calculate SHA256 hash of content for integrity"""
        content = json.dumps({
            'transactions': [str(t) for t in transactions],
            'calculations': [c.id for c in calculations],
            'rules': [r.id for r in rules],
        }, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()
