# DreamHeaven RAG API

A standalone FastAPI service for LLM-powered property search using Retrieval-Augmented Generation (RAG). This service provides semantic search over real estate listings using OpenAI embeddings and PostgreSQL with pgvector, enhanced with AI-generated explanations for search matches.

## Project Structure

```
dreamheaven-rag/
├── main.py                 # Main FastAPI application with PostgreSQL connection
├── main_supabase.py        # Alternative FastAPI app using Supabase client
├── embed_listings.py       # Script to generate embeddings for existing listings
├── test_rag_api.py         # Test script for API endpoints
├── setup.sh                # Automated setup script for environment
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration for containerization
├── docker-compose.yml      # Docker Compose configuration
├── add_vector_column.sql   # SQL script to add vector column to listings table
├── env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # This documentation file
├── server.log              # Application log file
├── ETL_PIPELINE_README.md  # Complete ETL pipeline documentation
├── test_etl_pipeline.py    # Test script for ETL pipeline
├── test_env_variables.py   # Environment variables test script
├── run_recent_listings_pipeline.py # Quick pipeline runner
├── run_missing_embeddings_update.py # Missing embeddings update runner
├── etl/                    # ETL pipeline components
│   ├── struct_tags.py      # Structured tags extraction
│   ├── embedding_text.py   # Embedding text generation
│   ├── embedding_pipeline.py # Complete embedding pipeline
│   └── config/             # ETL configuration files
│       ├── tags_struct_rules.yaml
│       └── text_extraction_keywords.yaml
├── jobs/                   # Database update jobs
│   ├── process_recent_listings.py # Main pipeline job for recent listings
│   ├── update_embeddings_pipeline.py # Complete pipeline job
│   ├── update_missing_embeddings.py # Missing embeddings job
│   └── update_embedding_text.py      # Legacy text-only job
├── scripts/                # Utility scripts
│   ├── supabase_manager.py # Database operations
│   ├── check_recent_listings.py # Check recent listings status
│   └── check_database_status.py # Database status checker
└── venv/                   # Python virtual environment (not in git)
```

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

#### Option A: Legacy Method (Basic)
```bash
python embed_listings.py
```

#### Option B: Enhanced ETL Pipeline (Recommended)
```bash
# Check current listings status
python scripts/check_recent_listings.py

# Process recent listings with complete pipeline
python jobs/process_recent_listings.py --dry-run --days-back 30  # Test first
python jobs/process_recent_listings.py --days-back 30  # Full update
```

The enhanced ETL pipeline provides:
- **Structured Tags**: Rule-based tag extraction from property data
- **Semantic Cues**: Advanced text analysis with 50+ keywords
- **Enhanced Embeddings**: Better quality embeddings using optimized text
- **Comprehensive Updates**: Updates embedding_text, embeddings, and tags

#### Option C: Quick Pipeline Runner
```bash
# Check environment and run pipeline
python run_recent_listings_pipeline.py
```

## 🔄 ETL Pipeline: Complete Embedding Generation

The ETL pipeline automatically processes listings to generate structured tags, embedding text, and embeddings for optimal RAG performance.

### **How the Pipeline Works**

1. **Automatic Discovery**: Uses `updated_at` timestamps to find recent listings
2. **Smart Detection**: Identifies listings missing tags, embedding_text, or embeddings
3. **Complete Processing**: Generates all three components in one operation
4. **Database Updates**: Updates listings with complete data

### **Pipeline Components**

- **Structured Tags**: Rule-based tags extracted from property data (location, amenities, features)
- **Embedding Text**: Optimized 500-character text with semantic cues and structured facts
- **Embeddings**: 1536-dimension vectors from OpenAI's text-embedding-3-small model

### **Checking Listings Status**

```bash
# Check all recent listings and their status
python scripts/check_recent_listings.py

# Check with custom time period
python scripts/check_recent_listings.py --days-back 14
```

### **Processing Recent Listings**

```bash
# Test run (no database changes)
python jobs/process_recent_listings.py --dry-run --days-back 7

# Process listings from last 7 days
python jobs/process_recent_listings.py --days-back 7

# Process listings from last 30 days
python jobs/process_recent_listings.py --days-back 30

# Process with verbose logging
python jobs/process_recent_listings.py --days-back 7 --verbose
```

### **Quick Pipeline Runner**

```bash
# Interactive pipeline runner with environment checks
python run_recent_listings_pipeline.py
```

### **Automated Processing**

For continuous processing, you can set up scheduled jobs:

```bash
# Daily processing (cron job)
0 2 * * * cd /path/to/dreamheaven-rag && python jobs/process_recent_listings.py --days-back 1

# Weekly processing
0 3 * * 0 cd /path/to/dreamheaven-rag && python jobs/process_recent_listings.py --days-back 7
```

### **Pipeline Output Example**

```
🚀 Starting Recent Listings Pipeline Processing...
📦 Processing 3 recent listings...

🔄 Processing listing 1/3: abc-123
   Title: Beautiful South-Facing Apartment...
   ✅ Success: 4 tags, 500 chars, 1536 dims

🎉 Recent listings pipeline processing completed!
📊 Final Statistics:
   Total processed: 3
   Successfully updated: 3
   Tags added: 3
   Embedding text added: 3
   Embeddings added: 3
```

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
| `reasons`