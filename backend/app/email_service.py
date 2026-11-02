"""Email service for sending verification and password reset emails."""

from __future__ import annotations

import logging
from typing import Optional

import brevo

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Brevo."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.BREVO_API_KEY
        self.from_email = settings.BREVO_FROM_EMAIL
        self.frontend_url = settings.FRONTEND_URL

        if self.api_key:
            self.client = brevo.Brevo(api_key=self.api_key)
        else:
            self.client = None

    def is_configured(self) -> bool:
        return self.api_key is not None and self.client is not None

    def send_verification_email(
        self,
        recipient_email: str,
        verification_token: str,
        frontend_url: str | None = None,
    ) -> bool:
        frontend_url = frontend_url or self.frontend_url
        if not self.is_configured():
            verify_link = f"{frontend_url}/verify-email?token={verification_token}"
            logger.info("[DEV MODE] Verification email for %s: %s", recipient_email, verify_link)
            return True

        try:
            verify_link = f"{frontend_url}/verify-email?token={verification_token}"

            sender = brevo.SendTransacEmailRequestSender(
                email=self.from_email,
                name="Declairo",
            )
            to_item = brevo.SendTransacEmailRequestToItem(email=recipient_email)

            self.client.transactional_emails.send_transac_email(
                sender=sender,
                to=[to_item],
                subject="Confirm your Declairo email address",
                html_content=f"""
                <h2>Welcome to Declairo!</h2>
                <p>Please confirm your email address by clicking the link below:</p>
                <p>
                    <a href="{verify_link}" style="background-color: #10b981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Verify Email Address
                    </a>
                </p>
                <p>Or copy this link: <code>{verify_link}</code></p>
                <p>This link expires in 24 hours.</p>
                <p>If you didn't create this account, please ignore this email.</p>
                """,
            )
            logger.info("Verification email sent to %s", recipient_email)
            return True
        except Exception as exc:
            logger.exception("Failed to send verification email to %s: %s", recipient_email, exc)
            return False

    def send_password_reset_email(
        self,
        recipient_email: str,
        reset_token: str,
        frontend_url: str | None = None,
    ) -> bool:
        frontend_url = frontend_url or self.frontend_url
        if not self.is_configured():
            reset_link = f"{frontend_url}/password-reset?token={reset_token}"
            logger.info("[DEV MODE] Password reset email for %s: %s", recipient_email, reset_link)
            return True

        try:
            reset_link = f"{frontend_url}/password-reset?token={reset_token}"

            sender = brevo.SendTransacEmailRequestSender(
                email=self.from_email,
                name="Declairo",
            )
            to_item = brevo.SendTransacEmailRequestToItem(email=recipient_email)

            self.client.transactional_emails.send_transac_email(
                sender=sender,
                to=[to_item],
                subject="Reset your Declairo password",
                html_content=f"""
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your Declairo password.</p>
                <p>Click the link below to create a new password:</p>
                <p>
                    <a href="{reset_link}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy this link: <code>{reset_link}</code></p>
                <p><strong>This link expires in 1 hour.</strong></p>
                <p>If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
                """,
            )
            logger.info("Password reset email sent to %s", recipient_email)
            return True
        except Exception as exc:
            logger.exception("Failed to send password reset email to %s: %s", recipient_email, exc)
            return False


    def send_contact_email(
        self,
        sender_name: str,
        sender_email: str,
        message: str,
    ) -> bool:
        """Send a contact form submission to support@declairo.com."""
        support_email = "support@declairo.com"
        subject = f"[Contact Form] New message from {sender_name}"
        html_content = f"""
        <h2>New Contact Form Submission</h2>
        <table style="border-collapse:collapse;width:100%;font-family:sans-serif">
            <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Name</strong></td><td style="padding:8px;border:1px solid #ddd;">{sender_name}</td></tr>
            <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Email</strong></td><td style="padding:8px;border:1px solid #ddd;"><a href="mailto:{sender_email}">{sender_email}</a></td></tr>
        </table>
        <h3>Message:</h3>
        <p style="background:#f9f9f9;padding:16px;border-left:4px solid #10b981;white-space:pre-wrap">{message}</p>
        <hr/>
        <p style="color:#999;font-size:12px">Sent via Declairo Contact Form</p>
        """

        if not self.is_configured():
            logger.info(
                "[DEV MODE] Contact form from %s <%s>: %s",
                sender_name, sender_email, message[:100]
            )
            return True

        try:
            sender = brevo.SendTransacEmailRequestSender(
                email=self.from_email,
                name="Declairo Website",
            )
            to_item = brevo.SendTransacEmailRequestToItem(email=support_email)
            reply_to = brevo.SendTransacEmailRequestReplyTo(email=sender_email, name=sender_name)

            self.client.transactional_emails.send_transac_email(
                sender=sender,
                to=[to_item],
                reply_to=reply_to,
                subject=subject,
                html_content=html_content,
            )
            logger.info("Contact email forwarded from %s to %s", sender_email, support_email)
            return True
        except Exception as exc:
            logger.exception("Failed to send contact email from %s: %s", sender_email, exc)
            return False


_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
