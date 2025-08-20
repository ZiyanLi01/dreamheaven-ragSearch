#!/usr/bin/env python3
"""
Update Missing Embeddings Job
Fill in all missing embeddings based on updated_at field, prioritizing recent listings
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from etl.embedding_pipeline import EmbeddingPipelineETL
from scripts.supabase_manager import SupabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdateMissingEmbeddingsJob:
    """Job to update all missing embeddings based on updated_at field"""
    
    def __init__(self, dry_run: bool = False, batch_size: int = 10, days_back: int = 30):
        """Initialize the job"""
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.days_back = days_back
        self.supabase = SupabaseManager()
        self.pipeline = EmbeddingPipelineETL()
        self.stats = {
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0,
            'batches': 0,
            'recent_processed': 0,
            'older_processed': 0
        }
    
    def get_listings_needing_embeddings(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get listings that need embeddings, sorted by updated_at (recent first)"""
        try:
            # Get all listings
            all_listings = self.supabase.get_listings()
            
            # Filter listings that need embeddings
            listings_needing_embeddings = []
            for listing in all_listings:
                # Check if listing needs embeddings
                needs_embedding = (
                    not listing.get('embedding') or 
                    not listing.get('embedding_text') or 
                    listing.get('embedding_text', '').strip() == ''
                )
                
                if needs_embedding:
                    listings_needing_embeddings.append(listing)
            
            # Sort by updated_at (recent first)
            def parse_updated_at(listing):
                updated_at_str = listing.get('updated_at', '')
                if not updated_at_str:
                    return datetime.min
                
                try:
                    if 'T' in updated_at_str:
                        # ISO format
                        return datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                    else:
                        # Try other formats
                        return datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                except:
                    return datetime.min
            
            listings_needing_embeddings.sort(key=parse_updated_at, reverse=True)
            
            if limit:
                listings_needing_embeddings = listings_needing_embeddings[:limit]
            
            logger.info(f"Found {len(listings_needing_embeddings)} listings needing embeddings")
            return listings_needing_embeddings
                
        except Exception as e:
            logger.error(f"Error fetching listings needing embeddings: {e}")
            return []
    
    def categorize_listings_by_recency(self, listings: List[Dict[str, Any]]) -> tuple:
        """Categorize listings into recent and older based on updated_at"""
        recent_listings = []
        older_listings = []
        cutoff_date = datetime.now() - timedelta(days=self.days_back)
        
        for listing in listings:
            updated_at_str = listing.get('updated_at', '')
            if not updated_at_str:
                older_listings.append(listing)
                continue
            
            try:
                if 'T' in updated_at_str:
                    # ISO format
                    updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                else:
                    # Try other formats
                    updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                
                if updated_at > cutoff_date:
                    recent_listings.append(listing)
                else:
                    older_listings.append(listing)
            except:
                older_listings.append(listing)
        
        return recent_listings, older_listings
    
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
    
    async def process_batch(self, listings: List[Dict[str, Any]], category: str = "unknown") -> Dict[str, Any]:
        """Process a batch of listings through the pipeline"""
        logger.info(f"🔄 Processing batch of {len(listings)} {category} listings...")
        
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
        
        if category == "recent":
            self.stats['recent_processed'] += results['processed']
        else:
            self.stats['older_processed'] += results['processed']
        
        return results
    
    async def run(self, limit: int = None, prioritize_recent: bool = True):
        """Run the missing embeddings update job"""
        logger.info("🚀 Starting missing embeddings update job...")
        logger.info(f"   Dry run: {self.dry_run}")
        logger.info(f"   Batch size: {self.batch_size}")
        logger.info(f"   Days back for recent: {self.days_back}")
        logger.info(f"   Prioritize recent: {prioritize_recent}")
        logger.info(f"   Limit: {limit if limit else 'No limit'}")
        
        try:
            # Get listings needing embeddings
            listings = self.get_listings_needing_embeddings(limit)
            
            if not listings:
                logger.info("✅ No listings need embeddings. Job complete!")
                return
            
            # Categorize by recency
            recent_listings, older_listings = self.categorize_listings_by_recency(listings)
            
            logger.info(f"📊 Categorized listings:")
            logger.info(f"   Recent listings (last {self.days_back} days): {len(recent_listings)}")
            logger.info(f"   Older listings: {len(older_listings)}")
            
            # Determine processing order
            if prioritize_recent:
                processing_order = [
                    ("recent", recent_listings),
                    ("older", older_listings)
                ]
            else:
                # Process all together in updated_at order
                processing_order = [("all", listings)]
            
            total_listings = len(listings)
            processed = 0
            
            for category, category_listings in processing_order:
                if not category_listings:
                    continue
                
                logger.info(f"📦 Processing {category} listings ({len(category_listings)} total)...")
                
                # Process in batches
                for i in range(0, len(category_listings), self.batch_size):
                    batch = category_listings[i:i + self.batch_size]
                    batch_num = (i // self.batch_size) + 1
                    
                    logger.info(f"📦 Processing {category} batch {batch_num} ({len(batch)} listings)...")
                    
                    # Process batch
                    batch_results = await self.process_batch(batch, category)
                    
                    processed += len(batch)
                    progress = (processed / total_listings) * 100
                    
                    logger.info(f"✅ {category.capitalize()} batch {batch_num} completed!")
                    logger.info(f"   Progress: {processed}/{total_listings} ({progress:.1f}%)")
                    logger.info(f"   Batch results: {batch_results['successful']} success, {batch_results['failed']} failed")
                    
                    # Add delay between batches
                    if processed < total_listings:
                        logger.info("⏳ Waiting 5 seconds before next batch...")
                        await asyncio.sleep(5.0)
            
            # Final statistics
            logger.info("🎉 Missing embeddings update job completed!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   Total processed: {self.stats['processed']}")
            logger.info(f"   Successfully updated: {self.stats['updated']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            logger.info(f"   Batches processed: {self.stats['batches']}")
            logger.info(f"   Recent listings processed: {self.stats['recent_processed']}")
            logger.info(f"   Older listings processed: {self.stats['older_processed']}")
            
        except Exception as e:
            logger.error(f"❌ Job failed: {e}")
            raise

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Update missing embeddings based on updated_at")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run in dry-run mode (no database updates)")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Number of listings to process per batch (default: 10)")
    parser.add_argument("--limit", type=int, default=None,
                       help="Limit total number of listings to process")
    parser.add_argument("--days-back", type=int, default=30,
                       help="Number of days back to consider 'recent' (default: 30)")
    parser.add_argument("--no-prioritize", action="store_true",
                       help="Don't prioritize recent listings (process all in updated_at order)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run job
    job = UpdateMissingEmbeddingsJob(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        days_back=args.days_back
    )
    
    # Run the job
    asyncio.run(job.run(limit=args.limit, prioritize_recent=not args.no_prioritize))

if __name__ == "__main__":
    main()
