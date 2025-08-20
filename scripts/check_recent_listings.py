#!/usr/bin/env python3
"""
Check Recent Listings
Check listings_v2 table for recent listings and identify missing tags, embedding_text, and embeddings
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.supabase_manager import SupabaseManager

def check_recent_listings():
    """Check recent listings in listings_v2 table"""
    print("🔍 Checking Recent Listings in listings_v2...")
    print("=" * 60)
    
    try:
        # Initialize Supabase manager
        supabase = SupabaseManager()
        
        # Test connection
        if not supabase.test_connection():
            print("❌ Failed to connect to database")
            return
        
        print("✅ Database connection successful")
        
        # Get all listings from listings_v2
        all_listings = supabase.get_listings()
        print(f"\n📊 Total listings in listings_v2: {len(all_listings)}")
        
        # Find recent listings (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_listings = []
        
        # Show all listings with their updated_at dates
        print(f"\n📅 All Listings with updated_at dates:")
        print("-" * 60)
        
        for listing in all_listings:
            updated_at_str = listing.get('updated_at', '')
            listing_id = listing.get('id', 'No ID')
            title = listing.get('title', 'No title')[:30]
            
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
                    
                    print(f"   {listing_id}: {title}... - {updated_at}")
                    
                    # Make sure we're comparing timezone-aware datetimes
                    if updated_at.tzinfo is None:
                        updated_at = updated_at.replace(tzinfo=timezone.utc)
                    
                    if updated_at > thirty_days_ago:
                        recent_listings.append(listing)
                except Exception as e:
                    print(f"   {listing_id}: {title}... - {updated_at_str} (parse error: {e})")
            else:
                print(f"   {listing_id}: {title}... - No updated_at")
        
        print(f"\n📅 Recent listings (last 30 days): {len(recent_listings)}")
        
        if not recent_listings:
            print("ℹ️  No recent listings found in the last 7 days")
            return
        
        # Analyze each recent listing
        print(f"\n🔍 Analyzing Recent Listings:")
        print("-" * 60)
        
        listings_needing_updates = []
        
        for i, listing in enumerate(recent_listings, 1):
            listing_id = listing.get('id', 'No ID')
            title = listing.get('title', 'No title')[:50]
            updated_at = listing.get('updated_at', 'Unknown')
            
            # Check what's missing
            has_tags = listing.get('tags') and len(listing.get('tags', [])) > 0
            has_embedding_text = listing.get('embedding_text') and listing.get('embedding_text', '').strip() != ''
            has_embedding = listing.get('embedding') is not None
            
            print(f"\n📋 Listing {i}: {listing_id}")
            print(f"   Title: {title}...")
            print(f"   Updated: {updated_at}")
            print(f"   Status:")
            print(f"     ✅ Tags: {'Yes' if has_tags else '❌ Missing'}")
            print(f"     ✅ Embedding Text: {'Yes' if has_embedding_text else '❌ Missing'}")
            print(f"     ✅ Embedding: {'Yes' if has_embedding else '❌ Missing'}")
            
            # Check if listing needs updates
            needs_update = not has_tags or not has_embedding_text or not has_embedding
            
            if needs_update:
                listings_needing_updates.append(listing)
                print(f"   🔄 Needs Update: YES")
            else:
                print(f"   ✅ Complete: All fields present")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"   Recent listings found: {len(recent_listings)}")
        print(f"   Listings needing updates: {len(listings_needing_updates)}")
        print(f"   Complete listings: {len(recent_listings) - len(listings_needing_updates)}")
        
        if listings_needing_updates:
            print(f"\n🔄 Listings that need pipeline processing:")
            for listing in listings_needing_updates:
                listing_id = listing.get('id', 'No ID')
                title = listing.get('title', 'No title')[:50]
                print(f"   - {listing_id}: {title}...")
        
        print(f"\n✅ Recent listings check completed")
        return listings_needing_updates
        
    except Exception as e:
        print(f"❌ Error checking recent listings: {e}")
        return []

if __name__ == "__main__":
    check_recent_listings()
