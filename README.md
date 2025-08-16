# DreamHeaven RAG API

A standalone FastAPI service for LLM-powered property search using Retrieval-Augmented Generation (RAG). This service provides semantic search over real estate listings using OpenAI embeddings and PostgreSQL with pgvector, enhanced with AI-generated explanations for search matches.

## Features

- **Semantic Search**: Natural language property search using OpenAI embeddings
- **Vector Similarity**: Fast similarity search using pgvector and cosine similarity
- **AI-Generated Reasons**: Intelligent explanations for why each property matches the query
- **RESTful API**: Clean FastAPI endpoints with automatic documentation
- **Batch Embedding**: One-time embedding generation for existing listings
- **Docker Support**: Containerized deployment with health checks
- **Pagination**: Support for large result sets with limit/offset
- **Feature Flags**: Optional generation with `reasons` parameter

## Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- OpenAI API key
- Supabase account with existing listings table

## Quick Start

### 1. Setup Environment

```bash
# Clone or navigate to the project directory
cd /Users/ziyanli/productMVP/dreamheaven-rag

# Copy and configure environment variables
cp env.example .env
# Edit .env with your actual credentials
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

First, add the vector column to your existing listings table:

```bash
# Execute the SQL script in your Supabase SQL Editor
cat add_vector_column.sql
```

Or run it directly if you have psql:
```bash
psql $DATABASE_URL -f add_vector_column.sql
```

### 4. Generate Embeddings

Batch embed all existing listings:

```bash
python embed_listings.py
```

This will:
- Fetch all listings without embeddings
- Generate text descriptions for each listing
- Create embeddings using OpenAI's text-embedding-3-small
- Store embeddings in the vector column

### 5. Run the Service

#### Development
```bash
python main.py
```

#### Production with Docker
```bash
# Build and run with docker-compose
docker-compose up --build

# Or run with Docker directly
docker build -t dreamheaven-rag .
docker run -p 8001:8001 --env-file .env dreamheaven-rag
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Semantic Search with AI Generation
```bash
POST /ai-search
Content-Type: application/json

{
  "query": "modern 3-bedroom condo in San Francisco with ocean view",
  "limit": 10,
  "offset": 0,
  "reasons": true
}
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid-here",
      "title": "Modern Condo with Ocean Views",
      "address": "123 Ocean St",
      "bedrooms": 3,
      "bathrooms": 2,
      "square_feet": 1500,
      "garage_number": 1,
      "price": 850000,
      "image_url": "https://example.com/image.jpg",
      "similarity_score": 0.85,
      "reason": "• Modern amenities and contemporary design\n• Stunning ocean views from multiple rooms\n• Prime San Francisco location with easy access to downtown"
    }
  ],
  "query": "modern 3-bedroom condo in San Francisco with ocean view",
  "page": 1,
  "limit": 10,
  "has_more": true,
  "generation_error": false
}
```

### Statistics
```bash
GET /stats
```

Returns information about embedding coverage and total listings.

## AI Generation Features

### Reason Generation

The API can generate intelligent explanations for why each property matches the user's query:

- **Model**: Uses GPT-4o-mini for fast, cost-effective generation
- **Format**: Top 3 bullet-pointed reasons
- **Content**: Focuses on key matching factors (location, features, price)
- **Fallback**: Returns empty reasons if generation fails

### Generation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reasons` | boolean | true | Enable/disable AI reason generation |

### Generation Examples

**With AI reasons (default):**
```bash
curl -X POST "http://localhost:8001/ai-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "luxury apartment", "limit": 2, "reasons": true}'
```

**Without AI reasons (faster):**
```bash
curl -X POST "http://localhost:8001/ai-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "luxury apartment", "limit": 2, "reasons": false}'
```

### Error Handling

If generation fails, the API continues to work with empty reasons:
```json
{
  "items": [...],
  "generation_error": true
}
```

## Pagination

The AI search endpoint supports pagination for better performance and user experience:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Number of results to return |
| `offset` | integer | 0 | Number of results to skip |

### Pagination Examples

**First page (10 results):**
```bash
curl -X POST "http://localhost:8001/ai-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "apartment in downtown", "limit": 10, "offset": 0}'
```

**Load more (next 5 results):**
```bash
curl -X POST "http://localhost:8001/ai-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "apartment in downtown", "limit": 5, "offset": 10}'
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `PORT` | Service port (default: 8001) | No |
| `HOST` | Service host (default: 0.0.0.0) | No |

## Example Environment File

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres.your-ref:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Service Configuration
PORT=8001
HOST=0.0.0.0
```

## Testing the Service

### Test Health Check
```bash
curl http://localhost:8001/health
```

### Test Semantic Search with Generation
```bash
curl -X POST "http://localhost:8001/ai-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "luxury 4-bedroom house with pool in Beverly Hills", "limit": 10, "offset": 0, "reasons": true}'
```

### Test Statistics
```bash
curl http://localhost:8001/stats
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   RAG API        │───▶│   Supabase      │
│   (React)       │    │   (FastAPI)      │    │   (PostgreSQL)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   OpenAI API     │
                       │ (Embeddings +    │
                       │  Generation)     │
                       └──────────────────┘
```

## Deployment Options

### Local Development
```bash
python main.py
```

### Docker Standalone
```bash
docker build -t dreamheaven-rag .
docker run -p 8001:8001 --env-file .env dreamheaven-rag
```

### Docker Compose
```bash
docker-compose up --build
```

### Production Considerations

1. **Rate Limiting**: Implement rate limiting for the search endpoint
2. **Caching**: Add Redis for embedding and generation cache
3. **Monitoring**: Add logging and metrics collection
4. **Security**: Configure CORS properly for production
5. **Scaling**: Use multiple instances behind a load balancer
6. **Cost Management**: Monitor OpenAI API usage for generation

## Troubleshooting

### Common Issues

1. **pgvector not found**: Ensure the vector extension is installed in PostgreSQL
2. **OpenAI rate limits**: Reduce batch size in `embed_listings.py`
3. **Database connection**: Check DATABASE_URL format and credentials
4. **No embeddings**: Run `embed_listings.py` to generate embeddings
5. **Generation errors**: Check OpenAI API key and quota limits

### Logs

Check application logs for detailed error messages:
```bash
# Development
python main.py

# Docker
docker-compose logs dreamheaven-rag
```

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation as needed
4. Ensure Docker builds successfully

## License

MIT License - see LICENSE file for details.

