#!/usr/bin/env python3
"""
Test script for pet query intent extraction
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import extract_search_intent, extract_detailed_criteria, calculate_rule_based_score, get_exact_matches

async def test_pet_query():
    """Test the pet query intent extraction"""
    query = "Give me a short-term rental in downtown that allows pets."
    
    print(f"Testing query: {query}")
    print("=" * 60)
    
    # Extract intent and criteria
    intent = extract_search_intent(query)
    criteria_list = extract_detailed_criteria(query, intent)
    
    print(f"Extracted intent: {intent}")
    print()
    print(f"Extracted {len(criteria_list)} criteria:")
    for i, criteria in enumerate(criteria_list, 1):
        print(f"  {i}. {criteria.criteria_name}: {criteria.evidence}")
    print()
    
    # Check which criteria should be captured
    expected_criteria = [
        "neighborhood",
        "short_term_rental", 
        "pet_friendly"
    ]
    
    print("Expected vs Actual criteria:")
    for expected in expected_criteria:
        found = any(c.criteria_name == expected for c in criteria_list)
        status = "✅" if found else "❌"
        print(f"  {status} {expected}")
    
    print()
    print("Intent flags that should be True:")
    print(f"  neighborhood: {intent.neighborhood}")
    print(f"  short_term_rental: {intent.short_term_rental}")
    print(f"  pet_friendly: {intent.pet_friendly}")

if __name__ == "__main__":
    asyncio.run(test_pet_query())
