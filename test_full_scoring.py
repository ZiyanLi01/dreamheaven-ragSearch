#!/usr/bin/env python3
"""
Test full rule-based scoring for San Francisco query
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import extract_search_intent, extract_detailed_criteria, calculate_rule_based_score, choose_search_method, get_exact_matches

async def test_full_scoring():
    """Test full rule-based scoring for the San Francisco query"""
    query = "Give me a short-term rental in downtown that allows pets in San Francisco, CA"
    
    print(f"Testing query: {query}")
    print("=" * 60)
    
    # Extract intent and criteria
    intent = extract_search_intent(query)
    criteria_list = extract_detailed_criteria(query, intent)
    
    print(f"Extracted {len(criteria_list)} criteria:")
    for i, criteria in enumerate(criteria_list, 1):
        print(f"  {i}. {criteria.criteria_name}: {criteria.evidence}")
    print()
    
    # Get database listings
    from main import create_db_pool, close_db_pool
    await create_db_pool()
    
    try:
        from main import db_pool
        listings = await get_exact_matches(intent, db_pool)
        print(f"Found {len(listings)} database listings")
        
        if listings:
            print("\nTesting rule-based scoring on first 2 listings:")
            print("-" * 50)
            
            for i, listing in enumerate(listings[:2], 1):
                score, matched_criteria, unmatched_criteria = calculate_rule_based_score(listing, criteria_list)
                
                print(f"Listing {i}: {listing.get('title', 'Unknown')}")
                print(f"  City: {listing.get('city', 'N/A')}")
                print(f"  Neighborhood: {listing.get('neighborhood', 'N/A')}")
                print(f"  Score: {score:.1%}")
                print(f"  Matched: {matched_criteria}")
                print(f"  Unmatched: {unmatched_criteria}")
                print(f"  Meets 60% threshold: {'✅ YES' if score >= 0.6 else '❌ NO'}")
                print()
            
            # Test choose_search_method
            search_method = choose_search_method(criteria_list, listings)
            print(f"Chosen search method: {search_method}")
            
            # Check individual criteria for first listing
            listing = listings[0]
            print(f"\nIndividual criteria checks for: {listing.get('title', 'Unknown')}")
            print("-" * 50)
            
            from main import check_criteria_against_listing
            for criteria in criteria_list:
                result = check_criteria_against_listing(listing, criteria)
                status = "✅" if result else "❌"
                print(f"  {status} {criteria.criteria_name}: {criteria.evidence}")
        
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(test_full_scoring())
