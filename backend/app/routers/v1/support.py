from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
import logging
from app.auth import get_current_user
from app.models import User
from app.email_service import get_email_service

router = APIRouter(prefix="/support", tags=["Support"])
logger = logging.getLogger(__name__)


# ── Public Contact Form ────────────────────────────────────────────────────────

class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    message: str


@router.post("/contact", summary="Submit a contact form message (public)")
async def submit_contact_form(payload: ContactFormRequest):
    """
    Receives a contact form submission from the landing page and
    forwards it to support@declairo.com via email.
    No authentication required.
    """
    if len(payload.message.strip()) < 10:
        raise HTTPException(status_code=422, detail="Message is too short.")

    email_service = get_email_service()
    sent = email_service.send_contact_email(
        sender_name=payload.name.strip(),
        sender_email=payload.email,
        message=payload.message.strip(),
    )

    if not sent:
        raise HTTPException(
            status_code=500,
            detail="Could not send your message. Please try again later."
        )

    return {"status": "ok", "message": "Your message has been sent. We'll reply within 24 hours."}


# ── Authenticated Support Ticket ───────────────────────────────────────────────

class SupportTicket(BaseModel):
    subject: str
    message: str
    category: str = "general"  # general, tax_question, bug, billing


@router.post("/ticket", summary="Create a support ticket (authenticated)")
async def create_support_ticket(
    ticket: SupportTicket,
    current_user: User = Depends(get_current_user)
):
    """
    Creates a support ticket from an authenticated user and notifies support.
    """
    try:
        admin_email = "support@declairo.com"
        content = (
            f"User: {current_user.email}\n"
            f"Category: {ticket.category}\n"
            f"Subject: {ticket.subject}\n\n"
            f"{ticket.message}"
        )
        logger.info(
            "SUPPORT_TICKET: %s - %s | notify=%s | body_len=%s",
            current_user.email,
            ticket.subject,
            admin_email,
            len(content),
        )

        email_service = get_email_service()
        email_service.send_contact_email(
            sender_name=current_user.email,
            sender_email=current_user.email,
            message=f"[{ticket.category.upper()}] {ticket.subject}\n\n{ticket.message}",
        )

        return {"status": "ok", "message": "Ticket received. Our team will contact you soon."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Support ticket failed: {e}")
        raise HTTPException(status_code=500, detail="Could not send ticket")
