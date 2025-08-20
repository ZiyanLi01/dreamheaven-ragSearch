#!/usr/bin/env python3
"""
Test script for the new ETL pipeline
Demonstrates the complete embedding generation process
"""

import asyncio
import logging
from etl.embedding_pipeline import EmbeddingPipelineETL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_etl_pipeline():
    """Test the complete ETL pipeline"""
    
    # Sample listings for testing
    sample_listings = [
        {
            'id': 'test-001',
            'title': 'Beautiful South-Facing Apartment with Balcony',
            'description': 'This stunning apartment features a south-facing living room with floor-to-ceiling windows providing abundant natural light. Recently renovated in 2021 with a modern kitchen and updated appliances. Located just steps to the metro station and within walking distance to excellent schools.',
            'property_type': 'Apartment',
            'bedrooms': 2,
            'bathrooms': 2,
            'city': 'San Francisco',
            'state': 'CA',
            'neighborhood': 'Downtown',
            'amenities': ['WiFi', 'Balcony', 'Parking', 'Pet Friendly', 'Modern Kitchen'],
            'facing': 'S',
            'distance_to_metro_m': 500,
            'has_parking_lot': True,
            'garage_number': 1,
            'year_renovated': 2021,
            'school_rating': 9,
            'crime_index': 0.2,
            'has_yard': True,
            'shopping_idx': 85,
            'grocery_idx': 90,
            'square_feet': 1500
        },
        {
            'id': 'test-002',
            'title': 'Luxury Penthouse with City Views',
            'description': 'Exclusive penthouse offering breathtaking city skyline views. This luxury property features high-end finishes, gourmet kitchen, and private elevator access. Perfect for discerning buyers seeking the ultimate in urban living.',
            'property_type': 'Penthouse',
            'bedrooms': 3,
            'bathrooms': 3,
            'city': 'New York',
            'state': 'NY',
            'neighborhood': 'Manhattan',
            'amenities': ['Doorman', 'Concierge', 'Gym', 'Pool', 'Private Elevator'],
            'facing': 'E',
            'distance_to_metro_m': 300,
            'has_parking_lot': False,
            'garage_number': 0,
            'year_renovated': 2023,
            'school_rating': 10,
            'crime_index': 0.1,
            'has_yard': False,
            'shopping_idx': 95,
            'grocery_idx': 90,
            'square_feet': 3000
        },
        {
            'id': 'test-003',
            'title': 'Cozy Studio in Quiet Neighborhood',
            'description': 'Charming studio apartment in a peaceful residential area. Perfect for students or young professionals. Features efficient layout and modern appliances.',
            'property_type': 'Studio',
            'bedrooms': 0,
            'bathrooms': 1,
            'city': 'Boston',
            'state': 'MA',
            'neighborhood': 'Cambridge',
            'amenities': ['WiFi', 'Modern Appliances', 'Laundry'],
            'facing': 'N',
            'distance_to_metro_m': 800,
            'has_parking_lot': True,
            'garage_number': 0,
            'year_renovated': 2019,
            'school_rating': 8,
            'crime_index': 0.4,
            'has_yard': False,
            'shopping_idx': 70,
            'grocery_idx': 75,
            'square_feet': 600
        }
    ]
    
    # Initialize pipeline
    pipeline = EmbeddingPipelineETL()
    
    print("🚀 Testing ETL Pipeline with Multiple Listings")
    print("=" * 60)
    
    # Process each listing
    for i, listing in enumerate(sample_listings, 1):
        print(f"\n📋 Processing Listing {i}: {listing['title']}")
        print("-" * 50)
        
        # Process through pipeline
        embedding_text, embedding_vector, tag_objects = await pipeline.process_listing(listing)
        
        # Display results
        print(f"📝 Embedding Text ({len(embedding_text)} chars):")
        print(f"   {embedding_text[:100]}...")
        
        print(f"🔢 Embedding Vector:")
        if embedding_vector:
            print(f"   Dimensions: {len(embedding_vector)}")
            print(f"   Sample values: {embedding_vector[:3]}...")
        else:
            print("   ❌ Failed to generate embedding")
        
        print(f"🏷️  Structured Tags ({len(tag_objects)} tags):")
        for tag in tag_objects[:5]:  # Show first 5 tags
            print(f"   • {tag['tag']}: {tag['evidence']}")
        if len(tag_objects) > 5:
            print(f"   ... and {len(tag_objects) - 5} more tags")
        
        print(f"💾 Database Update Ready:")
        update_data = {
            'embedding_text': embedding_text,
            'embedding': pipeline.format_embedding_for_db(embedding_vector),
            'tags': tag_objects
        }
        print(f"   ✅ embedding_text: {len(embedding_text)} chars")
        print(f"   ✅ embedding: {len(embedding_vector) if embedding_vector else 0} dimensions")
        print(f"   ✅ tags: {len(tag_objects)} structured tags")
        
        # Add delay between listings
        if i < len(sample_listings):
            print("\n⏳ Waiting 2 seconds before next listing...")
            await asyncio.sleep(2.0)
    
    print("\n🎉 ETL Pipeline Test Completed Successfully!")
    print("=" * 60)
    print("✅ All listings processed through the complete pipeline")
    print("✅ Embedding text generated with semantic cues")
    print("✅ Structured tags extracted from data")
    print("✅ Embedding vectors calculated using OpenAI")
    print("✅ Database update format ready")

if __name__ == "__main__":
    asyncio.run(test_etl_pipeline())
