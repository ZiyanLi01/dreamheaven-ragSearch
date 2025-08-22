#!/usr/bin/env python3
"""
Test script to check actual database listings
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import extract_search_intent, extract_detailed_criteria, calculate_rule_based_score, get_exact_matches

async def test_db_listings():
    """Test with actual database listings"""
    query = "Show me listings in safe areas that are walkable to restaurants and cafes in San Francisco"
    
    print(f"Testing query: {query}")
    print("=" * 60)
    
    # Extract intent and criteria
    from main import extract_search_intent, extract_detailed_criteria
    intent = extract_search_intent(query)
    criteria_list = extract_detailed_criteria(query, intent)
    
    print(f"Extracted {len(criteria_list)} criteria:")
    for i, criteria in enumerate(criteria_list, 1):
        print(f"  {i}. {criteria.criteria_name}: {criteria.evidence}")
    print()
    
    # Get actual database listings
    from main import create_db_pool, close_db_pool
    await create_db_pool()
    
    try:
        from main import db_pool
        listings = await get_exact_matches(intent, db_pool)
        print(f"Found {len(listings)} database listings")
        
        if listings:
            print("\nTesting rule-based scoring on first 3 listings:")
            print("-" * 50)
            
            for i, listing in enumerate(listings[:3], 1):
                score, matched_criteria, unmatched_criteria = calculate_rule_based_score(listing, criteria_list)
                
                print(f"Listing {i}: {listing.get('title', 'Unknown')}")
                print(f"  City: {listing.get('city', 'N/A')}")
                print(f"  Neighborhood: {listing.get('neighborhood', 'N/A')}")
                print(f"  Crime Index: {listing.get('crime_index', 'N/A')}")
                print(f"  Grocery Index: {listing.get('grocery_idx', 'N/A')}")
                print(f"  Shopping Index: {listing.get('shopping_idx', 'N/A')}")
                print(f"  Score: {score:.1%}")
                print(f"  Matched: {matched_criteria}")
                print(f"  Unmatched: {unmatched_criteria}")
                print()
                
                # Check each criteria individually
                print("  Individual criteria checks:")
                for criteria in criteria_list:
                    from main import check_criteria_against_listing
                    result = check_criteria_against_listing(listing, criteria)
                    status = "✅" if result else "❌"
                    print(f"    {status} {criteria.criteria_name}")
                print()
        
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(test_db_listings())
