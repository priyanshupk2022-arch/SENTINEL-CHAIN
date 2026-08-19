"""Offline Cryptographic License Verification Engine using Ed25519 signatures."""
import base64
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

# Public key sourced from environment. NEVER hardcode the private key in source.
# The private key is only used in the offline token-generation utility
# (skills/aegis-license-issuer), which is NOT shipped inside the proxy image.
import os
DEFAULT_PUBLIC_KEY_HEX = os.getenv(
    "AEGIS_PUBLIC_KEY_HEX",
    # Built-in development public key. Production deployments MUST set the
    # AEGIS_PUBLIC_KEY_HEX environment variable to the operator's own key.
    "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
)
# Note: there is intentionally no DEFAULT_DEV_PRIVATE_KEY_HEX in the source tree.
# Operators generate Ed25519 keypairs out-of-band and set AEGIS_PUBLIC_KEY_HEX.

class LicenseManager:
    """
    Manages zero-trust offline cryptographic license verification using Ed25519.
    Eliminates phone-home telemetry while strictly enforcing license tiers & validity.
    """
    def __init__(self, public_key_hex: str = DEFAULT_PUBLIC_KEY_HEX):
        self.public_key_hex = public_key_hex
        self._public_key: Optional[ed25519.Ed25519PublicKey] = None
        self._cached_license: Optional[Dict[str, Any]] = None
        self._cached_token: Optional[str] = None
        self._cache_timestamp: float = 0.0
        self._cache_ttl_seconds: float = 60.0  # Cache for 60 seconds to minimize CPU cycles
        self._init_public_key()

    def _init_public_key(self):
        try:
            pub_bytes = bytes.fromhex(self.public_key_hex.strip())
            if len(pub_bytes) != 32:
                raise ValueError("Public key must be exactly 32 bytes (64 hex characters).")
            self._public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        except Exception as e:
            self._public_key = None
            raise ValueError(f"Failed to initialize Ed25519 public key: {str(e)}")

    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """Generates a new Ed25519 private/public keypair (Hex encoded)."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        priv_bytes = private_key.private_bytes_raw()
        pub_bytes = public_key.public_bytes_raw()
        return priv_bytes.hex(), pub_bytes.hex()

    @staticmethod
    def issue_license(
        organization: str,
        tier: str = "enterprise",
        expires_at_iso: Optional[str] = None,
        max_requests_per_month: int = 10_000_000,
        features: Optional[List[str]] = None,
        signing_private_key_hex: Optional[str] = None,
    ) -> str:
        """
        Issues a cryptographically signed offline license token.
        Token format: base64(payload_json) + '.' + base64(ed25519_signature)

        CRITICAL: this method requires the signing private key as an explicit
        argument. The proxy image no longer carries a default private key —
        license issuance must be performed by the operator with a private key
        generated out-of-band.
        """
        if not signing_private_key_hex:
            raise ValueError(
                "Refusing to issue a license without an explicit signing_private_key_hex. "
                "Generate an Ed25519 keypair with LicenseManager.generate_keypair() and "
                "set AEGIS_LICENSE_SIGNING_KEY_HEX in your signing environment."
            )
        if features is None:
            features = [
                "pdf_forensics",
                "docx_forensics",
                "pii_redaction",
                "unicode_sanitization",
                "sse_streaming",
                "zero_telemetry",
                "custom_policies"
            ]

        if not expires_at_iso:
            # Default 10 years validity for enterprise offline license
            expires_at_iso = "2036-12-31T23:59:59Z"

        payload = {
            "iss": "Aegis Authority (Offline Root)",
            "org": organization,
            "tier": tier,
            "max_req": max_requests_per_month,
            "iat": datetime.now(timezone.utc).isoformat(),
            "exp": expires_at_iso,
            "features": features
        }

        payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')

        priv_bytes = bytes.fromhex(signing_private_key_hex.strip())
        priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        signature = priv_key.sign(payload_bytes)

        b64_payload = base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')
        b64_sig = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

        return f"{b64_payload}.{b64_sig}"

    def verify_token(self, token_str: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verifies the offline cryptographic license token without network I/O.
        Returns (is_valid, message, license_claims).
        """
        if not token_str or "." not in token_str:
            return False, "Malformed license token format.", None

        parts = token_str.strip().split(".")
        if len(parts) != 2:
            return False, "Invalid token structure (expected payload.signature).", None

        b64_payload, b64_sig = parts[0], parts[1]

        try:
            # Restore padding for URL-safe base64
            b64_payload_padded = b64_payload + "=" * ((4 - len(b64_payload) % 4) % 4)
            b64_sig_padded = b64_sig + "=" * ((4 - len(b64_sig) % 4) % 4)

            payload_bytes = base64.urlsafe_b64decode(b64_payload_padded.encode('utf-8'))
            sig_bytes = base64.urlsafe_b64decode(b64_sig_padded.encode('utf-8'))

            if not self._public_key:
                return False, "Ed25519 public key not initialized.", None

            # Verify Ed25519 cryptographic signature
            self._public_key.verify(sig_bytes, payload_bytes)

            payload_data = json.loads(payload_bytes.decode('utf-8'))

            # Check expiration date
            exp_str = payload_data.get("exp")
            if exp_str:
                exp_dt = datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > exp_dt:
                    return False, f"License expired on {exp_str}.", payload_data

            return True, "Valid offline cryptographic license.", payload_data

        except InvalidSignature:
            return False, "Cryptographic signature verification failed (Tampered or unauthorized key).", None
        except Exception as e:
            return False, f"Verification anomaly: {str(e)}", None

    def get_status(self, token_str: Optional[str] = None) -> Dict[str, Any]:
        """Returns structured license status for UI badge and audit telemetry."""
        now = time.time()
        if not token_str:
            # Generate default built-in community/trial license claims if no custom token provided
            return {
                "active": True,
                "tier": "community_evaluation",
                "organization": "Local Deployment",
                "expires_at": "2036-12-31T23:59:59Z",
                "features": ["pdf_forensics", "docx_forensics", "pii_redaction", "unicode_sanitization", "sse_streaming"],
                "offline_verified": True,
                "message": "Community Evaluation Tier (Offline active)"
            }

        if self._cached_license and self._cached_token == token_str and (now - self._cache_timestamp) < self._cache_ttl_seconds:
            return self._cached_license

        is_valid, msg, claims = self.verify_token(token_str)
        status = {
            "active": is_valid,
            "tier": claims.get("tier", "unknown") if claims else "unlicensed",
            "organization": claims.get("org", "unknown") if claims else "unlicensed",
            "expires_at": claims.get("exp", "unknown") if claims else "unknown",
            "features": claims.get("features", []) if claims else [],
            "offline_verified": is_valid,
            "message": msg
        }
        self._cached_token = token_str
        self._cached_license = status
        self._cache_timestamp = now
        return status

license_manager = LicenseManager()
