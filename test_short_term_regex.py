#!/usr/bin/env python3
import re

# Test the short-term rental regex patterns
query = "Give me a short-term rental in downtown that allows pets."
query_lower = query.lower()

short_term_patterns = [
    r'\bshort\s*[-]?\s*term\s+rental\b',
    r'\bshort\s*[-]?\s*term\s+lease\b',
    r'\btemporary\s+rental\b',
    r'\bmonth\s*to\s*month\b',
    r'\bflexible\s+lease\b'
]

print(f"Testing query: {query}")
print(f"Lowercase: {query_lower}")
print()

for i, pattern in enumerate(short_term_patterns, 1):
    match = re.search(pattern, query_lower)
    result = "✅ MATCH" if match else "❌ NO MATCH"
    print(f"{i}. Pattern: {pattern}")
    print(f"   Result: {result}")
    if match:
        print(f"   Matched text: '{match.group()}'")
    print()
