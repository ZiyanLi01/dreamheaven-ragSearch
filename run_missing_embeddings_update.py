#!/usr/bin/env python3
"""
Missing Embeddings Update Runner
Helper script to update all missing embeddings based on updated_at field
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
    """Main function to run the missing embeddings update"""
    print("🚀 Missing Embeddings Update Runner")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        return
    
    print("\n🔍 Step 1: Checking database status...")
    try:
        from scripts.check_database_status import check_database_status
        check_database_status()
    except Exception as e:
        print(f"❌ Error checking database status: {e}")
        return
    
    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. Review the database status above")
    print("2. Run the missing embeddings update:")
    print("   python jobs/update_missing_embeddings.py --dry-run --limit 5")
    print("3. If the dry run looks good, run the full update:")
    print("   python jobs/update_missing_embeddings.py")
    print("\n📖 Available options:")
    print("   --dry-run          : Test without making changes")
    print("   --limit N          : Process only N listings")
    print("   --batch-size N     : Process N listings per batch")
    print("   --days-back N      : Consider listings from last N days as 'recent'")
    print("   --no-prioritize    : Don't prioritize recent listings")
    print("   --verbose          : Enable detailed logging")

if __name__ == "__main__":
    main()
