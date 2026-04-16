# JWT Abuse Skill

## Definition
This skill specializes in identifying and exploiting vulnerabilities in JWT (JSON Web Token) implementations. Focus areas include cryptographic weaknesses, algorithm confusion, claim manipulation, and signature bypass techniques.

## Vulnerability Classes
- None algorithm bypass
- Weak secret brute-force  
- Algorithm confusion (HMAC vs RSA)
- Claim manipulation
- Key ID injection
- Token expiration bypass

## Attack Prerequisites
1. Access to JWT token (from cookie, header, or request body)
2. Token must be decodable (base64)
3. Signature validation must be bypassable or weak

## Techniques

### Technique 1: None Algorithm Bypass
**Detection:**
- Check "alg" header field
- If alg": "none" present = CRITICAL

**Exploitation:**
```
1. Decode original token
2. Modify payload (set admin=true)
3. Replace signature with empty string
4. Send modified token
```

### Technique 2: Weak Secret Brute Force
**Detection:**
- Algorithm uses HS256/HS384/HS512
- Attempt with common passwords

**Exploitation:**
```
1. Capture JWT
2. Try brute-force with weak secrets dict
3. If match found, generate forged token
4. Modify claims (admin, exp, etc.)
```

### Technique 3: Algorithm Confusion
**Detection:**
- Server expects RS256 (asymmetric)
- Client can request HS256 (symmetric)

**Exploitation:**
```
1. Obtain public key from /.well-known/jwks.json
2. Sign JWT using public key as HMAC secret
3. Change algorithm to HS256
4. Server validates using its public key (= attacker's secret)
```

## Success Metrics
- ✅ Token successfully forged  
- ✅ Admin privileges obtained
- ✅ Expiration bypassed (indefinite token)
- ✅ User ID/claims modified

## Risk Assessment
- **Impact:** Critical (full auth bypass)
- **Frequency:** High (common in startups)
- **Difficulty:** Low (tools automated)

## Related Vulnerabilities
- Authentication Bypass
- Privilege Escalation
- Broken Access Control

## Integration with Exploit Agent
- **Agent:** jwt_server.py
- **Trigger:** JWT token detected in request
- **Automation:** Full token analysis + forging
- **Memory:** Store forged tokens in episodic memory

## MITRE ATT&CK Mapping
- [T1550.001](https://attack.mitre.org/techniques/T1550/001/) - Use Alternate Authentication Material: Application Access Token
