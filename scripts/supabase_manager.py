#!/usr/bin/env python3
"""
Supabase Manager
Handles database operations for the ETL pipeline
"""

import os
import logging
from typing import Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manager for Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Supabase client initialized")
    
    def get_listings(self, limit: int = None, offset: int = 0) -> list:
        """Get listings from the database.

        If limit is None, fetches ALL listings using pagination (batches of 1000).
        If limit is provided, returns a single page starting at offset.
        """
        try:
            # Single-call fetch for all listings when limit is None (use a high limit)
            if limit is None:
                result = self.client.table("listings_v2").select("*").limit(100000).execute()
                return result.data if result.data else []

            # Otherwise fetch a single page
            query = self.client.table("listings_v2").select("*")
            if offset > 0:
                query = query.range(offset, offset + limit - 1)
            else:
                query = query.limit(limit)
            result = query.execute()
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error fetching listings: {e}")
            return []
    
    def get_listings_without_embeddings(self, limit: int = None) -> list:
        """Get listings that don't have embeddings"""
        try:
            query = self.client.table("listings_v2").select("*").is_("embedding", "null")
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching listings without embeddings: {e}")
            return []
    
    def update_listing(self, listing_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a single listing"""
        try:
            result = self.client.table("listings_v2").update(update_data).eq("id", listing_id).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating listing {listing_id}: {e}")
            return False
    
    def update_listings_batch(self, updates: list) -> bool:
        """Update multiple listings in batch"""
        try:
            # Note: Supabase doesn't support true batch updates, so we'll do them individually
            success_count = 0
            
            for update in updates:
                listing_id = update.get("id")
                update_data = {k: v for k, v in update.items() if k != "id"}
                
                if self.update_listing(listing_id, update_data):
                    success_count += 1
            
            logger.info(f"Batch update completed: {success_count}/{len(updates)} successful")
            return success_count == len(updates)
            
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Get total count
            total_result = self.client.table("listings_v2").select("id", count="exact").execute()
            total_count = total_result.count if total_result.count else 0
            
            # Get count with embeddings
            embedded_result = self.client.table("listings_v2").select("id", count="exact").not_.is_("embedding", "null").execute()
            embedded_count = embedded_result.count if embedded_result.count else 0
            
            # Get count with embedding_text
            text_result = self.client.table("listings_v2").select("id", count="exact").not_.eq("embedding_text", "").execute()
            text_count = text_result.count if text_result.count else 0
            
            return {
                "total_listings": total_count,
                "with_embeddings": embedded_count,
                "with_embedding_text": text_count,
                "embedding_coverage": f"{(embedded_count/total_count*100):.1f}%" if total_count > 0 else "0%",
                "text_coverage": f"{(text_count/total_count*100):.1f}%" if total_count > 0 else "0%"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            result = self.client.table("listings_v2").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
