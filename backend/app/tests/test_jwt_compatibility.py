"""Preserve existing HS256 sessions while rejecting modified/expired JWTs."""
import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi import HTTPException, Request

from app.auth import get_current_user
from app.core.config import get_settings
from app.services.oauth.manager import OAuthManager
from app.tests.test_service_workflows import store


def legacy_hs256_token(payload, key):
    def encode(value):
        return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=")
    body = encode({"typ": "JWT", "alg": "HS256"}) + b"." + encode(payload)
    signature = hmac.new(key.encode(), body, hashlib.sha256).digest()
    return (body + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode()


def request_for(token):
    return Request({"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})


def test_existing_hs256_token_still_authenticates_after_library_migration(store):
    db, user, _ = store
    token = legacy_hs256_token({"sub": user.email, "exp": int(time.time()) + 300}, get_settings().JWT_SECRET_KEY)
    assert get_current_user(request_for(token), db).id == user.id


@pytest.mark.parametrize("case", ["expired", "wrong_key", "pending_2fa"])
def test_invalid_or_incomplete_session_is_rejected(store, case):
    db, user, _ = store
    payload = {"sub": user.email, "exp": int(time.time()) + (300 if case != "expired" else -300)}
    if case == "pending_2fa":
        payload["tfa_pending"] = True
    key = get_settings().JWT_SECRET_KEY if case != "wrong_key" else "a-different-test-key-that-is-long-enough"
    token = legacy_hs256_token(payload, key)
    with pytest.raises(HTTPException) as error:
        get_current_user(request_for(token), db)
    assert error.value.status_code == 401


def test_oauth_state_is_bound_to_user_and_signed():
    manager = OAuthManager()
    state = manager.generate_state(123)
    assert manager.verify_state(state, 123)
    assert not manager.verify_state(state, 124)
    assert not manager.verify_state("invalid", 123)
    assert manager.get_provider("GITHUB").provider_name == "github"
    with pytest.raises(HTTPException):
        manager.get_provider("unknown")
