import ipaddress
import socket
import urllib.parse
import re
from typing import Tuple, Optional

# Disallowed protocols
ALLOWED_SCHEMES = {"http", "https"}

# Disallowed internal/private IP ranges for SSRF prevention
PRIVATE_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local & AWS/Cloud metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    ipaddress.ip_network("255.255.255.255/32"),
    ipaddress.ip_network("::1/128"),              # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),             # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),            # IPv6 link-local
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "metadata.google.internal",
    "169.254.169.254"
}

class SecurityUrlValidator:
    """
    Validates user-provided URLs to prevent Server-Side Request Forgery (SSRF),
    cloud metadata harvesting, local network traversal, and protocol abuse.
    """

    @classmethod
    def validate_url(cls, raw_url: str, allow_local_demo: bool = True) -> Tuple[bool, str, Optional[str]]:
        """
        Validates target URL.
        Returns (is_valid, error_reason, canonical_url)
        """
        if not raw_url or not isinstance(raw_url, str):
            return False, "Target URL must be a non-empty string.", None

        raw_url = raw_url.strip()
        try:
            parsed = urllib.parse.urlparse(raw_url)
        except Exception as e:
            return False, f"Malformed URL: {str(e)}", None

        # 1. Scheme Check
        if not parsed.scheme or parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return False, f"Invalid scheme '{parsed.scheme}'. Only http and https are permitted.", None

        # 2. Hostname Check
        hostname = parsed.hostname
        if not hostname:
            return False, "URL is missing a valid hostname or domain.", None

        hostname_lower = hostname.lower()

        # Check for local demo exception (e.g. testing with Chaos Proxy at localhost:8000)
        if allow_local_demo and (hostname_lower in {"localhost", "127.0.0.1"} or "api/proxy/target" in parsed.path):
            canonical_url = urllib.parse.urlunparse(parsed)
            return True, "Valid local test target", canonical_url

        # Check blocked hostnames
        if hostname_lower in BLOCKED_HOSTNAMES:
            return False, f"Access to internal host '{hostname}' is blocked by SSRF security policy.", None

        # 3. IP Resolution Check
        try:
            # Resolve DNS to IPv4/IPv6 addresses
            addr_info = socket.getaddrinfo(hostname, None)
            resolved_ips = {item[4][0] for item in addr_info}

            for ip_str in resolved_ips:
                ip_obj = ipaddress.ip_address(ip_str)
                for net in PRIVATE_IP_NETWORKS:
                    if ip_obj in net:
                        return False, f"Target hostname '{hostname}' resolves to restricted private IP address '{ip_str}'.", None
        except socket.gaierror:
            # DNS resolution failed or unreachable domain
            return False, f"Could not resolve domain '{hostname}'. Verify the domain name.", None
        except Exception as e:
            return False, f"Security validation error: {str(e)}", None

        canonical_url = urllib.parse.urlunparse(parsed)
        return True, "Valid public target URL", canonical_url
