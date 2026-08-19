"""Test Offline Cryptographic License Manager."""
import pytest
from app.security.license import LicenseManager, DEFAULT_PUBLIC_KEY_HEX

# Tests must never rely on a shipped private key: generate a throwaway
# Ed25519 keypair per session and use it as the signing key.
DEFAULT_DEV_PRIVATE_KEY_HEX, DEFAULT_DEV_PUBLIC_KEY_HEX = LicenseManager.generate_keypair()

def test_keypair_generation():
    priv, pub = LicenseManager.generate_keypair()
    assert len(priv) == 64
    assert len(pub) == 64
    assert priv != pub

def test_issue_and_verify_valid_token():
    priv, pub = LicenseManager.generate_keypair()
    token = LicenseManager.issue_license(
        organization="Federal Defense AI",
        tier="enterprise",
        signing_private_key_hex=priv
    )
    mgr = LicenseManager(public_key_hex=pub)
    is_valid, msg, claims = mgr.verify_token(token)
    assert is_valid is True
    assert claims is not None
    assert claims["org"] == "Federal Defense AI"
    assert claims["tier"] == "enterprise"
    assert "pdf_forensics" in claims["features"]

def test_tampered_token_rejected():
    priv, pub = LicenseManager.generate_keypair()
    token = LicenseManager.issue_license("Org A", "pro", signing_private_key_hex=priv)
    
    # Tamper with the base64 payload
    payload_b64, sig_b64 = token.split(".")
    tampered_token = "eyJvcmciOiAiSGFja2VkIn0." + sig_b64
    
    mgr = LicenseManager(public_key_hex=pub)
    is_valid, msg, claims = mgr.verify_token(tampered_token)
    assert is_valid is False
    assert "verification failed" in msg.lower() or "tampered" in msg.lower()

def test_expired_token_rejected():
    priv, pub = LicenseManager.generate_keypair()
    expired_token = LicenseManager.issue_license(
        organization="Legacy Corp",
        tier="community",
        expires_at_iso="2020-01-01T00:00:00Z",
        signing_private_key_hex=priv
    )
    mgr = LicenseManager(public_key_hex=pub)
    is_valid, msg, claims = mgr.verify_token(expired_token)
    assert is_valid is False
    assert "expired" in msg.lower()

def test_default_dev_license_verification():
    dev_token = LicenseManager.issue_license("Aegis Dev", "unlimited", signing_private_key_hex=DEFAULT_DEV_PRIVATE_KEY_HEX)
    mgr = LicenseManager(public_key_hex=DEFAULT_DEV_PUBLIC_KEY_HEX)
    is_valid, msg, claims = mgr.verify_token(dev_token)
    assert is_valid is True
    assert claims["org"] == "Aegis Dev"
