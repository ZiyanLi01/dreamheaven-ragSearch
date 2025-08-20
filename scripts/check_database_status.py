#!/usr/bin/env python3
"""
Database Status Checker
Check the current status of listings_v2 table and identify missing embeddings
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.supabase_manager import SupabaseManager

def check_database_status():
    """Check the current status of the database"""
    print("🔍 Checking Database Status...")
    print("=" * 50)
    
    try:
        # Initialize Supabase manager
        supabase = SupabaseManager()
        
        # Test connection
        if not supabase.test_connection():
            print("❌ Failed to connect to database")
            return
        
        print("✅ Database connection successful")
        
        # Get overall statistics
        stats = supabase.get_stats()
        print(f"\n📊 Overall Statistics:")
        print(f"   Total listings: {stats.get('total_listings', 0)}")
        print(f"   With embeddings: {stats.get('with_embeddings', 0)}")
        print(f"   With embedding_text: {stats.get('with_embedding_text', 0)}")
        print(f"   Embedding coverage: {stats.get('embedding_coverage', '0%')}")
        print(f"   Text coverage: {stats.get('text_coverage', '0%')}")
        
        # Get detailed breakdown
        print(f"\n🔍 Detailed Analysis:")
        
        # Get listings without embeddings
        no_embeddings = supabase.get_listings_without_embeddings()
        print(f"   Listings without embeddings: {len(no_embeddings)}")
        
        if no_embeddings:
            print(f"   Sample IDs without embeddings:")
            for i, listing in enumerate(no_embeddings[:5]):
                updated_at = listing.get('updated_at', 'Unknown')
                print(f"     - {listing.get('id', 'No ID')} (updated: {updated_at})")
            if len(no_embeddings) > 5:
                print(f"     ... and {len(no_embeddings) - 5} more")
        
        # Get recent listings (last 30 days)
        print(f"\n📅 Recent Activity (Last 30 days):")
        try:
            # Get all listings and filter by recent updates
            all_listings = supabase.get_listings()
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            recent_listings = []
            for listing in all_listings:
                updated_at_str = listing.get('updated_at')
                if updated_at_str:
                    try:
                        # Parse the updated_at string
                        if 'T' in updated_at_str:
                            # ISO format
                            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                        else:
                            # Try other formats
                            updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                        
                        if updated_at > thirty_days_ago:
                            recent_listings.append(listing)
                    except:
                        continue
            
            print(f"   Recent listings (last 30 days): {len(recent_listings)}")
            
            # Check embeddings for recent listings
            recent_with_embeddings = [l for l in recent_listings if l.get('embedding')]
            recent_without_embeddings = [l for l in recent_listings if not l.get('embedding')]
            
            print(f"   Recent listings with embeddings: {len(recent_with_embeddings)}")
            print(f"   Recent listings without embeddings: {len(recent_without_embeddings)}")
            
            if recent_without_embeddings:
                print(f"   Recent listings needing embeddings:")
                for listing in recent_without_embeddings[:5]:
                    updated_at = listing.get('updated_at', 'Unknown')
                    title = listing.get('title', 'No title')[:50]
                    print(f"     - {listing.get('id', 'No ID')}: {title}... (updated: {updated_at})")
                if len(recent_without_embeddings) > 5:
                    print(f"     ... and {len(recent_without_embeddings) - 5} more")
        
        except Exception as e:
            print(f"   Error analyzing recent activity: {e}")
        
        # Get listings with empty embedding_text
        print(f"\n📝 Embedding Text Status:")
        try:
            listings_with_empty_text = []
            for listing in all_listings:
                embedding_text = listing.get('embedding_text', '')
                if not embedding_text or embedding_text.strip() == '':
                    listings_with_empty_text.append(listing)
            
            print(f"   Listings with empty embedding_text: {len(listings_with_empty_text)}")
            
            if listings_with_empty_text:
                print(f"   Sample listings with empty embedding_text:")
                for listing in listings_with_empty_text[:3]:
                    updated_at = listing.get('updated_at', 'Unknown')
                    title = listing.get('title', 'No title')[:50]
                    print(f"     - {listing.get('id', 'No ID')}: {title}... (updated: {updated_at})")
        
        except Exception as e:
            print(f"   Error analyzing embedding_text: {e}")
        
        print(f"\n✅ Database status check completed")
        
    except Exception as e:
        print(f"❌ Error checking database status: {e}")

if __name__ == "__main__":
    check_database_status()
