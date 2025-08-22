#!/usr/bin/env python3
"""
Test script for hybrid approach debugging
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import extract_search_intent, extract_detailed_criteria, SearchIntent, CriteriaMatch

def test_intent_extraction():
    """Test intent extraction for the problematic query"""
    query = "Show me listings in safe areas that are walkable to restaurants and cafes in San Francisco"
    
    print(f"Testing query: {query}")
    print("=" * 60)
    
    # Extract intent
    intent = extract_search_intent(query)
    print(f"Extracted intent: {intent}")
    print()
    
    # Extract detailed criteria
    criteria_list = extract_detailed_criteria(query, intent)
    print(f"Extracted {len(criteria_list)} criteria:")
    for i, criteria in enumerate(criteria_list, 1):
        print(f"  {i}. {criteria.criteria_name}: {criteria.evidence}")
    print()
    
    # Check which criteria should be captured
    expected_criteria = [
        "location_match",
        "safe_area", 
        "walkable",
        "dining_options"
    ]
    
    print("Expected vs Actual criteria:")
    for expected in expected_criteria:
        found = any(c.criteria_name == expected for c in criteria_list)
        status = "✅" if found else "❌"
        print(f"  {status} {expected}")
    
    print()
    print("Intent flags that should be True:")
    print(f"  safe_area: {intent.safe_area}")
    print(f"  walkable: {intent.walkable}")
    print(f"  dining_options: {intent.dining_options}")

if __name__ == "__main__":
    test_intent_extraction()
