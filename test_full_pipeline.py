#!/usr/bin/env python3
"""
Test full pipeline to debug rule-based reasons
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import enhanced_semantic_search, extract_search_intent

async def test_full_pipeline():
    """Test the full enhanced search pipeline"""
    query = "Give me a short-term rental in downtown that allows pets in San Francisco, CA"
    
    print(f"Testing query: {query}")
    print("=" * 60)
    
    # Extract intent
    intent = extract_search_intent(query)
    print(f"Extracted intent: {intent}")
    print()
    
    # Get database connection
    from main import create_db_pool, close_db_pool
    await create_db_pool()
    
    try:
        from main import db_pool
        
        # Run the full enhanced search pipeline
        print("Running enhanced_semantic_search...")
        results = await enhanced_semantic_search(
            query=query,
            intent=intent,
            limit=2,
            offset=0,
            pool=db_pool
        )
        
        print(f"Pipeline returned {len(results)} results")
        print()
        
        for i, listing in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  Title: {listing.get('title', 'Unknown')}")
            print(f"  Similarity Score: {listing.get('similarity_score', 'N/A')}")
            print(f"  Has 'reason' field: {'reason' in listing}")
            if 'reason' in listing:
                print(f"  Reason: {listing['reason']}")
            if 'matched_criteria' in listing:
                print(f"  Matched Criteria: {listing['matched_criteria']}")
            if 'unmatched_criteria' in listing:
                print(f"  Unmatched Criteria: {listing['unmatched_criteria']}")
            print()
        
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
