"""
Batch embedding script for existing listings in Supabase.
This script generates embeddings for all listings and stores them in the vector column.

Rate-limiting improvements:
- Process 50 listings per batch
- 2-second delay between individual API requests  
- 5-second delay between batches
- Automatic resume capability (processes only listings without embeddings)
- Better error handling for quota limits
"""

import os
import asyncio
import logging
from typing import List, Dict, Any
import asyncpg
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BATCH_SIZE = 50  # Process listings in batches to avoid rate limits
REQUEST_DELAY = 2.0  # Delay between individual API requests (seconds)

if not DATABASE_URL or not OPENAI_API_KEY:
    raise ValueError("DATABASE_URL and OPENAI_API_KEY must be set in environment variables")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def get_embedding(text: str) -> List[float]:
    """Get embedding for text using OpenAI's text-embedding-3-small model"""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to get embedding for text: {text[:100]}... Error: {e}")
        return None

def create_listing_text(listing: Dict[str, Any]) -> str:
    """Create a text representation of a listing for embedding"""
    components = []
    
    # Add title if available
    if listing.get('title'):
        components.append(listing['title'])
    
    # Add property type and listing type
    if listing.get('property_type'):
        components.append(f"{listing['property_type']} property")
    
    if listing.get('property_listing_type'):
        listing_type = listing['property_listing_type']
        if listing_type == 'both':
            components.append("for sale or rent")
        else:
            components.append(f"for {listing_type}")
    
    # Add location information
    location_parts = []
    if listing.get('address'):
        location_parts.append(listing['address'])
    if listing.get('city'):
        location_parts.append(listing['city'])
    if listing.get('state'):
        location_parts.append(listing['state'])
    
    if location_parts:
        components.append(f"located at {', '.join(location_parts)}")
    
    # Add property details
    if listing.get('bedrooms'):
        components.append(f"{listing['bedrooms']} bedroom{'s' if listing['bedrooms'] != 1 else ''}")
    
    if listing.get('bathrooms'):
        components.append(f"{listing['bathrooms']} bathroom{'s' if listing['bathrooms'] != 1 else ''}")
    
    if listing.get('square_feet'):
        components.append(f"{listing['square_feet']} square feet")
    
    if listing.get('garage_number'):
        components.append(f"{listing['garage_number']} garage{'s' if listing['garage_number'] != 1 else ''}")
    
    # Add amenities
    amenities = []
    if listing.get('has_yard'):
        amenities.append("yard")
    if listing.get('has_parking_lot'):
        amenities.append("parking lot")
    
    if amenities:
        components.append(f"with {', '.join(amenities)}")
    
    # Add price information based on listing type
    listing_type = listing.get('property_listing_type', '').lower()
    
    if listing_type == 'both':
        # For both rent and sale, prioritize monthly rent price
        if listing.get('price_per_month'):
            components.append(f"rent ${listing['price_per_month']:,.0f} per month")
        elif listing.get('price_for_sale'):
            components.append(f"also available for sale at ${listing['price_for_sale']:,.0f}")
    elif listing_type == 'rent':
        # For rent only, use monthly price
        if listing.get('price_per_month'):
            components.append(f"rent ${listing['price_per_month']:,.0f} per month")
        elif listing.get('price_per_night'):
            components.append(f"${listing['price_per_night']:,.0f} per night")
    elif listing_type == 'sale':
        # For sale only, use sale price
        if listing.get('price_for_sale'):
            components.append(f"priced at ${listing['price_for_sale']:,.0f}")
    else:
        # Fallback: try any available price
        if listing.get('price_per_month'):
            components.append(f"rent ${listing['price_per_month']:,.0f} per month")
        elif listing.get('price_for_sale'):
            components.append(f"priced at ${listing['price_for_sale']:,.0f}")
        elif listing.get('price_per_night'):
            components.append(f"${listing['price_per_night']:,.0f} per night")
    
    # Add amenities if available
    if listing.get('amenities') and listing['amenities']:
        amenities_str = ', '.join(listing['amenities']) if isinstance(listing['amenities'], list) else str(listing['amenities'])
        components.append(f"amenities: {amenities_str}")
    
    return ". ".join(components) + "."

