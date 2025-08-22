#!/usr/bin/env python3
"""
Test location_match criteria checking
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import extract_search_intent, extract_detailed_criteria, check_criteria_against_listing, get_exact_matches

async def test_location_match():
    """Test location_match criteria checking"""
    query = "Give me a short-term rental in downtown that allows pets in San Francisco, CA"
    
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
    
    # Get database listings
    from main import create_db_pool, close_db_pool
    await create_db_pool()
    
    try:
        from main import db_pool
        listings = await get_exact_matches(intent, db_pool)
        print(f"Found {len(listings)} database listings")
        
        if listings:
            print("\nTesting location_match criteria on first listing:")
            print("-" * 50)
            
            listing = listings[0]
            print(f"Listing: {listing.get('title', 'Unknown')}")
            print(f"Listing city: '{listing.get('city', 'N/A')}'")
            print(f"Intent city: '{intent.city}'")
            
            # Find location_match criteria
            location_criteria = None
            for criteria in criteria_list:
                if criteria.criteria_name == "location_match":
                    location_criteria = criteria
                    break
            
            if location_criteria:
                print(f"Location criteria evidence: '{location_criteria.evidence}'")
                
                # Test the location_match checking
                result = check_criteria_against_listing(listing, location_criteria)
                print(f"Location match result: {result}")
                
                # Debug the parsing
                evidence_parts = location_criteria.evidence.split(': ')
                if len(evidence_parts) > 1:
                    expected_city = evidence_parts[1].lower()
                    listing_city = listing.get('city', '').lower()
                    print(f"Expected city: '{expected_city}'")
                    print(f"Listing city: '{listing_city}'")
                    print(f"Match: {expected_city == listing_city}")
        
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(test_location_match())
