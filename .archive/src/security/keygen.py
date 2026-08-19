import argparse
import sys
import json
from pathlib import Path

# Ensure root directory is on python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.security.license import LicenseManager, DEFAULT_PUBLIC_KEY_HEX, DEFAULT_DEV_PRIVATE_KEY_HEX

def main():
    parser = argparse.ArgumentParser(
        description="Aegis Offline Ed25519 Cryptographic Licensing Tool"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Keygen command
    subparsers.add_parser("keygen", help="Generate a new Ed25519 signing keypair")

    # Issue command
    issue_parser = subparsers.add_parser("issue", help="Issue a signed offline license token")
    issue_parser.add_argument("--org", required=True, help="Organization or customer name")
    issue_parser.add_argument("--tier", default="enterprise", choices=["community", "pro", "enterprise", "unlimited"], help="License tier")
    issue_parser.add_argument("--privkey", default=DEFAULT_DEV_PRIVATE_KEY_HEX, help="Hex-encoded Ed25519 private key")
    issue_parser.add_argument("--exp", default="2036-12-31T23:59:59Z", help="Expiration timestamp in ISO-8601 UTC format")
    issue_parser.add_argument("--max-req", type=int, default=10_000_000, help="Max requests per month")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify an offline license token")
    verify_parser.add_argument("--token", required=True, help="Base64 encoded license token")
    verify_parser.add_argument("--pubkey", default=DEFAULT_PUBLIC_KEY_HEX, help="Hex-encoded Ed25519 public key")

    args = parser.parse_args()

    if args.command == "keygen":
        priv, pub = LicenseManager.generate_keypair()
        print("==================================================")
        print("   AEGIS ED25519 CRYPTOGRAPHIC KEYPAIR GENERATED")
        print("==================================================")
        print(f"Private Key (KEEP SECRET): {priv}")
        print(f"Public Key  (DEPLOY TO APP): {pub}")
        print("==================================================")

    elif args.command == "issue":
        token = LicenseManager.issue_license(
            organization=args.org,
            tier=args.tier,
            expires_at_iso=args.exp,
            max_requests_per_month=args.max_req,
            signing_private_key_hex=args.privkey
        )
        print("==================================================")
        print("   AEGIS OFFLINE LICENSE TOKEN ISSUED")
        print("==================================================")
        print(f"Organization : {args.org}")
        print(f"Tier         : {args.tier.upper()}")
        print(f"Expires      : {args.exp}")
        print(f"Token        : {token}")
        print("==================================================")
        print("\nTo activate, add to your .env or environment:")
        print(f"AEGIS_LICENSE_TOKEN={token}")

    elif args.command == "verify":
        mgr = LicenseManager(public_key_hex=args.pubkey)
        is_valid, msg, claims = mgr.verify_token(args.token)
        print("==================================================")
        print(f"Verification Result: {'[+] VALID' if is_valid else '[-] INVALID'}")
        print(f"Message: {msg}")
        if claims:
            print("License Claims:")
            print(json.dumps(claims, indent=2))
        print("==================================================")
        sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
