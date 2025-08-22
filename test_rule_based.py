#!/usr/bin/env python3
"""
Test script for rule-based scoring debugging
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import extract_search_intent, extract_detailed_criteria, calculate_rule_based_score, SearchIntent, CriteriaMatch

async def test_rule_based_scoring():
    """Test rule-based scoring for the problematic query"""
    query = "Show me listings in safe areas that are walkable to restaurants and cafes in San Francisco"
    
    print(f"Testing query: {query}")
    print("=" * 60)
    
    # Extract intent and criteria
    intent = extract_search_intent(query)
    criteria_list = extract_detailed_criteria(query, intent)
    
    print(f"Extracted {len(criteria_list)} criteria:")
    for i, criteria in enumerate(criteria_list, 1):
        print(f"  {i}. {criteria.criteria_name}: {criteria.evidence}")
    print()
    
    # Sample listing data (from the database)
    sample_listings = [
        {
            'id': 'test1',
            'title': 'Cozy Studio in Park San Francisco',
            'city': 'San Francisco',
            'neighborhood': 'Park',
            'crime_index': 45.0,
            'grocery_idx': 60.0,
            'shopping_idx': 70.0,
            'property_type': 'Studio',
            'bedrooms': 0,
            'bathrooms': 1,
            'square_feet': 500,
            'price_for_sale': 400000,
            'price_per_month': 2500,
            'is_featured': False
        },
        {
            'id': 'test2', 
            'title': 'Luxurious House in Pacific Heights',
            'city': 'San Francisco',
            'neighborhood': 'Pacific Heights',
            'crime_index': 30.0,
            'grocery_idx': 80.0,
            'shopping_idx': 85.0,
            'property_type': 'House',
            'bedrooms': 3,
            'bathrooms': 2,
            'square_feet': 2000,
            'price_for_sale': 1500000,
            'price_per_month': 8000,
            'is_featured': True
        }
    ]
    
    print("Testing rule-based scoring on sample listings:")
    print("-" * 40)
    
    for i, listing in enumerate(sample_listings, 1):
        score, matched_criteria, unmatched_criteria = calculate_rule_based_score(listing, criteria_list)
        
        print(f"Listing {i}: {listing['title']}")
        print(f"  Score: {score:.1%}")
        print(f"  Matched criteria: {matched_criteria}")
        print(f"  Unmatched criteria: {unmatched_criteria}")
        print()
        
        # Check each criteria individually
        print("  Individual criteria checks:")
        for criteria in criteria_list:
            from main import check_criteria_against_listing
            result = check_criteria_against_listing(listing, criteria)
            status = "✅" if result else "❌"
            print(f"    {status} {criteria.criteria_name}: {criteria.evidence}")
        print()

if __name__ == "__main__":
    asyncio.run(test_rule_based_scoring())
