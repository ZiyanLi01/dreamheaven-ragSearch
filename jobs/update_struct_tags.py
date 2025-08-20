#!/usr/bin/env python3
"""
ETL #1 Job: Update Structured Tags
Loads listings where tags IS NULL OR cardinality(tags)=0 and applies structured rules
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
from etl.struct_tags import StructuredTagsETL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdateStructTagsJob:
    """Job to update structured tags for listings"""
    
    def __init__(self, dry_run: bool = False):
        """Initialize the job"""
        self.dry_run = dry_run
        self.supabase = SupabaseManager()
        self.etl = StructuredTagsETL()
        self.stats = {
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def get_listings_to_update(self) -> List[Dict[str, Any]]:
        """Get listings that need tag updates"""
        try:
            # Query for listings with NULL tags (most common case)
            result = self.supabase.client.table("listings_v2").select("*").is_("tags", "null").execute()
            
            if result.data:
                logger.info(f"Found {len(result.data)} listings with NULL tags")
                return result.data
            else:
                logger.info("No listings found with NULL tags")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching listings: {e}")
            return []
    
    def update_listing_tags(self, listing: Dict[str, Any]) -> bool:
        """Update tags for a single listing"""
        try:
            listing_id = listing.get('id')
            if not listing_id:
                logger.warning("Listing missing ID, skipping")
                self.stats['skipped'] += 1
                return False
            
            # Extract structured tags
            tag_hits = self.etl.extract_struct_tags(listing)
            
            if not tag_hits:
                logger.info(f"Listing {listing_id}: No tags generated")
                self.stats['skipped'] += 1
                return True
            
            # Get tag names for database update
            tag_names = self.etl.get_tag_names(tag_hits)
            
            # Log the tags being applied
            logger.info(f"Listing {listing_id}: Generated tags: {tag_names}")
            
            if not self.dry_run:
                # Update the listing with new tags
                update_data = {
                    'tags': tag_names,
                    'updated_at': 'now()'
                }
                
                result = self.supabase.client.table("listings_v2").update(update_data).eq('id', listing_id).execute()
                
                if result.data:
                    logger.info(f"Listing {listing_id}: Successfully updated with {len(tag_names)} tags")
                    self.stats['updated'] += 1
                    return True
                else:
                    logger.error(f"Listing {listing_id}: No data returned from update")
                    self.stats['errors'] += 1
                    return False
            else:
                # Dry run - just log what would be updated
                logger.info(f"DRY RUN - Listing {listing_id}: Would update with tags: {tag_names}")
                self.stats['updated'] += 1
                return True
                
        except Exception as e:
            logger.error(f"Error updating listing {listing.get('id', 'unknown')}: {e}")
            self.stats['errors'] += 1
            return False
    
    def run(self) -> bool:
        """Run the complete job"""
        logger.info(f"Starting structured tags update job (dry_run: {self.dry_run})")
        
        # Get listings to update
        listings = self.get_listings_to_update()
        
        if not listings:
            logger.info("No listings to update")
            return True
        
        # Process each listing
        for listing in listings:
            self.stats['processed'] += 1
            self.update_listing_tags(listing)
        
        # Print summary
        self.print_summary()
        
        return self.stats['errors'] == 0
    
    def print_summary(self):
        """Print job summary"""
        logger.info("=" * 50)
        logger.info("STRUCTURED TAGS UPDATE JOB SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Updated: {self.stats['updated']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 50)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Update structured tags for listings")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no database updates)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the job
    job = UpdateStructTagsJob(dry_run=args.dry_run)
    success = job.run()
    
    if success:
        logger.info("Job completed successfully")
        sys.exit(0)
    else:
        logger.error("Job completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    main()
