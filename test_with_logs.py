import asyncio
import aiohttp
import json
import time

async def test_with_logs():
    url = "http://localhost:8001/ai-search"
    payload = {
        "query": "Show me a 1-bedroom apartment in Mission District under $2,500 per month",
        "limit": 5,
        "reasons": True
    }
    
    print("=== TESTING QUERY WITH LOGS ===")
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
                
                if result.get('items'):
                    item = result['items'][0]
                    print(f"First result ID: {item.get('id', 'N/A')}")
                    print(f"First result title: {item.get('title', 'N/A')}")
                    print(f"First result reason: {item.get('reason', 'N/A')}")
            else:
                print(f"Error: {response.status}")
                error_text = await response.text()
                print(f"Error details: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_with_logs())
