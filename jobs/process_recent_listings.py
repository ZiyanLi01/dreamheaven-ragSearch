#!/usr/bin/env python3
"""
Process Recent Listings Job
Process recent listings in listings_v2 with complete pipeline (tags, embedding_text, embeddings)
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from etl.embedding_pipeline import EmbeddingPipelineETL
from scripts.supabase_manager import SupabaseManager
from scripts.check_recent_listings import check_recent_listings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcessRecentListingsJob:
    """Job to process recent listings with complete pipeline"""
    
    def __init__(self, dry_run: bool = False, days_back: int = 7):
        """Initialize the job"""
        self.dry_run = dry_run
        self.days_back = days_back
        self.supabase = SupabaseManager()
        self.pipeline = EmbeddingPipelineETL()
        self.stats = {
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0,
            'tags_added': 0,
            'text_added': 0,
            'embeddings_added': 0
        }
    
    def get_recent_listings_needing_updates(self) -> List[Dict[str, Any]]:
        """Get recent listings that need updates (tags, embedding_text, or embeddings)"""
        try:
            # Get all listings
            all_listings = self.supabase.get_listings()
            
            # Find recent listings
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
            recent_listings = []
            
            for listing in all_listings:
                updated_at_str = listing.get('updated_at', '')
                if updated_at_str:
                    try:
                        # Parse the updated_at string
                        if 'T' in updated_at_str:
                            # ISO format - handle timezone properly
                            if updated_at_str.endswith('Z'):
                                updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                            elif '+' in updated_at_str:
                                updated_at = datetime.fromisoformat(updated_at_str)
                            else:
                                # No timezone info, assume UTC
                                updated_at = datetime.fromisoformat(updated_at_str + '+00:00')
                        else:
                            # Try other formats
                            updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                            # Assume UTC for datetime without timezone
                            updated_at = updated_at.replace(tzinfo=timezone.utc)
                        
                        # Make sure we're comparing timezone-aware datetimes
                        if updated_at.tzinfo is None:
                            updated_at = updated_at.replace(tzinfo=timezone.utc)
                        
                        if updated_at > cutoff_date:
                            recent_listings.append(listing)
                    except Exception as e:
                        logger.warning(f"Error parsing updated_at for listing {listing.get('id', 'unknown')}: {e}")
                        continue
            
            # Filter listings that need updates
            listings_needing_updates = []
            for listing in recent_listings:
                # Check what's missing
                has_tags = listing.get('tags') and len(listing.get('tags', [])) > 0
                has_embedding_text = listing.get('embedding_text') and listing.get('embedding_text', '').strip() != ''
                has_embedding = listing.get('embedding') is not None
                
                # If any field is missing, include in updates
                if not has_tags or not has_embedding_text or not has_embedding:
                    listings_needing_updates.append(listing)
            
            logger.info(f"Found {len(listings_needing_updates)} recent listings needing updates")
            return listings_needing_updates
                
        except Exception as e:
            logger.error(f"Error fetching recent listings: {e}")
            return []
    
    async def update_listing_complete_pipeline(self, listing_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a single listing with complete pipeline data"""
        try:
            if self.dry_run:
                logger.info(f"DRY RUN - Would update listing {listing_id}:")
                logger.info(f"   Tags: {len(update_data.get('tags', []))} tags")
                logger.info(f"   Embedding text: {len(update_data.get('embedding_text', ''))} chars")
                logger.info(f"   Embedding: {len(update_data.get('embedding', '').split(',')) if update_data.get('embedding') else 0} dimensions")
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
    
    async def process_listing_complete_pipeline(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single listing through the complete pipeline"""
        try:
            listing_id = listing.get('id', 'unknown')
            
            # Step 1: Generate enhanced embedding text and embedding
            embedding_text, embedding_vector, tag_objects = await self.pipeline.process_listing(listing)
            
            # Step 2: Prepare update data
            update_data = {
                'embedding_text': embedding_text,
                'embedding': self.pipeline.format_embedding_for_db(embedding_vector),
                'tags': tag_objects,
                'updated_at': 'now()'
            }
            
            # Step 3: Update database
            success = await self.update_listing_complete_pipeline(listing_id, update_data)
            
            if success:
                # Track what was added
                if not listing.get('tags') or len(listing.get('tags', [])) == 0:
                    self.stats['tags_added'] += 1
                if not listing.get('embedding_text') or listing.get('embedding_text', '').strip() == '':
                    self.stats['text_added'] += 1
                if not listing.get('embedding'):
                    self.stats['embeddings_added'] += 1
                
                return {
                    'success': True,
                    'listing_id': listing_id,
                    'tags_count': len(tag_objects),
                    'text_length': len(embedding_text),
                    'embedding_dimensions': len(embedding_vector) if embedding_vector else 0
                }
            else:
                return {'success': False, 'listing_id': listing_id}
            
        except Exception as e:
            logger.error(f"Failed to process listing {listing.get('id', 'unknown')}: {e}")
            return {'success': False, 'listing_id': listing.get('id', 'unknown'), 'error': str(e)}
    
    async def run(self):
        """Run the complete pipeline for recent listings"""
        logger.info("🚀 Starting Recent Listings Pipeline Processing...")
        logger.info(f"   Dry run: {self.dry_run}")
        logger.info(f"   Days back: {self.days_back}")
        
        try:
            # Get recent listings needing updates
            listings = self.get_recent_listings_needing_updates()
            
            if not listings:
                logger.info("✅ No recent listings need updates. Job complete!")
                return
            
            logger.info(f"📦 Processing {len(listings)} recent listings...")
            
            # Process each listing
            for i, listing in enumerate(listings, 1):
                listing_id = listing.get('id', 'unknown')
                title = listing.get('title', 'No title')[:50]
                
                logger.info(f"🔄 Processing listing {i}/{len(listings)}: {listing_id}")
                logger.info(f"   Title: {title}...")
                
                # Process listing through complete pipeline
                result = await self.process_listing_complete_pipeline(listing)
                
                if result['success']:
                    self.stats['updated'] += 1
                    logger.info(f"   ✅ Success: {result['tags_count']} tags, {result['text_length']} chars, {result['embedding_dimensions']} dims")
                else:
                    self.stats['errors'] += 1
                    logger.error(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                
                self.stats['processed'] += 1
                
                # Add delay between listings
                if i < len(listings):
                    logger.info("   ⏳ Waiting 2 seconds before next listing...")
                    await asyncio.sleep(2.0)
            
            # Final statistics
            logger.info("🎉 Recent listings pipeline processing completed!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   Total processed: {self.stats['processed']}")
            logger.info(f"   Successfully updated: {self.stats['updated']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            logger.info(f"   Tags added: {self.stats['tags_added']}")
            logger.info(f"   Embedding text added: {self.stats['text_added']}")
            logger.info(f"   Embeddings added: {self.stats['embeddings_added']}")
            
        except Exception as e:
            logger.error(f"❌ Job failed: {e}")
            raise

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Process recent listings with complete pipeline")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run in dry-run mode (no database updates)")
    parser.add_argument("--days-back", type=int, default=7,
                       help="Number of days back to consider 'recent' (default: 7)")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check recent listings, don't process them")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.check_only:
        # Only check recent listings
        print("🔍 Checking recent listings only...")
        check_recent_listings()
    else:
        # Process recent listings
        job = ProcessRecentListingsJob(
            dry_run=args.dry_run,
            days_back=args.days_back
        )
        asyncio.run(job.run())

if __name__ == "__main__":
    main()
