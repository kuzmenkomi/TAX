"""
Tax Authority API Endpoints
REST API for tax filing, compliance, and status tracking
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel

from app.core.db import get_db
from app.auth import get_current_user
from app.models.user import User
from app.integrations.tax_authorities import (
    TaxAuthorityRegistry,
    TaxAuthorityManager,
    SubmissionStatus,
    ComplianceStatus,
)


# Pydantic models
class TaxFilingSubmissionRequest(BaseModel):
    """Request to submit tax filing"""
    jurisdiction_code: str
    tax_year: int
    filing_data: Dict[str, Any]
    is_amendment: bool = False


class FilingStatusResponse(BaseModel):
    """Response with filing status"""
    status: str
    submission_id: str
    message: str
    timestamp: str


class ComplianceCheckResponse(BaseModel):
    """Response with compliance check results"""
    status: str
    checks_performed: List[str]
    issues: List[str]
    warnings: List[str]


class JurisdictionMetadata(BaseModel):
    """Jurisdiction information"""
    code: str
    name: str
    authority: str
    tax_system: str
    filing_frequency: str
    deadline_month: int
    authentication: str
    primary_tax: str
    client_registered: bool


# Create router
router = APIRouter(prefix="/tax-authority", tags=["Tax Authorities"])
manager = TaxAuthorityManager()


# ==================== DISCOVERY ENDPOINTS ====================

@router.get("/jurisdictions", response_model=List[JurisdictionMetadata])
async def list_tax_jurisdictions(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of supported tax authorities
    
    Returns all 6 LatAm countries with metadata
    """
    return manager.get_all_jurisdictions_info()


