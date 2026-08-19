"""Comprehensive Test Suite for B2B SaaS Control Plane & Multi-Tenancy."""
import asyncio
import os
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import settings
from app.models.database import db, DEFAULT_DEFAULT_ORG_ID
from app.security.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.security.api_key import generate_api_key, hash_key
from app.services.webhooks import WebhookDispatcher
from app.services.billing import billing_service

@pytest.fixture(scope="module", autouse=True)
def init_test_db():
    db._init_db()

@pytest.mark.asyncio
async def test_password_hashing():
    pw = "SuperSecretP@ssw0rd2026"
    h = hash_password(pw)
    assert h != pw
    assert verify_password(pw, h) is True
    assert verify_password("WrongPassword", h) is False

@pytest.mark.asyncio
async def test_jwt_token_lifecycle():
    user_id = "test-user-uuid-123"
    email = "ciso@enterprise.com"
    token = create_access_token(user_id=user_id, email=email, role="owner")
    
    token_data = decode_access_token(token)
    assert token_data.user_id == user_id
    assert token_data.email == email
    assert token_data.role == "owner"

@pytest.mark.asyncio
async def test_api_key_generation_and_hashing():
    raw_key, prefix, key_hash = generate_api_key("Production Ingestion Key")
    assert raw_key.startswith("aegis_live_")
    assert len(raw_key) > 30
    assert hash_key(raw_key) == key_hash

@pytest.mark.asyncio
async def test_user_registration_and_login_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = f"test_user_{int(asyncio.get_event_loop().time()*1000)}@cyberdefense.com"
        
        # 1. Register
        reg_payload = {
            "full_name": "Dr. Sarah Connor",
            "organization_name": "Cyberdyne Systems",
            "email": email,
            "password": "SecurePassword123!"
        }
        res = await ac.post("/api/auth/register", json=reg_payload)
        assert res.status_code == 200, res.text
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == email
        org_id = data["active_organization_id"]
        assert org_id is not None

        # 2. Login
        login_payload = {
            "email": email,
            "password": "SecurePassword123!"
        }
        res_login = await ac.post("/api/auth/login", json=login_payload)
        assert res_login.status_code == 200
        login_data = res_login.json()
        assert login_data["access_token"] is not None

@pytest.mark.asyncio
async def test_api_key_creation_and_proxy_guard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = f"dev_{int(asyncio.get_event_loop().time()*1000)}@corp.com"
        reg = await ac.post("/api/auth/register", json={
            "full_name": "Dev Lead",
            "organization_name": "Acme Corp",
            "email": email,
            "password": "Password123!"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create API Key
        key_res = await ac.post("/api/api-keys", json={"name": "Proxy Gateway Key"}, headers=headers)
        assert key_res.status_code == 200
        key_data = key_res.json()
        raw_key = key_data["raw_api_key"]
        assert raw_key.startswith("aegis_live_")

        # 2. Use API Key to invoke proxy
        proxy_headers = {"Authorization": f"Bearer {raw_key}"}
        proxy_res = await ac.post("/v1/chat/completions", json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello Aegis!"}]
        }, headers=proxy_headers)
        assert proxy_res.status_code == 200
        assert "choices" in proxy_res.json()

@pytest.mark.asyncio
async def test_webhook_hmac_signing():
    secret = "super_secret_webhook_signing_key_2026"
    payload = '{"event":"threat.blocked","risk_score":95.0}'
    sig = WebhookDispatcher.sign_payload(payload, secret)
    assert len(sig) == 64  # SHA-256 hex string

@pytest.mark.asyncio
async def test_billing_checkout_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = f"billing_user_{int(asyncio.get_event_loop().time()*1000)}@saas.com"
        reg = await ac.post("/api/auth/register", json={
            "full_name": "Billing Admin",
            "email": email,
            "password": "Password123!"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = await ac.post("/api/billing/checkout-session", json={"plan": "pro"}, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "checkout_url" in data
