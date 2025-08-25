#!/usr/bin/env python3
"""
ETL Pipeline: Complete Embedding Generation
Combines embedding text generation and embedding calculation in one pipeline
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from etl.embedding_text import EmbeddingTextETL
from etl.struct_tags import StructuredTagsETL
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingPipelineETL:
    """Complete ETL pipeline for embedding generation"""
    
    def __init__(self):
        """Initialize the pipeline with all ETL components"""
        self.embedding_text_etl = EmbeddingTextETL()
        self.struct_tags_etl = StructuredTagsETL()
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI's text-embedding-3-small model"""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to get embedding for text: {text[:100]}... Error: {e}")
            return None
    
    def enhance_listing_with_tags(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance listing data with structured tags"""
        try:
            # Generate structured tags
            tag_hits = self.struct_tags_etl.extract_struct_tags(listing)
            tag_names = self.struct_tags_etl.get_tag_names(tag_hits)
            
            # Add tags to listing data for embedding text generation
            enhanced_listing = listing.copy()
            enhanced_listing['structured_tags'] = tag_names
            
            return enhanced_listing
        except Exception as e:
            logger.warning(f"Failed to enhance listing with tags: {e}")
            return listing
    
    def build_enhanced_embedding_text(self, listing: Dict[str, Any]) -> str:
        """Build enhanced embedding text using both ETL components"""
        try:
            # First, enhance listing with structured tags
            enhanced_listing = self.enhance_listing_with_tags(listing)
            
            # Generate embedding text with semantic cues
            embedding_text = self.embedding_text_etl.process_listing(enhanced_listing)
            
            # Add structured tags to the embedding text if not already present
            if 'structured_tags' in enhanced_listing and enhanced_listing['structured_tags']:
                tags_section = f"STRUCTURED_TAGS: {', '.join(enhanced_listing['structured_tags'])}"
                
                # Insert structured tags before the DESCRIPTION section
                if "DESCRIPTION:" in embedding_text:
                    parts = embedding_text.split("DESCRIPTION:")
                    embedding_text = f"{parts[0]}{tags_section} | DESCRIPTION:{parts[1]}"
                else:
                    embedding_text = f"{embedding_text} | {tags_section}"
            
            # Ensure length limit
            if len(embedding_text) > 500:
                embedding_text = embedding_text[:497] + "..."
            
            return embedding_text
            
        except Exception as e:
            logger.error(f"Failed to build enhanced embedding text: {e}")
            # Fallback to basic embedding text
            return self.embedding_text_etl.process_listing(listing)
    
    async def process_listing(self, listing: Dict[str, Any]) -> Tuple[str, Optional[List[float]], List[str]]:
        """Process a single listing through the complete pipeline"""
        try:
            # Step 1: Generate enhanced embedding text
            embedding_text = self.build_enhanced_embedding_text(listing)
            
            # Step 2: Generate embedding vector
            embedding_vector = await self.get_embedding(embedding_text)
            
            # Step 3: Get structured tags for database storage
            tag_hits = self.struct_tags_etl.extract_struct_tags(listing)
            tag_objects = self.struct_tags_etl.get_tag_objects(tag_hits)
            
            return embedding_text, embedding_vector, tag_objects
            
        except Exception as e:
            logger.error(f"Failed to process listing {listing.get('id', 'unknown')}: {e}")
            return "", None, []
    
    def format_embedding_for_db(self, embedding_vector: List[float]) -> str:
        """Format embedding vector for database storage"""
        if not embedding_vector:
            return None
        return f"[{','.join(map(str, embedding_vector))}]"
    
    async def process_batch(self, listings: List[Dict[str, Any]], 
                          update_callback=None) -> Dict[str, Any]:
        """Process a batch of listings"""
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        logger.info(f"Processing batch of {len(listings)} listings...")
        
        for i, listing in enumerate(listings):
            try:
                listing_id = listing.get('id', f'listing_{i}')
                
                # Process listing through pipeline
                embedding_text, embedding_vector, tag_objects = await self.process_listing(listing)
                
                if embedding_text and embedding_vector:
                    # Format data for database update
                    update_data = {
                        'embedding_text': embedding_text,
                        'embedding': self.format_embedding_for_db(embedding_vector),
                        'tags': tag_objects,
                        'updated_at': 'now()'
                    }
                    
                    # Call update callback if provided
                    if update_callback:
                        success = await update_callback(listing_id, update_data)
                        if success:
                            results['successful'] += 1
                        else:
                            results['failed'] += 1
                    else:
                        results['successful'] += 1
                    
                    logger.info(f"Processed listing {listing_id} ({i+1}/{len(listings)})")
                    logger.debug(f"   Text length: {len(embedding_text)} chars")
                    logger.debug(f"   Tags: {len(tag_objects)} tags")
                    
                else:
                    results['failed'] += 1
                    error_msg = f"Failed to generate embedding for listing {listing_id}"
                    results['errors'].append(error_msg)
                    logger.warning(f"Error: {error_msg}")
                
                results['processed'] += 1
                
                # Rate limiting delay
                await asyncio.sleep(2.0)
                
            except Exception as e:
                results['failed'] += 1
                error_msg = f"Error processing listing {listing.get('id', f'listing_{i}')}: {e}"
                results['errors'].append(error_msg)
                logger.error(f"Error: {error_msg}")
                continue
        
        return results

def main():
    """Test the complete ETL pipeline"""
    async def test_pipeline():
        pipeline = EmbeddingPipelineETL()
        
        # Sample listing data
        sample_listing = {
            'id': 'test-001',
            'title': 'Beautiful South-Facing Apartment with Balcony',
            'description': 'This stunning apartment features a south-facing living room with floor-to-ceiling windows providing abundant natural light. Recently renovated in 2021 with a modern kitchen and updated appliances. Located just steps to the metro station and within walking distance to excellent schools. The property includes a private balcony, assigned parking, and is pet-friendly. The neighborhood is known for its safety and convenience to shopping and grocery stores.',
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
        }
        
        # Process listing
        embedding_text, embedding_vector, tag_objects = await pipeline.process_listing(sample_listing)
        
        print("=== ETL Pipeline Test Results ===")
        print(f"\n📝 Embedding Text ({len(embedding_text)} chars):")
        print(embedding_text)
        
        print(f"\n🔢 Embedding Vector:")
        if embedding_vector:
            print(f"   Dimensions: {len(embedding_vector)}")
            print(f"   Sample values: {embedding_vector[:5]}...")
        else:
            print("   Failed to generate embedding")
        
        print(f"\nStructured Tags ({len(tag_objects)} tags):")
        for tag in tag_objects:
            print(f"   • {tag['tag']}: {tag['evidence']}")
        
        print(f"\n💾 Database Update Data:")
        update_data = {
            'embedding_text': embedding_text,
            'embedding': pipeline.format_embedding_for_db(embedding_vector),
            'tags': tag_objects
        }
        print(f"   embedding_text: {len(embedding_text)} chars")
        print(f"   embedding: {len(embedding_vector) if embedding_vector else 0} dimensions")
        print(f"   tags: {len(tag_objects)} tags")
    
    # Run the test
    asyncio.run(test_pipeline())

if __name__ == "__main__":
    main()
