"""
Tax Jurisdictions API Endpoints
REST API for tax jurisdictions, calculations, and forms
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body

from app.core.db import get_db
from app.models.jurisdiction import Jurisdiction, TaxRule, TaxFormTemplate
from app.models.tax_profile import UserTaxProfile
from app.auth import get_current_user
from app.models.user import User

# New 12-country architecture
from app.countries.registries.country_registry import CountryRegistry


# Pydantic schemas for request/response
from pydantic import BaseModel
from datetime import datetime as dt


class CapitalGainInput(BaseModel):
    """Input for capital gain calculation"""
    buy_date: dt
    sell_date: dt
    buy_price: Decimal
    sell_price: Decimal
    quantity: Decimal
    fee: Decimal = Decimal("0")


class TaxCalculationRequest(BaseModel):
    """Request for tax calculation"""
    transaction_type: str  # 'capital_gains', 'income', 'vat'
    amount: Optional[Decimal] = None
    gains: Optional[List[CapitalGainInput]] = None
    calculation_method: str = "fifo"


class TaxCalculationResponse(BaseModel):
    """Response from tax calculation"""
    transaction_type: str
    amount: str
    tax_category: str
    tax_rate: str
    calculated_tax: str
    notes: Optional[str] = None


class JurisdictionResponse(BaseModel):
    """Jurisdiction information"""
    code: str
    name: str
    region: str
    currency: str
    currency_symbol: str
    tax_authority: str
    description: str
    is_active: bool


class TaxProfileCreateRequest(BaseModel):
    """Request to create/update tax profile"""
    jurisdiction_code: str
    tax_id: Optional[str] = None
    tax_payer_name: Optional[str] = None
    tax_address: Optional[str] = None
    preferred_export_formats: str = "PDF,CSV"
    tax_advisor_email: Optional[str] = None


class TaxProfileResponse(BaseModel):
    """Tax profile response"""
    id: str
    jurisdiction_code: str
    tax_id: Optional[str]
    tax_payer_name: Optional[str]
    preferred_export_formats: str
    fiscal_year_start_month: int
    fiscal_year_end_month: int
    created_at: dt


# Create router
router = APIRouter(prefix="/tax", tags=["tax"])


# ==================== JURISDICTION ENDPOINTS ====================

@router.get("/jurisdictions", response_model=List[JurisdictionResponse])
def get_jurisdictions(db: Session = Depends(get_db)):
    """
    Get all supported tax jurisdictions with metadata.
    Fetches real-time info from the CountryRegistry.
    """
    try:
        all_countries = CountryRegistry.list_all()
        jurisdictions = []
        
        for code, info in all_countries.items():
            jurisdictions.append(JurisdictionResponse(
                code=code,
                name=info["name"],
                region=info.get("region") or info.get("regions", ["Unknown"])[0],
                currency=info["currency"],
                currency_symbol=info.get("currency_symbol", "$"),
                tax_authority=info["tax_authority"],
                description=f"Standard tax rules for {info['name']} ({info['tax_authority']})",
                is_active=True
            ))
        
        return jurisdictions

    except Exception as e:
        return []


@router.get("/jurisdictions/{code}", response_model=JurisdictionResponse)
async def get_jurisdiction_info(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific jurisdiction information
    
    Args:
        code: Jurisdiction code
    """
    if not CountryRegistry.is_supported(code):
        raise HTTPException(status_code=404, detail=f"Jurisdiction {code} not supported")
        
    info = CountryRegistry.get_country(code).get_country_info()
    return {
        "code": code,
        "name": info["name"],
        "region": info["region"],
        "currency": info["currency"],
        "currency_symbol": info["currency_symbol"],
        "tax_authority": info["tax_authority"],
        "description": f"Standard tax rules for {info['name']} ({info['tax_authority']})",
        "is_active": True
    }


# ==================== TAX CALCULATION ENDPOINTS ====================

