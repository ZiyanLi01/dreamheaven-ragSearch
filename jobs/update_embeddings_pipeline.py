#!/usr/bin/env python3
"""
ETL Pipeline Job: Update Embeddings
Uses the complete embedding pipeline to update embedding_text, embeddings, and tags
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from etl.embedding_pipeline import EmbeddingPipelineETL
from scripts.supabase_manager import SupabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdateEmbeddingsPipelineJob:
    """Job to update embeddings using the complete ETL pipeline"""
    
    def __init__(self, dry_run: bool = False, batch_size: int = 10):
        """Initialize the job"""
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.supabase = SupabaseManager()
        self.pipeline = EmbeddingPipelineETL()
        self.stats = {
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0,
            'batches': 0
        }
    
    def get_listings_to_update(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get listings that need embedding updates"""
        try:
            # Query for listings without embeddings or with empty embedding_text
            query = """
            SELECT * FROM listings_v2 
            WHERE embedding IS NULL 
               OR embedding_text = '' 
               OR embedding_text IS NULL
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.supabase.client.table("listings_v2").select("*").execute()
            
            # Filter results based on our criteria
            filtered_listings = []
            for listing in result.data:
                if (not listing.get('embedding') or 
                    not listing.get('embedding_text') or 
                    listing.get('embedding_text') == ''):
                    filtered_listings.append(listing)
            
            if filtered_listings:
                logger.info(f"Found {len(filtered_listings)} listings needing embedding updates")
                return filtered_listings[:limit] if limit else filtered_listings
            else:
                logger.info("No listings found needing embedding updates")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching listings: {e}")
            return []
    
    async def update_listing_embeddings(self, listing_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a single listing with embeddings, embedding_text, and tags"""
        try:
            if self.dry_run:
                logger.info(f"DRY RUN - Would update listing {listing_id}:")
                logger.info(f"   embedding_text: {len(update_data.get('embedding_text', ''))} chars")
                logger.info(f"   embedding: {len(update_data.get('embedding', '').split(',')) if update_data.get('embedding') else 0} dimensions")
                logger.info(f"   tags: {len(update_data.get('tags', []))} tags")
                return True
            
            # Update the listing
            result = self.supabase.client.table("listings_v2").update(update_data).eq('id', listing_id).execute()
            
            if result.data:
                logger.info(f"✅ Successfully updated listing {listing_id}")
                return True
            else:
                logger.error(f"❌ No data returned from update for listing {listing_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update listing {listing_id}: {e}")
            return False
    
    async def process_batch(self, listings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of listings through the pipeline"""
        logger.info(f"🔄 Processing batch of {len(listings)} listings...")
        
        # Use the pipeline's batch processing with our update callback
        results = await self.pipeline.process_batch(
            listings, 
            update_callback=self.update_listing_embeddings
        )
        
        # Update our stats
        self.stats['processed'] += results['processed']
        self.stats['updated'] += results['successful']
        self.stats['errors'] += results['failed']
        self.stats['batches'] += 1
        
        return results
    
    async def run(self, limit: int = None):
        """Run the complete embedding update job"""
        logger.info("🚀 Starting embedding pipeline update job...")
        logger.info(f"   Dry run: {self.dry_run}")
        logger.info(f"   Batch size: {self.batch_size}")
        logger.info(f"   Limit: {limit if limit else 'No limit'}")
        
        try:
            # Get listings to update
            listings = self.get_listings_to_update(limit)
            
            if not listings:
                logger.info("✅ No listings need updates. Job complete!")
                return
            
            # Process in batches
            total_listings = len(listings)
            processed = 0
            
            for i in range(0, total_listings, self.batch_size):
                batch = listings[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                
                logger.info(f"📦 Processing batch {batch_num} ({len(batch)} listings)...")
                
                # Process batch
                batch_results = await self.process_batch(batch)
                
                processed += len(batch)
                progress = (processed / total_listings) * 100
                
                logger.info(f"✅ Batch {batch_num} completed!")
                logger.info(f"   Progress: {processed}/{total_listings} ({progress:.1f}%)")
                logger.info(f"   Batch results: {batch_results['successful']} success, {batch_results['failed']} failed")
                
                # Add delay between batches
                if processed < total_listings:
                    logger.info("⏳ Waiting 5 seconds before next batch...")
                    await asyncio.sleep(5.0)
            
            # Final statistics
            logger.info("🎉 Embedding pipeline job completed!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   Total processed: {self.stats['processed']}")
            logger.info(f"   Successfully updated: {self.stats['updated']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            logger.info(f"   Batches processed: {self.stats['batches']}")
            
        except Exception as e:
            logger.error(f"❌ Job failed: {e}")
            raise

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Update embeddings using ETL pipeline")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run in dry-run mode (no database updates)")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Number of listings to process per batch (default: 10)")
    parser.add_argument("--limit", type=int, default=None,
                       help="Limit total number of listings to process")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run job
    job = UpdateEmbeddingsPipelineJob(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )
    
    # Run the job
    asyncio.run(job.run(limit=args.limit))

if __name__ == "__main__":
    main()
