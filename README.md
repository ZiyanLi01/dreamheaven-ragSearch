# DreamHeaven RAG - Real Estate Search Engine

A production-ready RAG (Retrieval-Augmented Generation) system for real estate search with semantic understanding and hybrid search capabilities.

## Features

- **Semantic Search**: AI-powered property search with natural language queries
- **Hybrid Search**: Combines vector embeddings with structured filtering
- **Intent Extraction**: Automatically extracts property types, neighborhoods, requirements
- **Real-time Scoring**: Intelligent ranking of search results
- **Production Ready**: Optimized for Railway deployment

## Architecture

- **Backend**: FastAPI with Python 3.11+
- **Database**: Supabase (PostgreSQL with vector extensions)
- **Embeddings**: OpenAI text-embedding-3-small
- **Search**: Hybrid vector + structured search
- **Deployment**: Railway with Docker

## Requirements

- Python 3.11+
- Supabase account
- OpenAI API key

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
```

## Railway Deployment

1. **Connect Repository**: Link your GitHub repo to Railway
2. **Set Environment Variables**: Configure all required env vars in Railway dashboard
3. **Deploy**: Railway will automatically build and deploy using the Dockerfile

## Database Setup

The system requires a `listings_v2` table with:
- `embedding` (vector): 1536-dimensional embeddings
- `embedding_text` (text): Optimized search text
- `tags` (array): Property tags for filtering

## API Endpoints

- `POST /ai-search`: Main search endpoint
- `GET /health`: Health check

## Production Files

- `main.py`: FastAPI application entry point
- `search_engine.py`: Core search functionality
- `database.py`: Database operations
- `intent_extractor.py`: Query intent extraction
- `scoring.py`: Result scoring algorithms
- `models.py`: Data models
- `config.py`: Configuration management
- `scripts/supabase_manager.py`: Database connection manager
- `etl/`: ETL modules for data processing

## Docker

The application is containerized and ready for Railway deployment:

```bash
docker build -t dreamheaven-rag .
docker run -p 8000:8000 dreamheaven-rag
```

## Performance

- **Search Speed**: < 2 seconds for complex queries
- **Database**: 3,080+ listings with 100% embedding coverage
- **Scalability**: Designed for Railway's auto-scaling
