from __future__ import annotations

from fastapi import APIRouter

from app.routers.v1.analysis import router as analysis_router
from app.routers.v1.auth import router as auth_router
from app.routers.v1.social_auth import router as social_auth_router
from app.routers.v1.defi import router as defi_router
from app.routers.v1.exchange import router as exchange_router
from app.routers.v1.exports import router as exports_router
from app.routers.v1.phase10 import router as phase10_router
from app.routers.v1.portfolio import router as portfolio_router
from app.routers.v1.sync import router as sync_router
from app.routers.v1.sync_settings import router as sync_settings_router
from app.routers.v1.tax_jurisdictions import router as tax_jurisdictions_router
from app.routers.v1.tax_authorities import router as tax_authorities_router
from app.routers.v1.wallet import router as wallet_router
from app.routers.v1.tlh import router as tlh_router
from app.routers.v1.banking import router as banking_router
from app.routers.v1.reconciliation import router as reconciliation_router
from app.routers.v1.ai import router as ai_router
from app.routers.v1.sse import router as sse_router
from app.routers.v1.plugins import router as plugins_router
from app.routers.v1.oauth import router as oauth_router
from app.routers.v1.accounting import router as accounting_router
from app.routers.v1.billing import router as billing_router
from app.routers.v1.bank_import import router as bank_import_router
from app.routers.v1.analytics import router as analytics_router
from app.routers.v1.support import router as support_router
from app.routers.v1.two_factor import router as two_factor_router
from app.routers.v1.support_impersonation import router as support_impersonation_router

router = APIRouter()
router.include_router(social_auth_router)  # Social OAuth — must come before auth_router
router.include_router(auth_router)
router.include_router(two_factor_router)
router.include_router(support_impersonation_router)
router.include_router(portfolio_router)
router.include_router(exchange_router)
router.include_router(wallet_router)
router.include_router(sync_router)
router.include_router(sync_settings_router)
router.include_router(defi_router)
router.include_router(exports_router)
router.include_router(phase10_router)
router.include_router(analysis_router)
router.include_router(tax_jurisdictions_router)
router.include_router(tax_authorities_router)
router.include_router(tlh_router)
router.include_router(banking_router)
router.include_router(reconciliation_router)
router.include_router(ai_router)
router.include_router(sse_router)
router.include_router(plugins_router)
router.include_router(oauth_router)
router.include_router(accounting_router)
router.include_router(billing_router)
router.include_router(bank_import_router)
router.include_router(analytics_router)
router.include_router(support_router)

__all__ = ["router"]
