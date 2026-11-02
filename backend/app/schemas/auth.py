from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()-_+={}[]|:;<>,.?/~" for c in v):
            raise ValueError("Password must contain at least one special character")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    id: int
    email: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    user: UserInfo | None = None
    requires_two_factor: bool = False
    two_factor_token: str | None = None


class LoginTwoFactorCompleteRequest(BaseModel):
    two_factor_token: str
    code: str


class TwoFactorSetupBeginResponse(BaseModel):
    otpauth_uri: str
    issuer: str


class TwoFactorConfirmRequest(BaseModel):
    code: str


class TwoFactorDisableRequest(BaseModel):
    password: str
    code: str


class SupportImpersonationStartRequest(BaseModel):
    user_id: int | None = None
    email: EmailStr | None = None
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_len(cls, v: str) -> str:
        s = (v or "").strip()
        if len(s) < 8:
            raise ValueError("Reason must be at least 8 characters")
        return s


class TokenRefreshRequest(BaseModel):
    refresh_token: str | None = None


class MeResponse(BaseModel):
    id: int
    email: str
    is_email_verified: bool
    role: str = "user"
    two_factor_enabled: bool = False
    jurisdiction_code: str = "BR"
    jurisdiction_name: str = "Brazil"
    impersonation: dict | None = None
    allow_support_until: str | None = None
    support_access_active: bool = False


class SupportAccessUpdateRequest(BaseModel):
    allow: bool


class SupportAccessResponse(BaseModel):
    allow_support_until: str | None = None
    support_access_active: bool = False


class EmailVerifyRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()-_+={}[]|:;<>,.?/~" for c in v):
            raise ValueError("Password must contain at least one special character")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v