@router.get("/jurisdictions/{code}", response_model=JurisdictionMetadata)
async def get_tax_jurisdiction(
    code: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific tax jurisdiction information"""
    try:
        info = manager.get_jurisdiction_info(code)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== FILING SUBMISSION ENDPOINTS ====================

@router.post("/submit-filing", response_model=FilingStatusResponse)
async def submit_tax_filing(
    request: TaxFilingSubmissionRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Submit tax filing to authority
    
    Args:
        request: Filing submission request with tax data
    
    Returns:
        Submission result with receipt/folio number
    """
    try:
        # Validate jurisdiction
        if not TaxAuthorityRegistry.is_supported(request.jurisdiction_code):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported jurisdiction: {request.jurisdiction_code}"
            )
        
        # Get or create client
        config = {
            "api_base_url": "https://tax-authority-api.example.com",
            "timeout": 30,
            **_get_jurisdiction_credentials(request.jurisdiction_code, current_user)
        }
        
        try:
            if not manager.has_client(request.jurisdiction_code):
                manager.register_client(request.jurisdiction_code, config)
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Authentication failed: {str(e)}"
            )
        
        client = manager.get_client(request.jurisdiction_code)
        
        # Submit filing
        result = client.submit_filing(
            request.tax_year,
            request.filing_data,
            request.is_amendment
        )
        
        return FilingStatusResponse(
            status=result.status.value,
            submission_id=result.submission_id or "",
            message=result.message,
            timestamp=result.timestamp.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filing submission error: {str(e)}")


@router.get("/filing-status/{jurisdiction_code}/{filing_id}")
async def get_filing_status(
    jurisdiction_code: str,
    filing_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of submitted filing
    
    Args:
        jurisdiction_code: Country code
        filing_id: Filing ID/folio from tax authority
    
    Returns:
        Current filing status and details
    """
    try:
        if not TaxAuthorityRegistry.is_supported(jurisdiction_code):
            raise HTTPException(status_code=400, detail="Unsupported jurisdiction")
        
        if not manager.has_client(jurisdiction_code):
            raise HTTPException(
                status_code=401,
                detail="Client not authenticated for this jurisdiction"
            )
        
        client = manager.get_client(jurisdiction_code)
        filing_info = client.get_filing_status(filing_id)
        
        return {
            "filing_id": filing_info.filing_id,
            "tax_year": filing_info.tax_year,
            "status": filing_info.status,
            "submitted_date": filing_info.submitted_date.isoformat() if filing_info.submitted_date else None,
            "amount_declared": str(filing_info.amount_declared),
            "amount_paid": str(filing_info.amount_paid),
            "balance_due": str(filing_info.balance_due),
            "deadline": filing_info.deadline.isoformat() if filing_info.deadline else None,
            "notes": filing_info.notes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status query error: {str(e)}")


# ==================== COMPLIANCE ENDPOINTS ====================

@router.post("/check-compliance/{jurisdiction_code}")
async def check_filing_compliance(
    jurisdiction_code: str,
    tax_year: int = Query(...),
    filing_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Check compliance with tax authority requirements
    
    Validates:
    - Document format and structure
    - Required fields
    - Tax calculation correctness
    - Threshold requirements
    - Deduction limits
    
    Args:
        jurisdiction_code: Country code
        tax_year: Year being filed
        filing_data: Filing data to validate
    
    Returns:
        ComplianceCheck results
    """
    try:
        if not TaxAuthorityRegistry.is_supported(jurisdiction_code):
            raise HTTPException(status_code=400, detail="Unsupported jurisdiction")
        
        config = {
            "api_base_url": "https://tax-authority-api.example.com",
            "timeout": 30,
            **_get_jurisdiction_credentials(jurisdiction_code, current_user)
        }
        
        if not manager.has_client(jurisdiction_code):
            try:
                manager.register_client(jurisdiction_code, config)
            except:
                pass  # Client registration not required for compliance check
        
        client = manager.get_client(jurisdiction_code)
        if not client:
            client = TaxAuthorityRegistry.get_client(jurisdiction_code, config)
        
        compliance = client.check_compliance(tax_year, filing_data)
        
        return ComplianceCheckResponse(
            status=compliance.status.value,
            checks_performed=compliance.checks_performed,
            issues=compliance.issues,
            warnings=compliance.warnings
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance check error: {str(e)}")


# ==================== FORMS ENDPOINTS ====================

@router.get("/required-forms/{jurisdiction_code}")
async def get_required_forms(
    jurisdiction_code: str,
    tax_year: int = Query(...),
    current_user: User = Depends(get_current_user)
):
    """
    Get required tax forms for jurisdiction and year
    
    Returns:
        List of forms with deadlines and requirements
    """
    try:
        if not TaxAuthorityRegistry.is_supported(jurisdiction_code):
            raise HTTPException(status_code=400, detail="Unsupported jurisdiction")
        
        config = _get_jurisdiction_credentials(jurisdiction_code, current_user)
        client = TaxAuthorityRegistry.get_client(jurisdiction_code, config)
        forms = client.get_filing_forms(tax_year)
        
        return {
            "jurisdiction": jurisdiction_code,
            "tax_year": tax_year,
            "forms": [
                {
                    **form,
                    "deadline": form["deadline"].isoformat() if hasattr(form.get("deadline"), "isoformat") else str(form.get("deadline"))
                }
                for form in forms
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forms retrieval error: {str(e)}")


# ==================== FILING SCHEDULE ENDPOINTS ====================

@router.get("/filing-schedule")
async def get_filing_schedule(
    current_user: User = Depends(get_current_user)
):
    """
    Get tax filing schedule for all jurisdictions
    
    Returns:
        Deadlines and filing requirements by country
    """
    schedule = []
    
    for code, metadata in TaxAuthorityRegistry.METADATA.items():
        schedule.append({
            "jurisdiction": code,
            "country": metadata["name"],
            "authority": metadata["authority"],
            "primary_tax": metadata["primary_tax"],
            "filing_frequency": metadata["filing_frequency"],
            "deadline_month": metadata["deadline_month"],
            "tax_system": metadata["tax_system"]
        })
    
    return {"filing_schedule": schedule}


# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """Health check for tax authority integration"""
    supported = TaxAuthorityRegistry.get_supported_jurisdictions()
    
    return {
        "status": "ok",
        "supported_jurisdictions": supported,
        "total_jurisdictions": len(supported),
        "jurisdictions_detail": {
            code: {
                "authority": TaxAuthorityRegistry.METADATA[code]["authority"],
                "primary_tax": TaxAuthorityRegistry.METADATA[code]["primary_tax"]
            }
            for code in supported
        }
    }


# ==================== HELPER FUNCTIONS ====================

def _get_jurisdiction_credentials(
    jurisdiction_code: str,
    user: User
) -> Dict[str, Any]:
    """
    Get stored credentials for jurisdiction
    
    In production: retrieve from secure storage
    For now: return template with placeholders
    """
    credentials_map = {
        "MX": {"rfc": "", "certificate_path": "", "private_key_path": ""},
        "BR": {"cpf": "", "password": ""},
        "AR": {"cuit": ""},
        "CO": {"nit": ""},
        "PE": {"ruc": ""},
        "CL": {"rut": ""},
    }
    
    return credentials_map.get(jurisdiction_code, {})


__all__ = ["router"]
