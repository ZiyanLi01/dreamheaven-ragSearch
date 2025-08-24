#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager
from config import Config
import asyncio

async def check_database_fields():
    config = Config()
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.initialize()
    
    # Get a sample listing
    query = "SELECT * FROM listings LIMIT 1"
    result = await db_manager.execute_query(query)
    
    if result:
        listing = result[0]
        print("=== DATABASE FIELDS CHECK ===")
        print("Available fields in database:")
        print("=" * 50)
        
        for key, value in listing.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        
        print("\nFields we're checking for:")
        print("  - pets_allowed")
        print("  - property_type")
        print("  - title")
        print("  - description")
        print("  - address")
        print("  - neighborhood")
        
        # Check specific fields
        print(f"\nSpecific field values:")
        print(f"  pets_allowed: {listing.get('pets_allowed', 'NOT FOUND')}")
        print(f"  property_type: {listing.get('property_type', 'NOT FOUND')}")
        print(f"  title: {listing.get('title', 'NOT FOUND')}")
        print(f"  description: {listing.get('description', 'NOT FOUND')}")
        print(f"  address: {listing.get('address', 'NOT FOUND')}")
        print(f"  neighborhood: {listing.get('neighborhood', 'NOT FOUND')}")
    else:
        print("No listings found in database")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_database_fields())
