"""
DreamHeaven RAG API - Semantic Property Search Service
A standalone FastAPI service for LLM-powered property search using RAG with Supabase.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Service role key for admin operations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 8001))
HOST = os.getenv("HOST", "0.0.0.0")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
    raise ValueError("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and OPENAI_API_KEY must be set in environment variables")

# Global clients
supabase: Optional[Client] = None
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Pydantic Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language description of dream home")

class ListingResult(BaseModel):
    id: str
    title: Optional[str] = None
    address: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    garage_number: Optional[int] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")

class SearchResponse(BaseModel):
    results: List[ListingResult]
    query: str
    total_results: int

# Supabase Functions
def get_supabase_client():
    """Get Supabase client"""
    global supabase
    if not supabase:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

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
def search_similar_listings(query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """Search for similar listings using vector similarity with Supabase"""
    try:
        client = get_supabase_client()
        
        # Convert embedding to string format for Supabase
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Use Supabase's RPC function for vector similarity search
        # We'll need to create this function in Supabase first
        try:
            # Try using the vector similarity search
            result = client.rpc(
                'search_listings_by_embedding',
                {
                    'query_embedding': embedding_str,
                    'similarity_threshold': 0.1,
                    'match_count': limit
                }
            ).execute()
            
            if result.data:
                return result.data
            else:
                # Fallback: get all listings with embeddings and calculate similarity in Python
                return fallback_similarity_search(client, query_embedding, limit)
                
        except Exception as rpc_error:
            logger.warning(f"RPC search failed, using fallback: {rpc_error}")
            return fallback_similarity_search(client, query_embedding, limit)
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Failed to search listings")

def fallback_similarity_search(client: Client, query_embedding: List[float], limit: int) -> List[Dict[str, Any]]:
    """Fallback similarity search using Python cosine similarity"""
    import numpy as np
    
    # Get all listings with embeddings
    result = client.table("listings").select(
        "id, title, address, bedrooms, bathrooms, garage_number, price_for_sale, price_per_month, price, image_url, embedding"
    ).not_.is_("embedding", "null").execute()
    
    if not result.data:
        return []
    
    query_vec = np.array(query_embedding)
    similarities = []
    
    for listing in result.data:
        try:
            # Parse the embedding vector from string
            embedding_str = listing['embedding']
            if isinstance(embedding_str, str):
                # Remove brackets and split by comma
                embedding_str = embedding_str.strip('[]')
                embedding_vec = np.array([float(x.strip()) for x in embedding_str.split(',')])
            else:
                # Already a list
                embedding_vec = np.array(embedding_str)
            
            # Calculate cosine similarity
            cosine_sim = np.dot(query_vec, embedding_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(embedding_vec))
            
            # Determine price
            price = listing.get('price_for_sale') or listing.get('price_per_month') or listing.get('price')
            
            similarities.append({
                'id': listing['id'],
                'title': listing.get('title'),
                'address': listing.get('address'),
                'bedrooms': listing.get('bedrooms'),
                'bathrooms': listing.get('bathrooms'),
                'garage_number': listing.get('garage_number'),
                'price': price,
                'image_url': listing.get('image_url'),
                'similarity_score': float(cosine_sim),
                'distance': 1 - float(cosine_sim)
            })
        except Exception as e:
            logger.warning(f"Error processing listing {listing.get('id')}: {e}")
            continue
    
    # Sort by similarity score (highest first) and return top results
    similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
    return similarities[:limit]

# FastAPI App
app = FastAPI(
    title="DreamHeaven RAG API",
    description="Semantic property search using LLM embeddings and vector similarity",
    version="1.0.0"
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
    try:
        client = get_supabase_client()
        # Test connection
        result = client.table("listings").select("count", count="exact").limit(1).execute()
        return {
            "status": "healthy",
            "service": "dreamheaven-rag",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "dreamheaven-rag",
            "version": "1.0.0",
            "error": str(e)
        }

@app.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search on property listings using natural language query.
    
    Example query: "modern 3-bedroom condo in San Francisco with ocean view"
    """
    try:
        logger.info(f"Processing search query: {request.query}")
        
        # Generate embedding for the query
        query_embedding = await get_embedding(request.query)
        
        # Search for similar listings
        similar_listings = search_similar_listings(
            query_embedding=query_embedding,
            limit=5
        )
        
        # Convert results to response format
        results = [
            ListingResult(
                id=str(listing["id"]),
                title=listing.get("title"),
                address=listing.get("address"),
                bedrooms=listing.get("bedrooms"),
                bathrooms=listing.get("bathrooms"),
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
async def get_stats():
    """Get statistics about the vector database"""
    try:
        client = get_supabase_client()
        
        # Count total listings
        total_result = client.table("listings").select("count", count="exact").execute()
        total_listings = total_result.count if total_result.count is not None else 0
        
        # Count embedded listings
        embedded_result = client.table("listings").select("count", count="exact").not_.is_("embedding", "null").execute()
        embedded_listings = embedded_result.count if embedded_result.count is not None else 0
        
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

