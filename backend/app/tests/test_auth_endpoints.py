"""Tests for auth endpoints: register, login, logout, refresh."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.server import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def test_register_success(client):
    email = f"test_reg_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secure123!"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_register_weak_password(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "x@x.com", "password": "weak"},
    )
    assert r.status_code == 422


def test_login_wrong_password(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "Password1!"},
    )
    assert r.status_code == 401


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_register_sets_jurisdiction_from_cf_ipcountry(client):
    email = f"geo_reg_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secure123!"},
        headers={"CF-IPCountry": "US"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["jurisdiction_code"] == "US"
    assert body["jurisdiction_name"] == "United States"


def test_set_jurisdiction_persists(client):
    email = f"jur_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secure123!"},
        headers={"CF-IPCountry": "BR"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    put = client.put(
        "/api/v1/tax/jurisdiction",
        json={"jurisdiction_code": "MX"},
        headers=headers,
    )
    assert put.status_code == 200
    assert put.json()["jurisdiction_code"] == "MX"
    assert put.json()["country_locked"] is True

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["jurisdiction_code"] == "MX"
    assert me.json()["jurisdiction_name"] == "Mexico"


def test_full_flow(client):
    email = f"flow_test_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secure123!"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    r2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["email"] == email

    r3 = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "logged_out"

    r4 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r4.status_code == 401
