# GraphQL Skill

## Definition
This skill specializes in exploiting GraphQL API vulnerabilities including introspection abuse, query batching, authorization bypass, and information disclosure.

## Vulnerability Classes
- Introspection enabled (schema enumeration)
- Query depth exploitation (DoS)
- Batch operations (rate limiting bypass)
- Authorization bypass (field-level)
- Hidden query discovery
- Type coercion bypass

## Attack Prerequisites
1. GraphQL endpoint reachable
2. Introspection enabled (common default)
3. Query operation allowed without strict AUTH

## Techniques

### Technique 1: Introspection Exploitation
**Detection:**
- Query `{ __schema { types { name } } }`
- If responds with schema = CRITICAL

**Exploitation:**
```
1. Extract all queries, mutations, subscriptions
2. Identify hidden admin endpoints
3. Discover field types and arguments
4. Find authorization weaknesses
```

### Technique 2: Batch Enumeration
**Detection:**
- Server accepts multiple queries in one request
- No rate limiting per query

**Exploitation:**
```
1. Create 1000 aliases for same query
2. Iterate through IDs: u1: user(id: 1), u2: user(id: 2), ...
3. Dump all user data in single request
4. Bypass rate limiting
```

### Technique 3: Field Authorization Bypass
**Detection:**
- Attempt to query private/admin fields
- If accessible = BOLA/authorization failure

**Exploitation:**
```
{ user { email ssn creditCard { number } } }
```

## Success Metrics
- ✅ Schema fully enumerated
- ✅ Private fields accessed
- ✅ Admin data exported
- ✅ Sensitive information leaked

## Risk Assessment
- **Impact:** High (data exfiltration, privilege escalation)
- **Frequency:** Medium (introspection common)
- **Difficulty:** Low (tools existence: get-graphql-schema)

## Related Vulnerabilities
- Information Disclosure
- Broken Object Level Authorization
- Denial of Service

## Integration with Exploit Agent
- **Agent:** xss_agent.py (can be adapted for GraphQL)
- **Trigger:** GraphQL endpoint detected
- **Automation:** Schema enumeration + field discovery
- **Memory:** Store enumerated schema in knowledge graph

## MITRE ATT&CK Mapping
- [T1087](https://attack.mitre.org/techniques/T1087/) - Account Discovery
- [T1087.004](https://attack.mitre.org/techniques/T1087/004/) - Account Discovery: Cloud Account
