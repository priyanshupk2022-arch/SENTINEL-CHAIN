"""Unit and Integration Tests for Aegis Offline Cryptographic Licensing Engine."""
import base64
import json
import time
from datetime import datetime, timedelta, timezone
import pytest
from app.security.license import LicenseManager, DEFAULT_PUBLIC_KEY_HEX

# Tests must never rely on a shipped private key: generate a throwaway
# Ed25519 keypair per session and use it as the signing root for this suite.
DEFAULT_DEV_PRIVATE_KEY_HEX, DEFAULT_DEV_PUBLIC_KEY_HEX = LicenseManager.generate_keypair()


class TestCryptoLicense:
    """Test suite for Ed25519 offline license generation, signature verification, and tampering detection."""

    def test_keypair_generation(self):
        """Test Ed25519 keypair generation validity and byte lengths."""
        priv_hex, pub_hex = LicenseManager.generate_keypair()
        assert isinstance(priv_hex, str)
        assert isinstance(pub_hex, str)
        assert len(priv_hex) == 64  # 32 bytes in hex
        assert len(pub_hex) == 64   # 32 bytes in hex

        # Verify hex decodability
        priv_bytes = bytes.fromhex(priv_hex)
        pub_bytes = bytes.fromhex(pub_hex)
        assert len(priv_bytes) == 32
        assert len(pub_bytes) == 32

    def test_invalid_public_key_initialization(self):
        """Test LicenseManager raises ValueError on malformed public keys."""
        with pytest.raises(ValueError, match="must be exactly 32 bytes"):
            LicenseManager(public_key_hex="1234abcd")

        with pytest.raises(ValueError, match="Failed to initialize"):
            LicenseManager(public_key_hex="zz" * 32)

    def test_issue_requires_explicit_signing_key(self):
        """Refusal to mint licenses without an explicit private key (no shipped root key)."""
        with pytest.raises(ValueError, match="signing_private_key_hex"):
            LicenseManager.issue_license(organization="Should Fail Corp")

    def test_issue_and_verify_valid_token(self):
        """Test issuing a license and verifying with the session signing root key."""
        lm = LicenseManager(DEFAULT_DEV_PUBLIC_KEY_HEX)
        token = LicenseManager.issue_license(
            organization="Cyberdyne Systems",
            tier="enterprise_airgap",
            expires_at_iso="2038-01-01T00:00:00Z",
            max_requests_per_month=50_000_000,
            features=["pdf_forensics", "docx_forensics", "pii_redaction", "custom_policies"],
            signing_private_key_hex=DEFAULT_DEV_PRIVATE_KEY_HEX
        )

        assert isinstance(token, str)
        assert "." in token
        parts = token.split(".")
        assert len(parts) == 2

        is_valid, msg, claims = lm.verify_token(token)
        assert is_valid is True
        assert "Valid offline cryptographic license" in msg
        assert claims is not None
        assert claims["org"] == "Cyberdyne Systems"
        assert claims["tier"] == "enterprise_airgap"
        assert claims["max_req"] == 50_000_000
        assert "pdf_forensics" in claims["features"]
        assert "custom_policies" in claims["features"]

    def test_custom_keypair_verification_and_isolation(self):
        """Test licenses signed with custom keypair only verify against matching public key."""
        priv_hex_a, pub_hex_a = LicenseManager.generate_keypair()
        priv_hex_b, pub_hex_b = LicenseManager.generate_keypair()

        manager_a = LicenseManager(pub_hex_a)
        manager_b = LicenseManager(pub_hex_b)

        token_a = LicenseManager.issue_license(
            organization="Org Alpha",
            tier="enterprise",
            signing_private_key_hex=priv_hex_a
        )

        # Valid with Manager A
        is_valid_a, _, claims_a = manager_a.verify_token(token_a)
        assert is_valid_a is True
        assert claims_a["org"] == "Org Alpha"

        # Invalid with Manager B (signature mismatch)
        is_valid_b, msg_b, claims_b = manager_b.verify_token(token_a)
        assert is_valid_b is False
        assert claims_b is None
        assert "verification failed" in msg_b.lower()

    def test_tampered_payload_detection(self):
        """Test that altering payload claims invalidates the Ed25519 signature."""
        lm = LicenseManager(DEFAULT_DEV_PUBLIC_KEY_HEX)
        token = LicenseManager.issue_license(
            organization="Initech Corp",
            tier="starter",
            signing_private_key_hex=DEFAULT_DEV_PRIVATE_KEY_HEX
        )

        b64_payload, b64_sig = token.split(".")

        # Decode payload, tamper tier from starter to enterprise_unlimited, re-encode
        payload_bytes = base64.urlsafe_b64decode(b64_payload + "==")
        payload_data = json.loads(payload_bytes.decode('utf-8'))
        payload_data["tier"] = "enterprise_unlimited"
        tampered_bytes = json.dumps(payload_data).encode('utf-8')
        tampered_b64_payload = base64.urlsafe_b64encode(tampered_bytes).decode('utf-8').rstrip('=')

        tampered_token = f"{tampered_b64_payload}.{b64_sig}"

        is_valid, msg, claims = lm.verify_token(tampered_token)
        assert is_valid is False
        assert claims is None
        assert "verification failed" in msg.lower()

    def test_tampered_signature_detection(self):
        """Test that flipping signature bits causes verification failure."""
        lm = LicenseManager(DEFAULT_DEV_PUBLIC_KEY_HEX)
        token = LicenseManager.issue_license(
            organization="Wayne Enterprises",
            signing_private_key_hex=DEFAULT_DEV_PRIVATE_KEY_HEX
        )
        b64_payload, b64_sig = token.split(".")

        # Corrupt signature string
        corrupted_sig = ("A" if b64_sig[0] != "A" else "B") + b64_sig[1:]
        tampered_token = f"{b64_payload}.{corrupted_sig}"

        is_valid, msg, claims = lm.verify_token(tampered_token)
        assert is_valid is False
        assert claims is None
        assert "verification failed" in msg.lower()

    def test_malformed_token_handling(self):
        """Test handling of empty, non-delimited, or invalid base64 tokens."""
        lm = LicenseManager(DEFAULT_PUBLIC_KEY_HEX)

        # Empty
        assert lm.verify_token("")[0] is False
        # No period
        assert lm.verify_token("invalid_token_without_period")[0] is False
        # Three parts
        assert lm.verify_token("part1.part2.part3")[0] is False
        # Invalid base64
        assert lm.verify_token("???invalid???.!!!sig!!!")[0] is False

    def test_expired_license_detection(self):
        """Test that an expired expiration date is rejected."""
        lm = LicenseManager(DEFAULT_DEV_PUBLIC_KEY_HEX)
        past_time = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()

        token = LicenseManager.issue_license(
            organization="Umbrella Corp",
            expires_at_iso=past_time,
            signing_private_key_hex=DEFAULT_DEV_PRIVATE_KEY_HEX
        )

        is_valid, msg, claims = lm.verify_token(token)
        assert is_valid is False
        assert "expired" in msg.lower()
        assert claims is not None
        assert claims["org"] == "Umbrella Corp"

    def test_license_status_caching_and_defaults(self):
        """Test get_status() default fallback and caching mechanism."""
        lm = LicenseManager(DEFAULT_DEV_PUBLIC_KEY_HEX)

        # Default status (no token)
        default_status = lm.get_status(None)
        assert default_status["active"] is True
        assert default_status["tier"] == "community_evaluation"
        assert default_status["offline_verified"] is True

        # Valid token status
        token = LicenseManager.issue_license(
            organization="Stark Industries",
            tier="defense_grade",
            signing_private_key_hex=DEFAULT_DEV_PRIVATE_KEY_HEX
        )
        status1 = lm.get_status(token)
        assert status1["active"] is True
        assert status1["tier"] == "defense_grade"
        assert status1["organization"] == "Stark Industries"

        # Subsequent call should return cached object
        status2 = lm.get_status(token)
        assert status2 is status1
