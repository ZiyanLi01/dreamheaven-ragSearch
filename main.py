"""
DreamHeaven RAG API - Semantic Property Search Service
A standalone FastAPI service for LLM-powered property search using RAG.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import asyncpg
import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 8001))
HOST = os.getenv("HOST", "0.0.0.0")

if not DATABASE_URL or not OPENAI_API_KEY:
    raise ValueError("DATABASE_URL and OPENAI_API_KEY must be set in environment variables")

# Global database connection pool
db_pool: Optional[asyncpg.Pool] = None
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Pydantic Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language description of dream home")
    limit: Optional[int] = Field(10, description="Number of results to return (default: 10)")
    offset: Optional[int] = Field(0, description="Number of results to skip for pagination (default: 0)")

class ListingResult(BaseModel):
    id: str
    title: Optional[str] = None
    address: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    square_feet: Optional[int] = None
    garage_number: Optional[int] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")

class SearchResponse(BaseModel):
    results: List[ListingResult]
    query: str
    total_results: int

# Database Functions
async def create_db_pool():
    """Create database connection pool"""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database connection pool created successfully")
        
        # Test the connection and ensure pgvector is available
        async with db_pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("pgvector extension verified")
            
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise

async def close_db_pool():
    """Close database connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

async def get_db_connection():
    """Dependency to get database connection"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")
    return db_pool

# OpenAI Functions
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
        logger.error(f"Failed to get embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding")

# Search Functions
async def search_similar_listings(
    query_embedding: List[float], 
    limit: int = 10,
    offset: int = 0,
    pool: asyncpg.Pool = None
) -> List[Dict[str, Any]]:
    """Search for similar listings using vector similarity"""
    try:
        async with pool.acquire() as conn:
            # Convert embedding to pgvector format
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
            # Query for most similar listings using cosine similarity
            query = """
            SELECT 
                id,
                title,
                address,
                bedrooms,
                bathrooms,
                square_feet,
                garage_number,
                CASE 
                    WHEN property_listing_type = 'sale' THEN price_for_sale
                    WHEN property_listing_type = 'both' THEN price_per_month
                    WHEN property_listing_type = 'rent' THEN price_per_month
                    ELSE COALESCE(price_per_month, price_for_sale, price_per_night)
                END as price,
                CASE 
                    WHEN images IS NOT NULL AND array_length(images, 1) > 0 
                    THEN images[1] 
                    ELSE NULL 
                END as image_url,
                embedding <=> $1::vector as distance,
                1 - (embedding <=> $1::vector) as similarity_score
            FROM listings 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2 OFFSET $3
            """
            
            rows = await conn.fetch(query, embedding_str, limit, offset)
            
            results = []
            for row in rows:
                result = dict(row)
                # Ensure similarity_score is properly calculated
                if 'similarity_score' not in result:
                    result['similarity_score'] = 1 - result.get('distance', 1)
                results.append(result)
            
            return results
            
    except Exception as e:
        logger.error(f"Database search error: {e}")
        raise HTTPException(status_code=500, detail="Failed to search listings")

# FastAPI App Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting DreamHeaven RAG API...")
    await create_db_pool()
    yield
    # Shutdown
    logger.info("Shutting down DreamHeaven RAG API...")
    await close_db_pool()

# FastAPI App
app = FastAPI(
    title="DreamHeaven RAG API",
    description="Semantic property search using LLM embeddings and vector similarity",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dreamheaven-rag",
        "version": "1.0.0"
    }

@app.post("/ai-search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Perform semantic search on property listings using natural language query.
    
    Example query: "modern 3-bedroom condo in San Francisco with ocean view"
    """
    try:
        logger.info(f"Processing search query: {request.query}")
        
        # Generate embedding for the query
        query_embedding = await get_embedding(request.query)
        
        # Search for similar listings
        similar_listings = await search_similar_listings(
            query_embedding=query_embedding,
            limit=request.limit,
            offset=request.offset,
            pool=pool
        )
        
        # Convert results to response format
        results = [
            ListingResult(
                id=str(listing["id"]),
                title=listing.get("title"),
                address=listing.get("address"),
                bedrooms=listing.get("bedrooms"),
                bathrooms=listing.get("bathrooms"),
                square_feet=listing.get("square_feet"),
                garage_number=listing.get("garage_number"),
                price=listing.get("price"),
                image_url=listing.get("image_url"),
                similarity_score=float(listing.get("similarity_score", 0))
            )
            for listing in similar_listings
        ]
        
        logger.info(f"Found {len(results)} similar listings")
        
        return SearchResponse(
            results=results,
            query=request.query,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats(pool: asyncpg.Pool = Depends(get_db_connection)):
    """Get statistics about the vector database"""
    try:
        async with pool.acquire() as conn:
            # Count total listings and embedded listings
            total_query = "SELECT COUNT(*) as total FROM listings"
            embedded_query = "SELECT COUNT(*) as embedded FROM listings WHERE embedding IS NOT NULL"
            
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
        raise HTTPException(status_code=500, detail="Failed to get statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

