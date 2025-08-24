#!/usr/bin/env python3
"""
Test the improved house recommendation algorithm
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import improved_house_recommendation, extract_search_intent, create_db_pool, close_db_pool

async def test_improved_algorithm():
    """Test the improved house recommendation algorithm with various queries"""
    
    # Load environment variables
    load_dotenv()
    
    # Test queries with different scenarios
    test_queries = [
        # Scenario 1: Strict requirements with hard constraints
        {
            "query": "3-bedroom house in San Francisco under $1.2M with garage, cannot exceed budget",
            "description": "Hard constraints with permanent price limit"
        },
        
        # Scenario 2: Flexible requirements
        {
            "query": "2-bedroom apartment in San Francisco around $800K, near metro, good schools",
            "description": "Flexible requirements with soft preferences"
        },
        
        # Scenario 3: Very specific requirements
        {
            "query": "4-bedroom house in Pacific Heights, San Francisco, under $2M, must have yard, pet-friendly",
            "description": "Very specific neighborhood and requirements"
        },
        
        # Scenario 4: Minimal requirements
        {
            "query": "apartment in San Francisco",
            "description": "Minimal requirements - should trigger semantic search"
        },
        
        # Scenario 5: Impossible requirements
        {
            "query": "10-bedroom mansion in San Francisco under $500K",
            "description": "Impossible requirements - should return empty with explanation"
        }
    ]
    
    try:
        # Initialize database connection
        await create_db_pool()
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{'='*80}")
            print(f"TEST CASE {i}: {test_case['description']}")
            print(f"Query: {test_case['query']}")
            print(f"{'='*80}")
            
            # Extract intent
            intent = extract_search_intent(test_case['query'])
            print(f"Extracted Intent: {intent}")
            
            # Run improved algorithm
            results = await improved_house_recommendation(
                query=test_case['query'],
                intent=intent,
                limit=5
            )
            
            # Display results
            if not results:
                print("❌ No results found")
            elif len(results) == 1 and results[0].get('id') == 'no_results':
                print("❌ No matching properties found")
                print(f"Explanation: {results[0].get('reason', 'No explanation provided')}")
            else:
                print(f"✅ Found {len(results)} results")
                print("\nTop Results:")
                for j, result in enumerate(results[:3], 1):
                    print(f"\n{j}. {result.get('title', 'Unknown')}")
                    print(f"   Address: {result.get('address', 'Unknown')}")
                    print(f"   Price: ${result.get('price', 'Unknown'):,}" if result.get('price') else "   Price: Unknown")
                    print(f"   Beds/Baths: {result.get('bedrooms', '?')}/{result.get('bathrooms', '?')}")
                    print(f"   Match %: {result.get('match_percent', 0):.1%}")
                    print(f"   Final Score: {result.get('final_score', 0):.3f}")
                    print(f"   Reason: {result.get('reason', 'No reason provided')}")
                    
                    if result.get('relaxation_explanation'):
                        print(f"   Relaxation: {result['relaxation_explanation']}")
            
            print(f"\n{'-'*80}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(test_improved_algorithm())

