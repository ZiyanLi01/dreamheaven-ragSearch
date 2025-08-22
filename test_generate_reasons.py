#!/usr/bin/env python3
"""
Test generate_enhanced_reasons with existing reasons
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import generate_enhanced_reasons, extract_search_intent

async def test_generate_reasons():
    """Test generate_enhanced_reasons with existing reasons"""
    
    # Create test listings with existing rule-based reasons
    test_listings = [
        {
            'id': 'test1',
            'title': 'Luxurious 5-Bedroom House in Downtown San Francisco',
            'similarity_score': 1.0,
            'reason': 'Perfect match! This property meets all 4 criteria: location_match, neighborhood, short_term_rental, pet_friendly.',
            'matched_criteria': ['location_match', 'neighborhood', 'short_term_rental', 'pet_friendly'],
            'unmatched_criteria': []
        },
        {
            'id': 'test2',
            'title': 'Luxurious Loft in Hills San Francisco',
            'similarity_score': 1.0,
            'reason': 'Perfect match! This property meets all 4 criteria: location_match, neighborhood, short_term_rental, pet_friendly.',
            'matched_criteria': ['location_match', 'neighborhood', 'short_term_rental', 'pet_friendly'],
            'unmatched_criteria': []
        }
    ]
    
    query = "Give me a short-term rental in downtown that allows pets in San Francisco, CA"
    intent = extract_search_intent(query)
    
    print("Testing generate_enhanced_reasons with existing rule-based reasons:")
    print("=" * 60)
    
    print(f"Query: {query}")
    print(f"Intent: {intent}")
    print()
    
    print("Input listings:")
    for i, listing in enumerate(test_listings, 1):
        print(f"  Listing {i}: {listing.get('title', 'Unknown')}")
        print(f"    Has 'reason' field: {'reason' in listing}")
        print(f"    Reason: {listing.get('reason', 'N/A')}")
    print()
    
    # Test generate_enhanced_reasons
    print("Calling generate_enhanced_reasons...")
    reasons = await generate_enhanced_reasons(query, test_listings, intent)
    
    print(f"generate_enhanced_reasons returned {len(reasons)} reasons:")
    for listing_id, reason in reasons.items():
        print(f"  {listing_id}: {reason}")
    
    print()
    print("Expected behavior: Should preserve existing rule-based reasons")
    print("Actual behavior: See above")

if __name__ == "__main__":
    asyncio.run(test_generate_reasons())
