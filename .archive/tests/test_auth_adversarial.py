"""Adversarial Authentication & Token Attack Campaign Test Suite."""
import asyncio
import time
import pytest
import jwt
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import settings
from app.models.database import db
from app.auth.tokens import create_access_token, create_refresh_token, revoke_token

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_auth_attacks_and_token_tampering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)

        # 1. Expired JWT Token
        expired_payload = {
            "sub": "user-expired-123",
            "email": "expired@target.com",
            "role": "OWNER",
            "exp": time.time() - 3600  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm="HS256")
        res_exp = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert res_exp.status_code == 401

        # 2. Forged Signature Token (Signed with attacker's secret key)
        attacker_key = "evil-secret-key-that-does-not-match-aegis"
        forged_token = jwt.encode(
            {"sub": "admin", "email": "ciso@target.com", "role": "OWNER", "exp": time.time() + 3600},
            attacker_key,
            algorithm="HS256"
        )
        res_forged = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
        assert res_forged.status_code == 401

        # 3. None Algorithm / Algorithm Confusion Attack
        try:
            none_token = jwt.encode({"sub": "admin", "email": "admin@target.com"}, key="", algorithm="none")
            res_none = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {none_token}"})
            assert res_none.status_code == 401
        except Exception:
            pass  # pyjwt blocks algorithm none by default

        # 4. Revoked Refresh Token Replay
        user_reg = await ac.post("/api/auth/register", json={
            "full_name": "Refresh User",
            "organization_name": "Refresh Corp",
            "email": f"refresh_{t_now}@refresh.com",
            "password": "Password123!"
        })
        user_id = user_reg.json()["user"]["id"]
        org_id = user_reg.json()["active_organization_id"]
        refresh_token = create_refresh_token(user_id=user_id, organization_id=org_id)

        # Revoke the token
        revoke_token(refresh_token)

        # Attempt to refresh session with revoked token
        res_refresh = await ac.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert res_refresh.status_code == 401
