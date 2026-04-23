"""
Tax Authority Clients Package
Tax filing, compliance checking, and status tracking for all LatAm jurisdictions
"""

from .base import (
    BaseTaxAuthorityClient,
    SubmissionStatus,
    ComplianceStatus,
    SubmissionResult,
    ComplianceCheck,
    TaxFilingInfo,
)

from .sat_mexico import SATClient
from .receita_brazil import ReceitaClient
from .afip_argentina import AFIPClient
from .dian_sunat_sii import DIANClient, SUNATClient, SIIClient

from .manager import TaxAuthorityRegistry, TaxAuthorityManager

__all__ = [
    # Base classes
    "BaseTaxAuthorityClient",
    "SubmissionStatus",
    "ComplianceStatus",
    "SubmissionResult",
    "ComplianceCheck",
    "TaxFilingInfo",
    
    # Country clients
    "SATClient",
    "ReceitaClient",
    "AFIPClient",
    "DIANClient",
    "SUNATClient",
    "SIIClient",
    
    # Manager
    "TaxAuthorityRegistry",
    "TaxAuthorityManager",
]
