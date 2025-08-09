"""
Test script for DreamHeaven RAG API
"""

import asyncio
import json
from typing import Dict, Any
import aiohttp

BASE_URL = "http://localhost:8001"

async def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def test_stats():
    """Test stats endpoint"""
    print("\nTesting stats endpoint...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Stats: {json.dumps(data, indent=2)}")
                    return data
                else:
                    print(f"❌ Stats failed: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return None

async def test_search(query: str, limit: int = 10, offset: int = 0):
    """Test semantic search endpoint"""
    pagination_info = f" (limit={limit}, offset={offset})" if offset > 0 else f" (limit={limit})"
    print(f"\nTesting search{pagination_info}: '{query}'...")
    async with aiohttp.ClientSession() as session:
        try:
            payload = {"query": query, "limit": limit, "offset": offset}
            async with session.post(
                f"{BASE_URL}/ai-search", 
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Search successful!")
                    print(f"Query: {data['query']}")
                    print(f"Total results: {data['total_results']}")
                    
                    for i, result in enumerate(data['results'], 1):
                        print(f"\n  Result {i}:")
                        print(f"    ID: {result['id']}")
                        print(f"    Title: {result.get('title', 'N/A')}")
                        print(f"    Address: {result.get('address', 'N/A')}")
                        print(f"    Bedrooms: {result.get('bedrooms', 'N/A')}")
                        print(f"    Bathrooms: {result.get('bathrooms', 'N/A')}")
                        print(f"    Price: ${result.get('price', 0):,.0f}")
                        print(f"    Similarity: {result['similarity_score']:.3f}")
                    
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Search failed: {response.status}")
                    print(f"Error: {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Search error: {e}")
            return None

async def test_pagination():
    """Test pagination functionality"""
    print(f"\n🔄 Testing Pagination...")
    query = "modern condo"
    
    # First page: 10 results
    print(f"\n📄 Page 1 (first 10 results):")
    page1 = await test_search(query, limit=10, offset=0)
    
    # Second page: next 5 results  
    print(f"\n📄 Page 2 (next 5 results):")
    page2 = await test_search(query, limit=5, offset=10)
    
    # Third page: next 5 results
    print(f"\n📄 Page 3 (next 5 results):")
    page3 = await test_search(query, limit=5, offset=15)
    
    return page1, page2, page3

async def main():
    """Run all tests"""
    print("🚀 Starting DreamHeaven RAG API Tests")
    print("=" * 50)
    
    # Test health check
    health_ok = await test_health_check()
    if not health_ok:
        print("❌ Service is not healthy. Please check if the server is running.")
        return
    
    # Test stats
    stats = await test_stats()
    if stats and stats.get('embedded_listings', 0) == 0:
        print("⚠️ No embeddings found. Run 'python embed_listings.py' first.")
        return
    
    # Test different search queries
    test_queries = [
        "modern 3-bedroom condo in San Francisco with ocean view",
        "luxury house with pool and garage",
        "affordable apartment for rent in downtown",
        "family home with yard and parking",
        "studio apartment near the beach"
    ]
    
    for query in test_queries:
        await test_search(query)
        await asyncio.sleep(1)  # Small delay between requests
    
    # Test pagination
    await test_pagination()
    
    print("\n" + "=" * 50)
    print("🎉 RAG API tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

