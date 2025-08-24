#!/usr/bin/env python3
"""
Test the specific query: "Find me a renovated condo near a BART station with parking."
"""

import asyncio
import aiohttp
import json
import time

async def test_bart_query():
    url = "http://localhost:8001/ai-search"
    payload = {
        "query": "Find me a renovated condo near a BART station with parking.",
        "limit": 5,
        "reasons": True
    }
    
    print("=== TESTING BART STATION QUERY ===")
    print(f"Query: {payload['query']}")
    print("Sending request...")
    
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            end_time = time.time()
            print(f"Response time: {end_time - start_time:.2f} seconds")
            
            if response.status == 200:
                result = await response.json()
                print(f"Status: {response.status}")
                print(f"What You Need: {result.get('what_you_need', 'N/A')}")
                print(f"Results count: {len(result.get('items', []))}")
                
                if result.get('items') and result['items'][0].get('id') != 'no_results':
                    print("\n=== TOP 3 RESULTS ===")
                    for i, item in enumerate(result['items'][:3]):
                        print(f"{i+1}. {item.get('title', 'N/A')}")
                        print(f"   Address: {item.get('address', 'N/A')}")
                        print(f"   Price: ${item.get('price', 'N/A')}")
                        print(f"   Score: {item.get('similarity_score', 'N/A'):.2%}")
                        print(f"   Reason: {item.get('reason', 'N/A')}")
                        print()
                else:
                    print("No results found")
                    if result.get('items'):
                        item = result['items'][0]
                        print(f"Reason: {item.get('reason', 'N/A')}")
            else:
                print(f"Error: {response.status}")
                error_text = await response.text()
                print(f"Error details: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_bart_query())
