-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Add vector column to listings table for storing embeddings
-- OpenAI text-embedding-3-small produces 1536-dimensional vectors
ALTER TABLE listings 
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create index for fast similarity search
CREATE INDEX IF NOT EXISTS listings_embedding_idx 
ON listings USING ivfflat (embedding vector_cosine_ops);

-- Optional: Create a function to calculate text content for embedding
CREATE OR REPLACE FUNCTION get_listing_text_content(listing_row listings)
RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(listing_row.title, '') || ' ' ||
           COALESCE(listing_row.address, '') || ' ' ||
           COALESCE(listing_row.city, '') || ' ' ||
           COALESCE(listing_row.state, '') || ' ' ||
           COALESCE(listing_row.bedrooms::text, '0') || ' bedrooms ' ||
           COALESCE(listing_row.bathrooms::text, '0') || ' bathrooms ' ||
           COALESCE(listing_row.property_type, '') || ' ' ||
           COALESCE(listing_row.tags, '');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add comment for documentation
COMMENT ON COLUMN listings.embedding IS 'OpenAI text-embedding-3-small vector (1536 dimensions) for semantic search';

