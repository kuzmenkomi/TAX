"""Subscription lifecycle and real TOTP verification with external billing mocked."""
from types import SimpleNamespace
from unittest.mock import Mock

import pyotp
import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import Subscription
from app.services import stripe_service as billing, two_factor_service as totp
from app.tests.test_service_workflows import store


def test_totp_setup_confirmation_and_disable_require_valid_proofs(store):
    db, user, _ = store
    user.hashed_password = hash_password("Password123!")
    db.commit()
    with pytest.raises(HTTPException):
        totp.confirm_totp_setup(db, user, "000000")
    secret, uri = totp.begin_totp_setup(db, user, issuer="Declairo")
    assert uri.startswith("otpauth://totp/")
    assert user.totp_pending and not user.totp_enabled
    assert user.totp_secret_encrypted != secret
    totp.confirm_totp_setup(db, user, pyotp.TOTP(secret).now())
    assert user.totp_enabled and not user.totp_pending
    assert totp.verify_user_totp_code(user, pyotp.TOTP(secret).now())
    with pytest.raises(HTTPException):
        totp.begin_totp_setup(db, user, issuer="Declairo")
    with pytest.raises(HTTPException):
        totp.disable_totp(db, user, "incorrect", pyotp.TOTP(secret).now())
    totp.disable_totp(db, user, "Password123!", pyotp.TOTP(secret).now())
    assert not user.totp_enabled and user.totp_secret_encrypted is None
    assert not totp.verify_user_totp_code(user, "000000")


def test_cancel_totp_setup_removes_pending_secret(store):
    db, user, _ = store
    totp.begin_totp_setup(db, user, issuer="Declairo")
    totp.cancel_totp_setup(db, user)
    assert not user.totp_pending and user.totp_secret_encrypted is None


@pytest.fixture
def stripe_settings(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "demo-only")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "demo-only-signing-secret")
    monkeypatch.setattr(settings, "STRIPE_PRICE_PRO", "price_demo_pro")
    monkeypatch.setattr(settings, "STRIPE_PRICE_BUSINESS", "price_demo_business")
    return settings


@pytest.mark.parametrize("plan,price", [("pro", "price_demo_pro"), ("business", "price_demo_business")])
def test_checkout_reuses_customer_and_selects_configured_price(store, stripe_settings, monkeypatch, plan, price):
    db, user, _ = store
    create_customer = Mock(return_value=SimpleNamespace(id="customer-demo"))
    create_checkout = Mock(return_value=SimpleNamespace(url="https://checkout.example.com/demo"))
    monkeypatch.setattr(billing.stripe.Customer, "create", create_customer)
    monkeypatch.setattr(billing.stripe.checkout.Session, "create", create_checkout)
    for _ in range(2):
        assert billing.create_checkout_session(db, user, plan, "https://example.com/success", "https://example.com/cancel").endswith("/demo")
    create_customer.assert_called_once()
    assert create_checkout.call_args.kwargs["line_items"] == [{"price": price, "quantity": 1}]
    assert db.query(Subscription).one().stripe_customer_id == "customer-demo"
    with pytest.raises(ValueError, match="No Stripe price"):
        billing.create_checkout_session(db, user, "unknown", "success", "cancel")


@pytest.mark.parametrize("event_type,expected_plan,expected_status", [
    ("checkout.session.completed", "pro", "active"),
    ("customer.subscription.updated", "free", "past_due"),
    ("customer.subscription.deleted", "free", "canceled"),
])
def test_signed_webhook_updates_subscription(store, stripe_settings, monkeypatch, event_type, expected_plan, expected_status):
    db, user, _ = store
    sub = Subscription(user_id=user.id, plan="free", status="active")
    db.add(sub)
    db.commit()
    obj = SimpleNamespace(metadata={"user_id": user.id, "plan": "pro"}, subscription="sub-demo", status="past_due")
    event = SimpleNamespace(type=event_type, data=SimpleNamespace(object=obj))
    verify = Mock(return_value=event)
    monkeypatch.setattr(billing.stripe.Webhook, "construct_event", verify)
    assert billing.handle_webhook_event(db, b"{}", "demo-signature") == {"status": "success"}
    assert sub.plan == expected_plan and sub.status == expected_status
    verify.assert_called_once_with(b"{}", "demo-signature", stripe_settings.STRIPE_WEBHOOK_SECRET)


def test_unsigned_or_invalid_webhook_cannot_modify_subscription(store, stripe_settings, monkeypatch):
    db, user, _ = store
    with pytest.raises(ValueError, match="Missing"):
        billing.handle_webhook_event(db, b"{}", None)
    invalid = billing.stripe.SignatureVerificationError("invalid", "demo-signature")
    monkeypatch.setattr(billing.stripe.Webhook, "construct_event", Mock(side_effect=invalid))
    with pytest.raises(ValueError, match="Invalid webhook signature"):
        billing.handle_webhook_event(db, b"{}", "demo-signature")
    assert db.query(Subscription).count() == 0
