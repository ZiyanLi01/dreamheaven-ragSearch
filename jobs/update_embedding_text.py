#!/usr/bin/env python3
"""
ETL #2 Job: Update Embedding Text
Selects rows where embedding_text = '' and generates embedding-ready text
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.supabase_manager import SupabaseManager
from etl.embedding_text import EmbeddingTextETL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdateEmbeddingTextJob:
    """Job to update embedding_text for listings"""
    
    def __init__(self, dry_run: bool = False):
        """Initialize the job"""
        self.dry_run = dry_run
        self.supabase = SupabaseManager()
        self.etl = EmbeddingTextETL()
        self.stats = {
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def get_listings_to_update(self) -> List[Dict[str, Any]]:
        """Get listings that need embedding_text updates"""
        try:
            # Query for listings with empty embedding_text
            result = self.supabase.client.table("listings_v2").select("*").eq("embedding_text", "").execute()
            
            if result.data:
                logger.info(f"Found {len(result.data)} listings with empty embedding_text")
                return result.data
            else:
                logger.info("No listings found with empty embedding_text")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching listings: {e}")
            return []
    
    def update_listing_embedding_text(self, listing: Dict[str, Any]) -> bool:
        """Update embedding_text for a single listing"""
        try:
            listing_id = listing.get('id')
            if not listing_id:
                logger.warning("Listing missing ID, skipping")
                self.stats['skipped'] += 1
                return False
            
            # Generate embedding text
            embedding_text = self.etl.process_listing(listing)
            
            if not embedding_text:
                logger.info(f"Listing {listing_id}: No embedding text generated")
                self.stats['skipped'] += 1
                return True
            
            # Log the embedding text being applied
            logger.info(f"Listing {listing_id}: Generated embedding text ({len(embedding_text)} chars)")
            logger.debug(f"Listing {listing_id}: Embedding text preview: {embedding_text[:100]}...")
            
            if not self.dry_run:
                # Update the listing with new embedding_text
                update_data = {
                    'embedding_text': embedding_text,
                    'updated_at': 'now()'
                }
                
                result = self.supabase.client.table("listings_v2").update(update_data).eq('id', listing_id).execute()
                
                if result.data:
                    logger.info(f"Listing {listing_id}: Successfully updated with embedding text")
                    self.stats['updated'] += 1
                    return True
                else:
                    logger.error(f"Listing {listing_id}: No data returned from update")
                    self.stats['errors'] += 1
                    return False
            else:
                # Dry run - just log what would be updated
                logger.info(f"DRY RUN - Listing {listing_id}: Would update with embedding text ({len(embedding_text)} chars)")
                self.stats['updated'] += 1
                return True
                
        except Exception as e:
            logger.error(f"Error updating listing {listing.get('id', 'unknown')}: {e}")
            self.stats['errors'] += 1
            return False
    
    def run(self) -> bool:
        """Run the complete job"""
        logger.info(f"Starting embedding text update job (dry_run: {self.dry_run})")
        
        # Get listings to update
        listings = self.get_listings_to_update()
        
        if not listings:
            logger.info("No listings to update")
            return True
        
        # Process each listing
        for listing in listings:
            self.stats['processed'] += 1
            self.update_listing_embedding_text(listing)
        
        # Print summary
        self.print_summary()
        
        return self.stats['errors'] == 0
    
    def print_summary(self):
        """Print job summary"""
        logger.info("=" * 50)
        logger.info("EMBEDDING TEXT UPDATE JOB SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Updated: {self.stats['updated']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 50)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Update embedding text for listings")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no database updates)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the job
    job = UpdateEmbeddingTextJob(dry_run=args.dry_run)
    success = job.run()
    
    if success:
        logger.info("Job completed successfully")
        sys.exit(0)
    else:
        logger.error("Job completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    main()
