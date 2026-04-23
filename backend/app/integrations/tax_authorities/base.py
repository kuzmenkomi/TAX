"""
Base Tax Authority API Client
Abstract base class for all tax authority integrations
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SubmissionStatus(str, Enum):
    """Tax filing submission status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    AMENDED = "amended"
    PROCESSING = "processing"
    ERROR = "error"


class ComplianceStatus(str, Enum):
    """Compliance check status"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"


@dataclass
class SubmissionResult:
    """Tax filing submission result"""
    status: SubmissionStatus
    submission_id: Optional[str]
    timestamp: datetime
    message: str
    errors: List[str] = None
    warnings: List[str] = None
    receipt_number: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class ComplianceCheck:
    """Compliance validation result"""
    status: ComplianceStatus
    checks_performed: List[str]
    issues: List[str] = None
    warnings: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.warnings is None:
            self.warnings = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class TaxFilingInfo:
    """Tax filing information from authority"""
    filing_id: str
    tax_year: int
    status: str
    submitted_date: Optional[datetime]
    amount_declared: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    deadline: Optional[datetime]
    notes: Optional[str]


class BaseTaxAuthorityClient(ABC):
    """
    Abstract base class for tax authority API clients
    
    Each country implements:
    - Authentication (OAuth, certificate, API key, etc.)
    - Filing submission
    - Status tracking
    - Amendment/correction
    - Compliance checking
    """
    
    def __init__(self, jurisdiction_code: str, config: Dict[str, Any]):
        """
        Initialize tax authority client
        
        Args:
            jurisdiction_code: Country code (MX, BR, AR, CO, PE, CL)
            config: Configuration dict with auth credentials, endpoints, etc.
        """
        self.jurisdiction_code = jurisdiction_code
        self.config = config
        self._authenticated = False
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with tax authority
        
        Raises:
            Exception: Authentication failed
        
        Returns:
            bool: True if authenticated
        """
        pass
    
    @abstractmethod
    def submit_filing(
        self,
        tax_year: int,
        filing_data: Dict[str, Any],
        is_amendment: bool = False
    ) -> SubmissionResult:
        """
        Submit tax filing to authority
        
        Args:
            tax_year: Year being filed for
            filing_data: Complete filing data (transactions, calculations, etc.)
            is_amendment: Whether this is an amendment to existing filing
        
        Returns:
            SubmissionResult with status and submission ID
        """
        pass
    
    @abstractmethod
    def get_filing_status(self, filing_id: str) -> TaxFilingInfo:
        """
        Get status of submitted filing
        
        Args:
            filing_id: Filing ID from authority
        
        Returns:
            TaxFilingInfo with status and details
        """
        pass
    
    @abstractmethod
    def check_compliance(
        self,
        tax_year: int,
        filing_data: Dict[str, Any]
    ) -> ComplianceCheck:
        """
        Check compliance before submission
        
        Args:
            tax_year: Tax year to check
            filing_data: Filing data to validate
        
        Returns:
            ComplianceCheck with results and any issues
        """
        pass
    
    @abstractmethod
    def get_filing_forms(self, tax_year: int) -> List[Dict[str, Any]]:
        """
        Get list of required forms for tax year
        
        Args:
            tax_year: Tax year
        
        Returns:
            List of form definitions needed
        """
        pass
    
    # ==================== COMMON METHODS ====================
    
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return self._authenticated
    
    def get_jurisdiction_code(self) -> str:
        """Get jurisdiction code"""
        return self.jurisdiction_code
    
    def get_api_base_url(self) -> str:
        """Get API base URL from config"""
        return self.config.get("api_base_url", "")
    
    def get_timeout(self) -> int:
        """Get request timeout in seconds"""
        return self.config.get("timeout", 30)
    
    def validate_filing_data(self, filing_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate filing data for required fields
        
        Args:
            filing_data: Filing data to validate
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ["tax_year", "taxpayer_id", "transactions", "tax_summary"]
        for field in required_fields:
            if field not in filing_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate tax year
        if "tax_year" in filing_data:
            tax_year = filing_data["tax_year"]
            if not isinstance(tax_year, int) or tax_year < 1900 or tax_year > datetime.now().year:
                errors.append(f"Invalid tax year: {tax_year}")
        
        # Validate transactions
        if "transactions" in filing_data:
            transactions = filing_data["transactions"]
            if not isinstance(transactions, list):
                errors.append("Transactions must be a list")
            elif len(transactions) == 0:
                errors.append("No transactions provided")
        
        return len(errors) == 0, errors
    
    def format_currency(self, amount: Decimal, decimals: int = 2) -> str:
        """
        Format currency amount for filing
        
        Args:
            amount: Amount to format
            decimals: Number of decimal places
        
        Returns:
            Formatted string
        """
        return f"{Decimal(str(amount)):.{decimals}f}"
    
    def format_date(self, date: datetime, format_str: str = "%Y-%m-%d") -> str:
        """
        Format date for filing
        
        Args:
            date: Date to format
            format_str: Format string
        
        Returns:
            Formatted date string
        """
        if isinstance(date, str):
            return date
        return date.strftime(format_str)
    
    def handle_api_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Handle and log API error
        
        Args:
            error: Exception that occurred
            context: Context describing what was attempted
        
        Returns:
            Dict with error information
        """
        error_msg = str(error)
        return {
            "error": error_msg,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "jurisdiction": self.jurisdiction_code
        }
    
    def get_error_message_for_code(self, error_code: str) -> str:
        """
        Get human-readable error message for error code
        
        Args:
            error_code: Error code from API
        
        Returns:
            Human-readable message
        """
        # Base error codes - override in subclasses for jurisdiction-specific
        error_messages = {
            "AUTH_FAILED": "Authentication failed. Check credentials.",
            "INVALID_FORMAT": "Filing format is invalid.",
            "DUPLICATE_FILING": "Filing already submitted for this period.",
            "INVALID_DATA": "Filing data contains errors.",
            "NETWORK_ERROR": "Network error. Please try again.",
            "TIMEOUT": "Request timeout. Please try again.",
            "NOT_FOUND": "Filing not found.",
            "SERVER_ERROR": "Tax authority server error. Try again later.",
        }
        return error_messages.get(error_code, f"Unknown error: {error_code}")


__all__ = [
    "BaseTaxAuthorityClient",
    "SubmissionStatus",
    "ComplianceStatus",
    "SubmissionResult",
    "ComplianceCheck",
    "TaxFilingInfo",
]