@router.post("/calculate/{code}", response_model=TaxCalculationResponse)
async def calculate_tax(
    code: str,
    request: TaxCalculationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate tax for a jurisdiction (supporting 12 countries)
    """
    try:
        calculator = CountryRegistry.get_calculator(code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        if request.transaction_type == "capital_gains" and request.gains:
            # For now, we sum up the total gains for the new calculator's interface
            # In a future update, we can pass individual transactions if needed
            total_gains = sum((g.sell_price - g.buy_price) * g.quantity - g.fee for g in request.gains)
            
            result = calculator.calculate_capital_gains_tax(float(total_gains))
            
            return TaxCalculationResponse(
                transaction_type="capital_gains",
                amount=str(result["capital_gains"]),
                tax_category=result["gain_type"],
                tax_rate=str(result["effective_rate"]),
                calculated_tax=str(result["capital_gains_tax"]),
                notes=f"Calculated for {code} using {request.calculation_method}"
            )
        
        elif request.transaction_type == "income" and request.amount:
            amount = float(request.amount)
            result = calculator.calculate_income_tax(amount)
            
            return TaxCalculationResponse(
                transaction_type="income",
                amount=str(result["gross_income"]),
                tax_category="ordinary_income",
                tax_rate=str(result["effective_rate"]),
                calculated_tax=str(result["income_tax"]),
                notes=f"Income tax for {code}"
            )
        
        elif request.transaction_type == "vat" and request.amount:
            amount = float(request.amount)
            vat_tax = calculator._calculate_vat(amount)
            
            return TaxCalculationResponse(
                transaction_type="vat",
                amount=str(amount),
                tax_category="vat",
                tax_rate="standard",
                calculated_tax=str(vat_tax),
                notes=f"VAT estimation for {code}"
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid request - provide either 'gains' for capital gains or 'amount' for income/vat"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# ==================== TAX PROFILE ENDPOINTS ====================

@router.post("/profile", response_model=TaxProfileResponse)
async def create_tax_profile(
    request: TaxProfileCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update user's tax profile for a jurisdiction
    
    Args:
        request: Tax profile details
    """
    # Get jurisdiction to validate (using 12-country model)
    try:
        if not CountryRegistry.is_supported(request.jurisdiction_code):
             raise ValueError(f"Jurisdiction {request.jurisdiction_code} not supported")
        jurisdiction_info = CountryRegistry.get_country(request.jurisdiction_code).get_country_info()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid jurisdiction code: {request.jurisdiction_code}")
    
    # Get or create jurisdiction record
    j = db.query(Jurisdiction).filter_by(code=request.jurisdiction_code).first()
    if not j:
        j = Jurisdiction(
            code=request.jurisdiction_code,
            name=jurisdiction_info["name"],
            region=jurisdiction_info["region"],
            vat_rate=0.0,  # Placeholder, would fetch from calculator if needed
            capital_gains_rate=0.0, # Placeholder
            reporting_currency=jurisdiction_info["currency"],
            filing_frequency="yearly",
            filing_authority=jurisdiction_info["tax_authority"]
        )
        db.add(j)
        db.flush()
    
    # Create or update profile
    profile = db.query(UserTaxProfile).filter_by(
        user_id=current_user.id,
        jurisdiction_id=j.id
    ).first()
    
    if not profile:
        profile = UserTaxProfile(
            user_id=current_user.id,
            jurisdiction_id=j.id
        )
        db.add(profile)
    
    # Update fields
    if request.tax_id:
        profile.tax_id = request.tax_id
    if request.tax_payer_name:
        profile.tax_payer_name = request.tax_payer_name
    if request.tax_address:
        profile.tax_address = request.tax_address
    if request.tax_advisor_email:
        profile.tax_advisor_email = request.tax_advisor_email
    
    profile.preferred_export_formats = request.preferred_export_formats
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    
    return TaxProfileResponse(
        id=str(profile.id),
        jurisdiction_code=j.code,
        tax_id=profile.tax_id,
        tax_payer_name=profile.tax_payer_name,
        preferred_export_formats=profile.preferred_export_formats,
        fiscal_year_start_month=profile.fiscal_year_start_month,
        fiscal_year_end_month=profile.fiscal_year_end_month,
        created_at=profile.created_at
    )


@router.get("/profile/{code}", response_model=TaxProfileResponse)
async def get_tax_profile(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's tax profile for a jurisdiction
    
    Args:
        code: Jurisdiction code
    """
    jurisdiction = db.query(Jurisdiction).filter_by(code=code).first()
    if not jurisdiction:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
    
    profile = db.query(UserTaxProfile).filter_by(
        user_id=current_user.id,
        jurisdiction_id=jurisdiction.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Tax profile not found")
    
    return TaxProfileResponse(
        id=str(profile.id),
        jurisdiction_code=code,
        tax_id=profile.tax_id,
        tax_payer_name=profile.tax_payer_name,
        preferred_export_formats=profile.preferred_export_formats,
        fiscal_year_start_month=profile.fiscal_year_start_month,
        fiscal_year_end_month=profile.fiscal_year_end_month,
        created_at=profile.created_at
    )


# ==================== FORM ENDPOINTS ====================

@router.get("/forms/{code}")
async def get_required_forms(
    code: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get required tax forms for a jurisdiction (supporting 12 countries)
    """
    if not CountryRegistry.is_supported(code):
        raise HTTPException(status_code=404, detail=f"Jurisdiction {code} not found")
        
    country = CountryRegistry.get_country(code)
    forms = country.get_tax_forms()
    
    return {
        "jurisdiction": code,
        "forms": {f_code: {"name": f.name, "deadline": f.deadline, "required": f.required} for f_code, f in forms.items()},
        "filing_deadline": country.filing_deadline_full
    }


@router.post("/forms/{code}/generate")
async def generate_tax_forms(
    code: str,
    export_format: str = Query("PDF", regex="^(PDF|XML|CSV|ODS)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Generate tax forms for a jurisdiction
    
    Args:
        code: Jurisdiction code
        export_format: Export format (PDF, XML, CSV, ODS)
    
    Returns:
        Form generation status/download link
    """
    if not CountryRegistry.is_supported(code):
        raise HTTPException(status_code=400, detail=f"Invalid jurisdiction code: {code}")
    
    # This is a placeholder - actual implementation would generate forms
    return {
        "status": "generating",
        "jurisdiction": code,
        "export_format": export_format,
        "message": "Form generation will be implemented in Phase 2"
    }


# ============================================================================
# Export Endpoints
# ============================================================================

@router.get("/export/formats")
def get_export_formats():
    """Get supported export formats"""
    return {
        "formats": ["pdf", "xml", "csv", "ods"],
        "default": "pdf"
    }

@router.post("/export/{code}/{year}")
def export_tax_report(
    code: str = Path(...),
    year: int = Path(...),
    request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate and download official tax report (PDF/XML/CSV)
    """
    from app.services.report_service import ReportService
    from app.services.analysis_service import get_latest_analysis_result
    
    format_type = request.get("format", "pdf").lower()
    
    # Get latest analysis results
    data = get_latest_analysis_result(db, current_user.id)
    if not data:
        data = {"pnl": {"realized_pnl_by_asset": {}, "lot_matches": []}} # Empty fallback for testing
        
    # Generate content
    if format_type == "pdf":
        return ReportService.generate_pdf_report(current_user, code, year, data)
    elif format_type == "xml":
        return ReportService.generate_xml_report(current_user, code, year, data)
    elif format_type == "csv":
        return ReportService.generate_turbotax_csv(data)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format_type}")

@router.post("/export/{code}/{year}/preview")
def preview_tax_report(
    code: str = Path(...),
    year: int = Path(...),
    request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get preview of the tax report"""
    format_type = request.get("format", "pdf").lower()
    return {
        "format": format_type,
        "filename": f"tax_report_{code}_{year}.{format_type}",
        "preview": f"Detailed tax report for {code} in {year}...",
        "size_bytes": 1024 * 45
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for tax engine"""
    jurisdiction_codes = CountryRegistry.list_codes()
    
    return {
        "status": "ok",
        "supported_jurisdictions": jurisdiction_codes,
        "jurisdiction_count": len(jurisdiction_codes),
        "export_formats": ["pdf", "xml", "csv", "ods"],
        "total_exporters": 4
    }
