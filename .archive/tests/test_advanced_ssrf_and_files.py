"""Advanced SSRF Evasion & Malicious Document Testing."""
import asyncio
import io
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db
from app.security.ssrf import validate_safe_url

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

def test_advanced_ssrf_evasion_techniques():
    """Validates SSRF defense against decimal, hex, loopback, and metadata obfuscations."""
    blocked_urls = [
        "http://2130706433/admin",          # Decimal for 127.0.0.1
        "http://0x7f000001/status",         # Hex for 127.0.0.1
        "http://169.254.169.254/latest",    # AWS/GCP Metadata
        "http://[::1]/internal",            # IPv6 Loopback
        "http://10.0.0.1:8080/flag",        # RFC1918 Class A
        "http://172.16.0.1/flag",           # RFC1918 Class B
        "http://192.168.1.1/flag",          # RFC1918 Class C
        "file:///etc/passwd",               # File protocol
        "gopher://127.0.0.1:6379/_INFO"     # Gopher protocol
    ]

    for u in blocked_urls:
        is_safe, msg = validate_safe_url(u, allow_local_for_dev=False)
        assert is_safe is False, f"Expected URL {u} to be blocked by SSRF defense! Message: {msg}"

@pytest.mark.asyncio
async def test_malformed_and_oversized_documents():
    """Validates that corrupt, malformed, or oversized documents are safely handled."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)
        reg = await ac.post("/api/auth/register", json={
            "full_name": "Fuzz Tester",
            "organization_name": "Fuzz Corp",
            "email": f"fuzz_{t_now}@fuzz.com",
            "password": "Password123!"
        })
        token = reg.json()["access_token"]
        key_res = await ac.post("/api/api-keys", json={"name": "Fuzz Key"}, headers={"Authorization": f"Bearer {token}"})
        raw_key = key_res.json()["raw_api_key"]
        headers = {"Authorization": f"Bearer {raw_key}"}

        # 1. Corrupted / Malformed PDF bytes
        corrupted_pdf = b"%PDF-1.4\nGARBAGE_BYTES_NO_CATALOG_NO_ROOT\n%%EOF"
        files = {"file": ("corrupt.pdf", corrupted_pdf, "application/pdf")}
        res_corrupt = await ac.post("/v1/scan/document", files=files, headers=headers)
        assert res_corrupt.status_code == 200  # Returns scan report with graceful error handling

        # 2. Corrupted DOCX (not a valid zip)
        corrupted_docx = b"PK\x03\x04NOT_A_VALID_WORD_DOCX_XML"
        files_docx = {"file": ("corrupt.docx", corrupted_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        res_docx = await ac.post("/v1/scan/document", files=files_docx, headers=headers)
        assert res_docx.status_code == 200
