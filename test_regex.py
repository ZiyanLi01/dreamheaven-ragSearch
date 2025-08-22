#!/usr/bin/env python3
import re

# Test the safe_area regex patterns
query = "Show me listings in safe areas that are walkable to restaurants and cafes in San Francisco"
query_lower = query.lower()

safe_area_patterns = [
    r'\bsafe\s+areas?\b',
    r'\bsafe\s+neighborhoods?\b',
    r'\bsafe\s+communities?\b',
    r'\bsecure\s+areas?\b',
    r'\b(?:low|good)\s+crime\s+(?:areas?|neighborhoods?)\b'
]

print(f"Testing query: {query}")
print(f"Lowercase: {query_lower}")
print()

for i, pattern in enumerate(safe_area_patterns, 1):
    match = re.search(pattern, query_lower)
    result = "✅ MATCH" if match else "❌ NO MATCH"
    print(f"{i}. Pattern: {pattern}")
    print(f"   Result: {result}")
    if match:
        print(f"   Matched text: '{match.group()}'")
    print()
