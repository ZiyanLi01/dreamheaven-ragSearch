"""
Database management module for DreamHeaven RAG API
"""

import logging
import asyncpg
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
            
            # Test the connection and ensure pgvector is available
            async with self.pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info("pgvector extension verified")
                
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            async with self.pool.acquire() as conn:
                # Count total listings and embedded listings
                total_query = "SELECT COUNT(*) as total FROM listings_v2"
                embedded_query = "SELECT COUNT(*) as embedded FROM listings_v2 WHERE embedding IS NOT NULL"
                
                total_result = await conn.fetchrow(total_query)
                embedded_result = await conn.fetchrow(embedded_query)
                
                total_listings = total_result["total"] if total_result else 0
                embedded_listings = embedded_result["embedded"] if embedded_result else 0
                
                return {
                    "total_listings": total_listings,
                    "embedded_listings": embedded_listings,
                    "embedding_coverage": f"{(embedded_listings/total_listings*100):.1f}%" if total_listings > 0 else "0%"
                }
        except Exception as e:
            logger.error(f"Stats query failed: {e}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI's text-embedding-3-small model"""
        # This method will be implemented in the search engine
        # as it requires OpenAI client
        raise NotImplementedError("Use SearchEngine.get_embedding() instead")
    
    async def vector_search(self, embedding: List[float], candidate_ids: List[str], top_k: int = 100) -> List[Dict[str, Any]]:
        """Perform vector search on filtered candidates or entire database if no candidates provided"""
        try:
            if not candidate_ids:
                logger.info("No candidate IDs provided, performing full database vector search")
                # Search entire database
                embedding_str = f"[{','.join(map(str, embedding))}]"
                
                query = f"""
                SELECT 
                    id, title, address, bedrooms, bathrooms, square_feet,
                    garage_number, has_parking_lot, property_type,
                    price_for_sale, price_per_month,
                    has_yard, school_rating, crime_index, facing,
                    shopping_idx, grocery_idx, tags, embedding_text,
                    city, state, country, neighborhood,
                    description, amenities, host_id, is_available, is_featured,
                    latitude, longitude, rating, review_count,
                    property_listing_type, year_built, year_renovated,
                    created_at, updated_at,
                    CASE 
                        WHEN property_listing_type = 'sale' THEN price_for_sale
                        WHEN property_listing_type = 'both' THEN price_per_month
                        WHEN property_listing_type = 'rent' THEN price_per_month
                        ELSE COALESCE(price_per_month, price_for_sale)
                    END as price,
                    images,
                    embedding <=> $1::vector as distance,
                    1 - (embedding <=> $1::vector) as similarity_score
                FROM listings_v2 
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT {top_k}
                """
                
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(query, embedding_str)
                    vector_results = [dict(row) for row in rows]
                    
                    logger.info(f"Full database vector search returned {len(vector_results)} candidates")
                    
                    return vector_results
            
            logger.info(f"Vector search on {len(candidate_ids)} candidates, top_k={top_k}")
            
            # Convert embedding to pgvector format
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            # Create placeholders for candidate IDs
            id_placeholders = ','.join([f"${i+2}" for i in range(len(candidate_ids))])
            
            query = f"""
            SELECT 
                id, title, address, bedrooms, bathrooms, square_feet,
                garage_number, has_parking_lot, property_type,
                price_for_sale, price_per_month,
                has_yard, school_rating, crime_index, facing,
                shopping_idx, grocery_idx, tags, embedding_text,
                city, state, country, neighborhood,
                description, amenities, host_id, is_available, is_featured,
                latitude, longitude, rating, review_count,
                property_listing_type, year_built, year_renovated,
                created_at, updated_at,
                CASE 
                    WHEN property_listing_type = 'sale' THEN price_for_sale
                    WHEN property_listing_type = 'both' THEN price_per_month
                    WHEN property_listing_type = 'rent' THEN price_per_month
                    ELSE COALESCE(price_per_month, price_for_sale)
                END as price,
                images,
                embedding <=> $1::vector as distance,
                1 - (embedding <=> $1::vector) as similarity_score
            FROM listings_v2 
            WHERE id IN ({id_placeholders})
            ORDER BY embedding <=> $1::vector
            LIMIT {top_k}
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, embedding_str, *candidate_ids)
                vector_results = [dict(row) for row in rows]
                
                logger.info(f"Vector search returned {len(vector_results)} candidates")
                
                return vector_results
                
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            raise
    
    async def execute_query(self, query: str, *params) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    async def execute_query_single(self, query: str, *params) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result as dictionary"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
