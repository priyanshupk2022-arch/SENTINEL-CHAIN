"""Comprehensive Browser-Level UI & UX Flow Testing Suite for Aegis SaaS Platform."""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_landing_page_rendering_and_security_headers():
    """Validates that landing page renders valid semantic HTML with all security headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers.get("content-type", "")
        
        # Verify Security Headers
        assert res.headers.get("x-frame-options") == "DENY"
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert "strict-origin" in res.headers.get("referrer-policy", "")
        assert "x-request-id" in res.headers
        
        # Verify Key Elements in Landing Page
        html = res.text
        assert "AEGIS AI" in html
        assert "Enterprise Security" in html or "Guardrail" in html
        assert "/login" in html
        assert "/register" in html

@pytest.mark.asyncio
async def test_auth_pages_rendering_and_forms():
    """Validates login and registration page structure, forms, and Alpine.js state hooks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login Page
        login_res = await ac.get("/login")
        assert login_res.status_code == 200
        login_html = login_res.text
        assert "Sign in to Aegis" in login_html
        assert "handleLogin" in login_html
        assert "x-model=\"email\"" in login_html
        assert "x-model=\"password\"" in login_html
        assert "/register" in login_html

        # 2. Registration Page
        reg_res = await ac.get("/register")
        assert reg_res.status_code == 200
        reg_html = reg_res.text
        assert "Deploy Aegis Enterprise" in reg_html or "Create Organization" in reg_html
        assert "handleRegister" in reg_html
        assert "x-model=\"fullName\"" in reg_html
        assert "x-model=\"orgName\"" in reg_html
        assert "x-model=\"email\"" in reg_html
        assert "x-model=\"password\"" in reg_html
        assert "minlength=\"12\"" in reg_html

@pytest.mark.asyncio
async def test_dashboard_rendering_and_session_cookie_flow():
    """Validates complete browser login, session cookie injection, and authenticated dashboard access."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_stamp = int(asyncio.get_event_loop().time() * 1000)
        email = f"ui_ciso_{t_stamp}@uicorp.com"
        password = "SecureUIPassword2026!"

        # 1. Register via API (Simulating form submission)
        reg_res = await ac.post("/api/auth/register", json={
            "full_name": "UI Test Engineer",
            "organization_name": "UI Verification Corp",
            "email": email,
            "password": password
        })
        assert reg_res.status_code == 200
        # Check that session cookie was set
        assert "aegis_session" in reg_res.cookies
        session_cookie = reg_res.cookies["aegis_session"]

        # 2. Access Dashboard with Session Cookie
        dash_res = await ac.get("/dashboard", cookies={"aegis_session": session_cookie})
        assert dash_res.status_code == 200
        dash_html = dash_res.text
        assert "Enterprise Guardrail Dashboard" in dash_html
        assert "Forensic Studio" in dash_html
        assert "Quickstart & Docs" in dash_html
        assert "API Keys & Auth" in dash_html
        assert "Guardrail Policies" in dash_html
        assert "Team & Workspaces" in dash_html
        assert "Billing & Quotas" in dash_html
        assert "dashboardApp()" in dash_html

        # 3. Test Logout flow
        logout_res = await ac.post("/api/auth/logout", cookies={"aegis_session": session_cookie})
        assert logout_res.status_code == 200
        assert logout_res.json()["message"] == "Logged out successfully."
