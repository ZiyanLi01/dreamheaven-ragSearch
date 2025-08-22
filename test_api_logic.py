#!/usr/bin/env python3
"""
Test API endpoint logic for preserving rule-based reasons
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_api_logic():
    """Test the API endpoint logic for preserving rule-based reasons"""
    
    # Simulate the listings returned by rule_based_search
    listings_with_reasons = [
        {
            'id': 'test1',
            'title': 'Test Property 1',
            'similarity_score': 1.0,
            'reason': 'Perfect match! This property meets all 4 criteria: location_match, neighborhood, short_term_rental, pet_friendly.',
            'matched_criteria': ['location_match', 'neighborhood', 'short_term_rental', 'pet_friendly'],
            'unmatched_criteria': []
        },
        {
            'id': 'test2',
            'title': 'Test Property 2',
            'similarity_score': 1.0,
            'reason': 'Perfect match! This property meets all 4 criteria: location_match, neighborhood, short_term_rental, pet_friendly.',
            'matched_criteria': ['location_match', 'neighborhood', 'short_term_rental', 'pet_friendly'],
            'unmatched_criteria': []
        }
    ]
    
    # Test the has_rule_based_reasons check
    has_rule_based_reasons = any('reason' in listing for listing in listings_with_reasons)
    
    print("Testing API endpoint logic:")
    print("=" * 40)
    print(f"Listings have 'reason' field: {has_rule_based_reasons}")
    
    for i, listing in enumerate(listings_with_reasons, 1):
        print(f"Listing {i}:")
        print(f"  Has 'reason' field: {'reason' in listing}")
        print(f"  Reason: {listing.get('reason', 'N/A')}")
        print()
    
    # Test the reason extraction logic
    reasons = {}
    if has_rule_based_reasons:
        print("Using existing rule-based reasons...")
        for listing in listings_with_reasons:
            listing_id = str(listing['id'])
            if 'reason' in listing:
                reasons[listing_id] = listing['reason']
                print(f"🔍 Rule-based reason for {listing_id}: {listing['reason']}")
    
    print(f"Final reasons dict: {reasons}")

if __name__ == "__main__":
    asyncio.run(test_api_logic())
