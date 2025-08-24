#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_query_step_by_step():
    """Test the query step by step to understand what's happening"""
    
    query = "Find me a renovated condo near a BART station with parking."
    
    print("🔍 STEP-BY-STEP ANALYSIS OF QUERY:")
    print(f"Query: '{query}'")
    print("=" * 60)
    
    # Test the API endpoint
    url = "http://localhost:8001/ai-search"
    payload = {
        "query": query,
        "page": 1,
        "limit": 10
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("📡 Sending request to /ai-search endpoint...")
            async with session.post(url, json=payload) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ SUCCESS! Here's the response:")
                    print(json.dumps(data, indent=2))
                    
                    # Analyze the results
                    if 'items' in data and data['items']:
                        print("\n📋 ANALYSIS OF RESULTS:")
                        print(f"Total results: {len(data['items'])}")
                        
                        for i, item in enumerate(data['items'][:3], 1):
                            print(f"\n🏠 Result #{i}:")
                            print(f"  Title: {item.get('title', 'N/A')}")
                            print(f"  Match Score: {item.get('match_percent', 'N/A')}")
                            print(f"  Similarity Score: {item.get('similarity_score', 'N/A')}")
                            print(f"  Final Score: {item.get('final_score', 'N/A')}")
                            print(f"  Reason: {item.get('reason', 'N/A')}")
                            
                            # Show matched criteria
                            if 'matched_criteria' in item:
                                print(f"  ✅ Matched: {', '.join(item['matched_criteria'])}")
                            if 'unmatched_criteria' in item:
                                print(f"  ❌ Unmatched: {', '.join(item['unmatched_criteria'])}")
                    
                    # Show "What You Need" if available
                    if 'what_you_need' in data:
                        print(f"\n📝 What You Need: {data['what_you_need']}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ ERROR: {response.status}")
                    print(f"Error details: {error_text}")
                    
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    print("🚀 Starting step-by-step query analysis...")
    asyncio.run(test_query_step_by_step())
