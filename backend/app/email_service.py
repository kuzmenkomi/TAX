"""Email service for sending verification and password reset emails."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import brevo

# Load environment variables from .env file
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


class EmailService:
    """Service for sending emails via Brevo."""

    def __init__(self):
        """Initialize Brevo client."""
        self.api_key = os.getenv("BREVO_API_KEY")
        self.from_email = os.getenv("BREVO_FROM_EMAIL", "noreply@declairo.com")
        
        if self.api_key:
            self.client = brevo.Brevo(api_key=self.api_key)
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Check if Brevo is properly configured."""
        return self.api_key is not None and self.client is not None

    def send_verification_email(
        self,
        recipient_email: str,
        verification_token: str,
        frontend_url: str = "http://localhost:5173",
    ) -> bool:
        """Send email verification link to user."""
        if not self.is_configured():
            # Development mode: print to console
            verify_link = f"{frontend_url}/verify-email?token={verification_token}"
            print(f"\n[DEV MODE] Verification email for {recipient_email}:")
            print(f"🔗 Click here: {verify_link}\n")
            return True

        try:
            verify_link = f"{frontend_url}/verify-email?token={verification_token}"
            
            sender = brevo.SendTransacEmailRequestSender(
                email=self.from_email,
                name="Declairo",
            )
            
            to_item = brevo.SendTransacEmailRequestToItem(
                email=recipient_email,
            )
            
            self.client.transactional_emails.send_transac_email(
                sender=sender,
                to=[to_item],
                subject="Confirm your Declairo email address",
                html_content=f"""
                <h2>Welcome to Declairo! 🎉</h2>
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
            print(f"✅ Verification email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send verification email: {str(e)}")
            return False

    def send_password_reset_email(
        self,
        recipient_email: str,
        reset_token: str,
        frontend_url: str = "http://localhost:5173",
    ) -> bool:
        """Send password reset link to user."""
        if not self.is_configured():
            # Development mode: print to console
            reset_link = f"{frontend_url}/password-reset?token={reset_token}"
            print(f"\n[DEV MODE] Password reset email for {recipient_email}:")
            print(f"🔗 Click here: {reset_link}\n")
            return True

        try:
            reset_link = f"{frontend_url}/password-reset?token={reset_token}"
            
            sender = brevo.SendTransacEmailRequestSender(
                email=self.from_email,
                name="Declairo",
            )
            
            to_item = brevo.SendTransacEmailRequestToItem(
                email=recipient_email,
            )
            
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
            print(f"✅ Password reset email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send password reset email: {str(e)}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
