"""Multi-tenant isolation smoke tests (JWT must scope data to the authenticated user)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.server import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def _register(client: TestClient, password: str = "Secure123!") -> tuple[str, str]:
    email = f"iso_{uuid.uuid4().hex[:10]}@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return email, r.json()["access_token"]


def test_user_cannot_read_other_users_me_with_wrong_token(client):
    email_a, token_a = _register(client)
    email_b, token_b = _register(client)
    assert email_a != email_b

    me_as_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me_as_a.status_code == 200
    assert me_as_a.json()["email"] == email_a

    me_as_b_with_a_token = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me_as_b_with_a_token.json()["email"] == email_a

    me_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert me_b.json()["email"] == email_b
