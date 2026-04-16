# API Security Skill

## Definition
Comprehensive skill for API-specific vulnerabilities including authentication bypass, authorization flaws, rate limiting bypass, and business logic exploitation.

## Vulnerability Classes
- Broken Object Level Authorization (BOLA)
- Broken Function Level Authorization (BFLA)
- Excessive Data Exposure
- Rate Limiting Bypass
- Mass Assignment
- Parameter Pollution
- API Version Confusion

## Attack Prerequisites
1. API endpoint identified
2. Authentication mechanism detected
3. Endpoint behavior understood

## Techniques

### Technique 1: Object Access Bypass (BOLA)
**Base vs Tampered:**
```
GET /api/users/me
→ 200 OK (own resource)

GET /api/users/999
→ 200 OK (unauthorized access!)
```

**Exploitation chains:**
- Sequential ID enumeration
- UUID prediction
- Hash collision

### Technique 2: Function Access Bypass (BFLA)
**Hidden operations:**
```
GET /api/reports/export        ← User function
POST /api/admin/reports/delete ← Admin function (no auth check?)
```

### Technique 3: Rate Limit Bypass
**Batch operations:**
```
POST /api/login?username=user1&password=pass1
POST /api/login?username=user2&password=pass2
POST /api/login?username=user3&password=pass3
(3 attempts in 1 request = counts as 1?)
```

## Success Metrics
- ✅ Unauthorized resource accessed
- ✅ Admin function executed
- ✅ Rate limiting circumvented

## Integration with Exploit Agent
- **Agent:** idor_agent.py, ssrf_agent.py
- **Trigger:** REST/GraphQL API detected
- **Automation:** Parameter enumeration + authorization bypass testing
- **Memory:** Store successful bypass patterns

## MITRE ATT&CK Mapping
- [T1087.004](https://attack.mitre.org/techniques/T1087/004/) - Cloud Account Discovery
- [T1078.001](https://attack.mitre.org/techniques/T1078/001/) - Valid Accounts
