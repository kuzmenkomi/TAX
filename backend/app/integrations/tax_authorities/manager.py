"""
Tax Authority Client Manager
Registry and factory for tax authority clients
"""
from typing import Dict, Type, Optional, Any
from .base import BaseTaxAuthorityClient
from .sat_mexico import SATClient
from .receita_brazil import ReceitaClient
from .afip_argentina import AFIPClient
from .dian_sunat_sii import DIANClient, SUNATClient, SIIClient


class TaxAuthorityRegistry:
    """Registry of tax authority clients for all jurisdictions"""
    
    # Mapping of jurisdiction codes to client classes
    CLIENTS: Dict[str, Type[BaseTaxAuthorityClient]] = {
        "MX": SATClient,
        "BR": ReceitaClient,
        "AR": AFIPClient,
        "CO": DIANClient,
        "PE": SUNATClient,
        "CL": SIIClient,
    }
    
    # Metadata for each jurisdiction
    METADATA = {
        "MX": {
            "name": "Mexico",
            "authority": "SAT (Servicio de Administración Tributaria)",
            "tax_system": "Progressive ISR (1.92% - 35%)",
            "filing_frequency": "Yearly",
            "deadline_month": 4,
            "authentication": "X.509 Certificate + RFC",
            "primary_tax": "IRPF"
        },
        "BR": {
            "name": "Brazil",
            "authority": "Receita Federal do Brasil",
            "tax_system": "Progressive IRPF (up to 27.5%)",
            "filing_frequency": "Yearly + Monthly (CARNÊ-LEÃO)",
            "deadline_month": 5,
            "authentication": "CPF + eCAC Portal",
            "primary_tax": "IRPF"
        },
        "AR": {
            "name": "Argentina",
            "authority": "AFIP (Administración Federal de Ingresos Públicos)",
            "tax_system": "Ganancias (5% - 35%) with CER adjustment",
            "filing_frequency": "Yearly",
            "deadline_month": 5,
            "authentication": "CUIT Certificate",
            "primary_tax": "Ganancias"
        },
        "CO": {
            "name": "Colombia",
            "authority": "DIAN (Dirección de Impuestos y Aduanas Nacionales)",
            "tax_system": "Renta (0% - 37%) UVT-based",
            "filing_frequency": "Yearly",
            "deadline_month": 4,
            "authentication": "NIT + Digital Certificate",
            "primary_tax": "Renta"
        },
        "PE": {
            "name": "Peru",
            "authority": "SUNAT (Superintendencia Nacional de Aduanas)",
            "tax_system": "IR (30% flat for most)",
            "filing_frequency": "Yearly",
            "deadline_month": 4,
            "authentication": "RUC + SOL Portal",
            "primary_tax": "IR"
        },
        "CL": {
            "name": "Chile",
            "authority": "SII (Servicio de Impuestos Internos)",
            "tax_system": "IGC (5% - 40%) UTA-based",
            "filing_frequency": "Yearly",
            "deadline_month": 4,
            "authentication": "RUT Digital Certificate",
            "primary_tax": "IGC"
        }
    }
    
    @classmethod
    def get_client(
        cls,
        jurisdiction_code: str,
        config: Dict[str, Any]
    ) -> BaseTaxAuthorityClient:
        """
        Get tax authority client for jurisdiction
        
        Args:
            jurisdiction_code: Country code (MX, BR, AR, CO, PE, CL)
            config: Configuration dict with credentials
        
        Returns:
            Initialized tax authority client
        
        Raises:
            ValueError: Invalid jurisdiction code
        """
        if jurisdiction_code not in cls.CLIENTS:
            supported = ", ".join(cls.CLIENTS.keys())
            raise ValueError(
                f"Unsupported jurisdiction: {jurisdiction_code}\n"
                f"Supported jurisdictions: {supported}"
            )
        
        client_class = cls.CLIENTS[jurisdiction_code]
        return client_class(config)
    
    @classmethod
    def is_supported(cls, jurisdiction_code: str) -> bool:
        """Check if jurisdiction is supported"""
        return jurisdiction_code in cls.CLIENTS
    
    @classmethod
    def get_supported_jurisdictions(cls) -> list:
        """Get list of supported jurisdiction codes"""
        return list(cls.CLIENTS.keys())
    
    @classmethod
    def get_metadata(cls, jurisdiction_code: str) -> Optional[Dict[str, Any]]:
        """Get metadata for jurisdiction"""
        return cls.METADATA.get(jurisdiction_code)
    
    @classmethod
    def get_all_metadata(cls) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all jurisdictions"""
        return cls.METADATA


class TaxAuthorityManager:
    """
    Manager for tax authority operations across jurisdictions
    
    Provides unified interface for:
    - Filing submissions
    - Status tracking
    - Compliance checking
    - Form requirements
    """
    
    def __init__(self):
        """Initialize manager"""
        self.clients: Dict[str, BaseTaxAuthorityClient] = {}
    
    def register_client(
        self,
        jurisdiction_code: str,
        config: Dict[str, Any]
    ) -> BaseTaxAuthorityClient:
        """
        Register and initialize tax authority client
        
        Args:
            jurisdiction_code: Country code
            config: Client configuration (credentials, endpoints, etc.)
        
        Returns:
            Initialized and authenticated client
        """
        if jurisdiction_code in self.clients:
            return self.clients[jurisdiction_code]
        
        # Get client class from registry
        client = TaxAuthorityRegistry.get_client(jurisdiction_code, config)
        
        # Authenticate
        if not client.authenticate():
            raise Exception(f"Failed to authenticate with {jurisdiction_code} tax authority")
        
        # Cache client
        self.clients[jurisdiction_code] = client
        return client
    
    def get_client(self, jurisdiction_code: str) -> Optional[BaseTaxAuthorityClient]:
        """Get registered client for jurisdiction"""
        return self.clients.get(jurisdiction_code)
    
    def has_client(self, jurisdiction_code: str) -> bool:
        """Check if client is registered"""
        return jurisdiction_code in self.clients
    
    def get_jurisdiction_info(self, jurisdiction_code: str) -> Dict[str, Any]:
        """Get jurisdiction information and metadata"""
        metadata = TaxAuthorityRegistry.get_metadata(jurisdiction_code)
        if not metadata:
            raise ValueError(f"Unknown jurisdiction: {jurisdiction_code}")
        
        return {
            "code": jurisdiction_code,
            **metadata,
            "client_registered": self.has_client(jurisdiction_code)
        }
    
    def get_all_jurisdictions_info(self) -> list:
        """Get information for all supported jurisdictions"""
        return [
            {
                "code": code,
                **metadata,
                "client_registered": self.has_client(code)
            }
            for code, metadata in TaxAuthorityRegistry.get_all_metadata().items()
        ]


__all__ = [
    "TaxAuthorityRegistry",
    "TaxAuthorityManager",
]
