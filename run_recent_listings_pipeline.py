#!/usr/bin/env python3
"""
Recent Listings Pipeline Runner
Process the 6 recent listings in listings_v2 with complete pipeline
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please set these variables in your .env file:")
        print("   1. Copy env.example to .env")
        print("   2. Fill in your actual values:")
        print("      - SUPABASE_URL: Your Supabase project URL")
        print("      - SUPABASE_SERVICE_ROLE_KEY: Your Supabase service role key")
        print("      - OPENAI_API_KEY: Your OpenAI API key")
        print("   3. Run this script again")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Main function to process recent listings"""
    print("🚀 Recent Listings Pipeline Runner")
    print("=" * 50)
    print("This will process the 6 recent listings in listings_v2 table")
    print("with the complete pipeline: tags, embedding_text, and embeddings")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        return
    
    print("\n🔍 Step 1: Checking recent listings...")
    try:
        from scripts.check_recent_listings import check_recent_listings
        check_recent_listings()
    except Exception as e:
        print(f"❌ Error checking recent listings: {e}")
        return
    
    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. Review the recent listings status above")
    print("2. Run the pipeline processing:")
    print("   python jobs/process_recent_listings.py --dry-run")
    print("3. If the dry run looks good, run the actual processing:")
    print("   python jobs/process_recent_listings.py")
    print("\n📖 Available options:")
    print("   --dry-run          : Test without making changes")
    print("   --days-back N      : Consider listings from last N days (default: 7)")
    print("   --check-only       : Only check, don't process")
    print("   --verbose          : Enable detailed logging")
    print("\n🎯 For the 6 recent listings, use:")
    print("   python jobs/process_recent_listings.py --dry-run --days-back 30")
    print("   python jobs/process_recent_listings.py --days-back 30")

if __name__ == "__main__":
    main()