async def fetch_listings_without_embeddings(conn: asyncpg.Connection, limit: int = None) -> List[Dict[str, Any]]:
    """Fetch listings that don't have embeddings yet"""
    query = """
    SELECT 
        id, title, address, city, state, property_type, property_listing_type,
        bedrooms, bathrooms, square_feet, garage_number, has_yard, has_parking_lot,
        price_per_night, price_for_sale, price_per_month, amenities
    FROM listings 
    WHERE embedding IS NULL
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    rows = await conn.fetch(query)
    return [dict(row) for row in rows]

async def update_listing_embedding(conn: asyncpg.Connection, listing_id: str, embedding: List[float]):
    """Update a listing with its embedding"""
    try:
        embedding_str = f"[{','.join(map(str, embedding))}]"
        await conn.execute(
            "UPDATE listings SET embedding = $1::vector WHERE id = $2",
            embedding_str, listing_id
        )
        return True
    except Exception as e:
        logger.error(f"Failed to update embedding for listing {listing_id}: {e}")
        return False

async def process_batch(conn: asyncpg.Connection, listings: List[Dict[str, Any]]):
    """Process a batch of listings"""
    logger.info(f"Processing batch of {len(listings)} listings...")
    
    for i, listing in enumerate(listings):
        try:
            # Create text representation
            listing_text = create_listing_text(listing)
            logger.debug(f"Listing {listing['id']}: {listing_text[:100]}...")
            
            # Get embedding
            embedding = await get_embedding(listing_text)
            if embedding is None:
                logger.warning(f"Skipping listing {listing['id']} due to embedding failure")
                continue
            
            # Update database
            success = await update_listing_embedding(conn, listing['id'], embedding)
            if success:
                logger.info(f"Updated embedding for listing {listing['id']} ({i+1}/{len(listings)})")
            else:
                logger.warning(f"Failed to update embedding for listing {listing['id']}")
            
            # Longer delay to respect rate limits and avoid quota issues
            await asyncio.sleep(REQUEST_DELAY)
            
            # Log progress within batch
            if (i + 1) % 10 == 0:
                logger.info(f"  Batch progress: {i+1}/{len(listings)} completed")
            
        except Exception as e:
            logger.error(f"Error processing listing {listing['id']}: {e}")
            # Check if it's a quota/rate limit error
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                logger.error("Hit rate limit or quota. Stopping batch processing.")
                logger.info(f"Successfully processed {i} listings in this batch before hitting limit.")
                break
            continue

async def main():
    """Main function to batch embed all listings"""
    logger.info("Starting batch embedding process...")
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Check if vector extension is enabled
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Get total count of listings without embeddings
        total_result = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM listings WHERE embedding IS NULL"
        )
        total_count = total_result['count'] if total_result else 0
        logger.info(f"Found {total_count} listings without embeddings")
        
        if total_count == 0:
            logger.info("All listings already have embeddings!")
            return
        
        # Process in batches with progress tracking
        processed = 0
        batch_number = 1
        
        while processed < total_count:
            # Fetch next batch
            listings = await fetch_listings_without_embeddings(conn, BATCH_SIZE)
            
            if not listings:
                logger.info("No more listings to process")
                break
            
            logger.info(f"Starting batch {batch_number} with {len(listings)} listings...")
            
            # Process batch
            await process_batch(conn, listings)
            
            processed += len(listings)
            progress_percent = (processed / total_count) * 100
            logger.info(f"✅ Batch {batch_number} completed! Progress: {processed}/{total_count} listings ({progress_percent:.1f}%)")
            
            # Add delay between batches to be extra safe
            if processed < total_count:
                logger.info(f"Waiting 5 seconds before next batch...")
                await asyncio.sleep(5.0)
            
            batch_number += 1
        
        # Final statistics
        embedded_result = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM listings WHERE embedding IS NOT NULL"
        )
        embedded_count = embedded_result['count'] if embedded_result else 0
        
        logger.info(f"Embedding complete! {embedded_count} listings now have embeddings.")
        
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

