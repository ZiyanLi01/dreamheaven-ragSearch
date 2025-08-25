"""
DreamHeaven RAG API - Semantic Property Search Service
A standalone FastAPI service for LLM-powered property search using RAG.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Import our modular components
from search_engine import SearchEngine
from models import SearchRequest, SearchResponse, ListingResult
from database import DatabaseManager
from config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize configuration
config = Config()

# Global instances
db_manager: Optional[DatabaseManager] = None
search_engine: Optional[SearchEngine] = None
openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

# FastAPI App Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global db_manager, search_engine
    
    # Startup
    logger.info("Starting DreamHeaven RAG API...")
    
    # Initialize database manager
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.initialize()
    
    # Initialize search engine
    search_engine = SearchEngine(db_manager, openai_client)
    
    logger.info("DreamHeaven RAG API started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down DreamHeaven RAG API...")
    if db_manager:
        await db_manager.close()
    logger.info("DreamHeaven RAG API shutdown complete")

# FastAPI App
app = FastAPI(
    title="DreamHeaven RAG API",
    description="Enhanced semantic property search using LLM embeddings, intent extraction, and reranking",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://dreamheaven.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "https://www.nestvector.com",  # Your custom domain
        "https://nestvector.com",  # Also allow without www
        FRONTEND_ORIGIN,  # Production frontend from environment variable
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Dependency to get database connection
async def get_db_connection():
    """Dependency to get database connection"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database manager not initialized")
    return db_manager

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dreamheaven-rag-enhanced",
        "version": "2.0.0"
    }

@app.post("/ai-search", response_model=SearchResponse)
async def ai_search(
    request: SearchRequest,
    db: DatabaseManager = Depends(get_db_connection)
):
    """
    Perform improved house listing recommendation using the advanced algorithm.
    
    Features:
    - Permanent hard constraints (red lines)
    - Progressive relaxation strategy
    - Adaptive scoring based on query information density
    - Diversity control
    - Detailed explanations with relaxation info
    
    Example query: "3-bedroom house in San Francisco under $1.2M with garage, cannot exceed budget"
    """
    try:
        logger.info(f"Processing AI search query: {request.query}")
        
        if not search_engine:
            raise HTTPException(status_code=500, detail="Search engine not initialized")
        
        # Perform search using the search engine
        results = await search_engine.search(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            generate_reasons=request.reasons,
            structured_filters=request.get_structured_filters()
        )
        
        logger.info(f"AI search completed with {len(results.items)} results")
        return results
        
    except Exception as e:
        logger.error(f"AI search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/stats")
async def get_stats(db: DatabaseManager = Depends(get_db_connection)):
    """Get statistics about the vector database"""
    try:
        stats = await db.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)

