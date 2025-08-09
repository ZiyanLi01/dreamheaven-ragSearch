#!/bin/bash

# DreamHeaven RAG API Setup Script

set -e

echo "🚀 Setting up DreamHeaven RAG API..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env with your actual credentials before proceeding!"
    echo "   Required: DATABASE_URL, OPENAI_API_KEY"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if we can connect to the database
echo "🔍 Testing database connection..."
python3 -c "
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

async def test_db():
    load_dotenv()
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await conn.execute('SELECT 1')
        await conn.close()
        print('✅ Database connection successful!')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

result = asyncio.run(test_db())
exit(0 if result else 1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Please check your DATABASE_URL in .env"
    exit 1
fi

# Check if pgvector extension exists
echo "🔍 Checking pgvector extension..."
python3 -c "
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

async def test_pgvector():
    load_dotenv()
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        await conn.execute('SELECT 1::vector')
        await conn.close()
        print('✅ pgvector extension is available!')
        return True
    except Exception as e:
        print(f'❌ pgvector extension not available: {e}')
        print('Please ensure pgvector is installed in your PostgreSQL database.')
        return False

result = asyncio.run(test_pgvector())
exit(0 if result else 1)
"

if [ $? -ne 0 ]; then
    echo "❌ pgvector extension is not available."
    echo "Please install pgvector in your PostgreSQL database."
    exit 1
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run database migration: Execute add_vector_column.sql in your Supabase SQL Editor"
echo "2. Generate embeddings: python embed_listings.py"
echo "3. Start the service: python main.py"
echo "4. Test the API: python test_rag_api.py"
echo ""
echo "The service will be available at: http://localhost:8001"
echo "API documentation: http://localhost:8001/docs"

