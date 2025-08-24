import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_database():
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as conn:
            # Check total properties
            total = await conn.fetchval("SELECT COUNT(*) FROM listings_v2")
            print(f"Total properties in database: {total}")
            
            # Check properties with embeddings
            embedded = await conn.fetchval("SELECT COUNT(*) FROM listings_v2 WHERE embedding IS NOT NULL")
            print(f"Properties with embeddings: {embedded}")
            
            # Check properties by city
            cities = await conn.fetch("SELECT city, COUNT(*) FROM listings_v2 GROUP BY city")
            print("\nProperties by city:")
            for city, count in cities:
                print(f"  {city}: {count}")
            
            # Check properties by price range
            print("\nProperties by price range:")
            price_ranges = await conn.fetch("""
                SELECT 
                    CASE 
                        WHEN price_per_month <= 2000 THEN 'Under $2,000'
                        WHEN price_per_month <= 2500 THEN '$2,000-$2,500'
                        WHEN price_per_month <= 3000 THEN '$2,500-$3,000'
                        WHEN price_per_month <= 3500 THEN '$3,000-$3,500'
                        ELSE 'Over $3,500'
                    END as price_range,
                    COUNT(*) as count
                FROM listings_v2 
                WHERE price_per_month IS NOT NULL
                GROUP BY price_range
                ORDER BY 
                    CASE price_range
                        WHEN 'Under $2,000' THEN 1
                        WHEN '$2,000-$2,500' THEN 2
                        WHEN '$2,500-$3,000' THEN 3
                        WHEN '$3,000-$3,500' THEN 4
                        ELSE 5
                    END
            """)
            for price_range, count in price_ranges:
                print(f"  {price_range}: {count}")
            
            # Check properties by neighborhood
            print("\nProperties by neighborhood:")
            neighborhoods = await conn.fetch("SELECT neighborhood, COUNT(*) FROM listings_v2 WHERE neighborhood IS NOT NULL GROUP BY neighborhood")
            for neighborhood, count in neighborhoods:
                print(f"  {neighborhood}: {count}")
            
            # Check properties by property type
            print("\nProperties by property type:")
            property_types = await conn.fetch("SELECT property_type, COUNT(*) FROM listings_v2 WHERE property_type IS NOT NULL GROUP BY property_type")
            for prop_type, count in property_types:
                print(f"  {prop_type}: {count}")

if __name__ == "__main__":
    asyncio.run(check_database())
