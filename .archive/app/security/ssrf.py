"""Enterprise SSRF Protection & URL Validation Utility."""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # Link-Local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),     # Multicast
    ipaddress.ip_network("240.0.0.0/4"),     # Reserved
    ipaddress.ip_network("::1/128"),         # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),        # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),       # IPv6 Link-Local
    ipaddress.ip_network("ff00::/8"),        # IPv6 Multicast
]

def is_ip_blocked(ip_addr_str: str) -> bool:
    """Checks whether an IP address belongs to any restricted / private / link-local network."""
    try:
        ip = ipaddress.ip_address(ip_addr_str.strip())
        if hasattr(ip, "ipv4_mapped") and ip.ipv4_mapped:
            if is_ip_blocked(str(ip.ipv4_mapped)):
                return True
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return True
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                return True
        return False
    except ValueError:
        return True

def validate_safe_url(url: str, allow_local_for_dev: bool = False) -> Tuple[bool, str]:
    """
    Validates a URL against Server-Side Request Forgery (SSRF) attack vectors.
    Returns (is_valid, error_message).
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string."

    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        return False, f"Malformed URL: {str(e)}"

    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid URL scheme '{parsed.scheme}'. Only http:// and https:// are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a valid hostname or IP address."

    # Immediate rejection of known dangerous hostnames
    lower_host = hostname.lower().strip()
    if lower_host in ("localhost", "127.0.0.1", "::1", "metadata.google.internal", "169.254.169.254"):
        if not allow_local_for_dev:
            return False, f"Access to restricted hostname or metadata address '{lower_host}' is prohibited."

    # Direct parse for Decimal, Hex, Octal, and Raw IP representations
    try:
        # Octal / dotted notation with leading zeros
        if "." in hostname and any(part.startswith("0") and len(part) > 1 and part.isdigit() for part in hostname.split(".")):
            try:
                octal_parts = [int(p, 8 if p.startswith("0") else 10) for p in hostname.split(".")]
                if len(octal_parts) == 4:
                    reconstructed_ip = ".".join(str(p) for p in octal_parts)
                    if is_ip_blocked(reconstructed_ip):
                        if not allow_local_for_dev:
                            return False, f"Octal IP notation '{hostname}' resolves to restricted IP '{reconstructed_ip}'."
            except Exception:
                pass

        if hostname.isdigit():
            num_ip = ipaddress.ip_address(int(hostname))
            if is_ip_blocked(str(num_ip)):
                if not allow_local_for_dev:
                    return False, f"Decimal IP notation '{hostname}' resolves to restricted IP '{num_ip}'."
        elif hostname.startswith("0x") or hostname.startswith("0X"):
            num_ip = ipaddress.ip_address(int(hostname, 16))
            if is_ip_blocked(str(num_ip)):
                if not allow_local_for_dev:
                    return False, f"Hexadecimal IP notation '{hostname}' resolves to restricted IP '{num_ip}'."
        else:
            # Check if it's already an IP address
            clean_host = hostname.strip("[]")
            raw_ip = ipaddress.ip_address(clean_host)
            if is_ip_blocked(str(raw_ip)):
                if not allow_local_for_dev:
                    return False, f"Direct IP address '{hostname}' is in restricted range '{raw_ip}'."
    except ValueError:
        pass  # Standard DNS hostname, proceed to DNS resolution

    # DNS Resolution & IP Check
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        for item in addr_info:
            ip_str = item[4][0]
            if is_ip_blocked(ip_str):
                if not allow_local_for_dev:
                    return False, f"Host '{hostname}' resolves to restricted/private IP '{ip_str}'."

    except socket.gaierror as e:
        if allow_local_for_dev:
            return True, "Offline/mock hostname allowed in development/test environment."
        return False, f"Could not resolve host '{hostname}': {str(e)}"
    except Exception as e:
        if allow_local_for_dev:
            return True, "Mock host resolution bypassed in development/test environment."
        return False, f"DNS resolution failed for '{hostname}': {str(e)}"

    return True, "URL is safe."
