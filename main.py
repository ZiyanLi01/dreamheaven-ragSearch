"""
DreamHeaven RAG API - Semantic Property Search Service
A standalone FastAPI service for LLM-powered property search using RAG.
"""

import os
import asyncio
import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager
from dataclasses import dataclass

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

# Intent Extraction Configuration
@dataclass
class SearchIntent:
    # Hard filters
    city: Optional[str] = None
    state: Optional[str] = None
    max_price_sale: Optional[float] = None
    max_price_rent: Optional[float] = None
    min_beds: Optional[int] = None
    min_baths: Optional[int] = None
    garage_required: Optional[bool] = None
    property_type: Optional[str] = None
    
    # Soft preferences (for reranking)
    good_schools: bool = False
    parking: bool = False
    yard: bool = False
    walk_to_metro: bool = False
    modern: bool = False
    renovated: bool = False
    ocean_view: bool = False
    mountain_view: bool = False
    quiet: bool = False
    family_friendly: bool = False

# Intent extraction patterns
INTENT_PATTERNS = {
    # Cities and states
    'city_state': [
        r'\b(san francisco|sf|new york|nyc|los angeles|la|chicago|miami|seattle|boston|austin|denver|portland|atlanta|phoenix|las vegas|houston|dallas|philadelphia|washington dc|dc)\b',
        r'\b(california|ca|new york|ny|texas|tx|florida|fl|illinois|il|washington|wa|massachusetts|ma|colorado|co|oregon|or|georgia|ga|arizona|az|nevada|nv|pennsylvania|pa|virginia|va)\b'
    ],
    
    # Price ranges
    'price_sale': [
        r'\bunder\s+\$?([0-9,]+(?:k|m)?)\b',
        r'\bless than\s+\$?([0-9,]+(?:k|m)?)\b',
        r'\bmax\s+\$?([0-9,]+(?:k|m)?)\b',
        r'\bup to\s+\$?([0-9,]+(?:k|m)?)\b'
    ],
    'price_rent': [
        r'\brent\s+under\s+\$?([0-9,]+)\b',
        r'\brental\s+max\s+\$?([0-9,]+)\b'
    ],
    
    # Bedrooms and bathrooms
    'beds': [
        r'\b([1-5])\s*(?:bed|bedroom|br)s?\b',
        r'\b([1-5])\s*bed\b'
    ],
    'baths': [
        r'\b([1-4])\s*(?:bath|bathroom)\b',
        r'\b([1-4])\s*bath\b'
    ],
    
    # Property features
    'garage': [
        r'\bgarage\b',
        r'\bparking\b',
        r'\bcar space\b'
    ],
    'property_type': [
        r'\b(condo|apartment|house|townhouse|single family|multi family|duplex|loft|studio)\b'
    ],
    
    # Soft preferences
    'good_schools': [
        r'\bgood school\b',
        r'\bexcellent school\b',
        r'\bgreat school\b',
        r'\bhigh rated school\b'
    ],
    'parking': [
        r'\bparking\b',
        r'\bcar space\b',
        r'\bgarage\b'
    ],
    'yard': [
        r'\byard\b',
        r'\bgarden\b',
        r'\boutdoor space\b',
        r'\bbackyard\b'
    ],
    'walk_to_metro': [
        r'\bwalk to metro\b',
        r'\bwalking distance to transit\b',
        r'\bnear metro\b',
        r'\bclose to subway\b',
        r'\bwalk to train\b'
    ],
    'modern': [
        r'\bmodern\b',
        r'\bcontemporary\b',
        r'\bnew\b',
        r'\bupdated\b'
    ],
    'renovated': [
        r'\brenovated\b',
        r'\bremodeled\b',
        r'\bupdated\b',
        r'\bnewly renovated\b'
    ],
    'ocean_view': [
        r'\bocean view\b',
        r'\bwaterfront\b',
        r'\bsea view\b',
        r'\bwater view\b'
    ],
    'mountain_view': [
        r'\bmountain view\b',
        r'\bhills view\b',
        r'\bscenic view\b'
    ],
    'quiet': [
        r'\bquiet\b',
        r'\bpeaceful\b',
        r'\bcalm\b',
        r'\bno noise\b'
    ],
    'family_friendly': [
        r'\bfamily friendly\b',
        r'\bkid friendly\b',
        r'\bgood for family\b',
        r'\bsafe neighborhood\b'
    ]
}

def extract_search_intent(query: str) -> SearchIntent:
    """Extract structured search intent from natural language query"""
    query_lower = query.lower()
    intent = SearchIntent()
    
    # Extract city/state
    for pattern in INTENT_PATTERNS['city_state']:
        matches = re.findall(pattern, query_lower)
        if matches:
            match = matches[0]
            # Check if it's a state abbreviation
            if match in ['ca', 'ny', 'tx', 'fl', 'il', 'wa', 'ma', 'co', 'or', 'ga', 'az', 'nv', 'pa', 'va']:
                intent.state = match
            # Check if it's a full state name
            elif match in ['california', 'new york', 'texas', 'florida', 'illinois', 'washington', 'massachusetts', 'colorado', 'oregon', 'georgia', 'arizona', 'nevada', 'pennsylvania', 'virginia']:
                intent.state = match
            # Otherwise treat as city
            else:
                intent.city = match
    
    # Extract price ranges
    for pattern in INTENT_PATTERNS['price_sale']:
        matches = re.findall(pattern, query_lower)
        if matches:
            price_str = matches[0].replace(',', '')
            if 'k' in price_str:
                intent.max_price_sale = float(price_str.replace('k', '')) * 1000
            elif 'm' in price_str:
                intent.max_price_sale = float(price_str.replace('m', '')) * 1000000
            else:
                intent.max_price_sale = float(price_str)
    
    for pattern in INTENT_PATTERNS['price_rent']:
        matches = re.findall(pattern, query_lower)
        if matches:
            intent.max_price_rent = float(matches[0].replace(',', ''))
    
    # Extract bedrooms/bathrooms
    for pattern in INTENT_PATTERNS['beds']:
        matches = re.findall(pattern, query_lower)
        if matches:
            intent.min_beds = int(matches[0])
    
    for pattern in INTENT_PATTERNS['baths']:
        matches = re.findall(pattern, query_lower)
        if matches:
            intent.min_baths = int(matches[0])
    
    # Extract property type
    for pattern in INTENT_PATTERNS['property_type']:
        matches = re.findall(pattern, query_lower)
        if matches:
            intent.property_type = matches[0]
    
    # Extract soft preferences
    intent.garage_required = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['garage'])
    intent.good_schools = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['good_schools'])
    intent.parking = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['parking'])
    intent.yard = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['yard'])
    intent.walk_to_metro = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['walk_to_metro'])
    intent.modern = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['modern'])
    intent.renovated = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['renovated'])
    intent.ocean_view = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['ocean_view'])
    intent.mountain_view = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['mountain_view'])
    intent.quiet = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['quiet'])
    intent.family_friendly = any(re.search(pattern, query_lower) for pattern in INTENT_PATTERNS['family_friendly'])
    
    return intent

def build_exact_filter_conditions(intent: SearchIntent) -> Tuple[str, List[Any]]:
    """Build SQL WHERE conditions for exact matching (strict filters)"""
    conditions = ["embedding IS NOT NULL"]
    params = []
    param_count = 1
    
    # Exact address matching using city/state columns
    if intent.city:
        conditions.append(f"LOWER(city) = ${param_count}")
        params.append(intent.city.lower())
        param_count += 1
    
    if intent.state:
        conditions.append(f"LOWER(state) = ${param_count}")
        params.append(intent.state.lower())
        param_count += 1
    
    # Exact price filtering (no flexibility)
    if intent.max_price_sale:
        conditions.append(f"price_for_sale <= ${param_count}")
        params.append(intent.max_price_sale)
        param_count += 1
    
    if intent.max_price_rent:
        conditions.append(f"price_per_month <= ${param_count}")
        params.append(intent.max_price_rent)
        param_count += 1
    
    # Exact bedroom/bathroom filtering (no flexibility)
    if intent.min_beds:
        conditions.append(f"bedrooms >= ${param_count}")
        params.append(intent.min_beds)
        param_count += 1
    
    if intent.min_baths:
        conditions.append(f"bathrooms >= ${param_count}")
        params.append(intent.min_baths)
        param_count += 1
    
    # Exact garage requirement
    if intent.garage_required:
        conditions.append("(garage_number > 0 OR has_parking_lot = true)")
    
    # Exact property type matching
    if intent.property_type:
        conditions.append(f"LOWER(property_type) = ${param_count}")
        params.append(intent.property_type.lower())
        param_count += 1
    
    where_clause = " AND ".join(conditions)
    return where_clause, params

def build_relaxed_filter_conditions(intent: SearchIntent) -> Tuple[str, List[Any]]:
    """Build SQL WHERE conditions for relaxed filtering (flexible logic)"""
    conditions = ["embedding IS NOT NULL"]
    params = []
    param_count = 1
    
    # Improved address matching using city/state columns
    if intent.city:
        # Try exact city match first, then fallback to address text
        conditions.append(f"(LOWER(city) = ${param_count} OR LOWER(address) LIKE ${param_count + 1})")
        params.extend([intent.city.lower(), f"%{intent.city.lower()}%"])
        param_count += 2
    
    if intent.state:
        # Try exact state match first, then fallback to address text
        conditions.append(f"(LOWER(state) = ${param_count} OR LOWER(address) LIKE ${param_count + 1})")
        params.extend([intent.state.lower(), f"%{intent.state.lower()}%"])
        param_count += 2
    
    # Relaxed price filtering with fallback ranges
    if intent.max_price_sale:
        # Allow 20% flexibility in price range
        relaxed_price = intent.max_price_sale * 1.2
        conditions.append(f"(price_for_sale <= ${param_count} OR price_for_sale IS NULL)")
        params.append(relaxed_price)
        param_count += 1
    
    if intent.max_price_rent:
        # Allow 20% flexibility in rent range
        relaxed_rent = intent.max_price_rent * 1.2
        conditions.append(f"(price_per_month <= ${param_count} OR price_per_month IS NULL)")
        params.append(relaxed_rent)
        param_count += 1
    
    # Relaxed bedroom/bathroom filtering
    if intent.min_beds:
        # Allow 1 bedroom less than requested
        relaxed_beds = max(1, intent.min_beds - 1)
        conditions.append(f"(bedrooms >= ${param_count} OR bedrooms IS NULL)")
        params.append(relaxed_beds)
        param_count += 1
    
    if intent.min_baths:
        # Allow 0.5 bathroom less than requested
        relaxed_baths = max(1, intent.min_baths - 0.5)
        conditions.append(f"(bathrooms >= ${param_count} OR bathrooms IS NULL)")
        params.append(relaxed_baths)
        param_count += 1
    
    # Relaxed garage requirement
    if intent.garage_required:
        # Don't require garage, just prefer it
        conditions.append("(garage_number > 0 OR has_parking_lot = true OR garage_number IS NULL)")
    
    # Relaxed property type matching
    if intent.property_type:
        # Use broader property type matching
        property_type_mapping = {
            'condo': 'condo|apartment',
            'apartment': 'apartment|condo|unit',
            'house': 'house|home|single family|townhouse',
            'townhouse': 'townhouse|house|home',
            'loft': 'loft|studio|apartment'
        }
        
        if intent.property_type in property_type_mapping:
            pattern = property_type_mapping[intent.property_type]
            conditions.append(f"(LOWER(property_type) ~ ${param_count} OR LOWER(title) ~ ${param_count})")
            params.append(pattern)
        else:
            conditions.append(f"(LOWER(property_type) LIKE ${param_count} OR LOWER(title) LIKE ${param_count})")
            params.append(f"%{intent.property_type.lower()}%")
        param_count += 1
    
    where_clause = " AND ".join(conditions)
    return where_clause, params

def build_filter_conditions(intent: SearchIntent) -> Tuple[str, List[Any]]:
    """Build SQL WHERE conditions for hard filtering with relaxed logic (legacy function)"""
    return build_relaxed_filter_conditions(intent)

def calculate_reranking_score(similarity_score: float, listing: Dict[str, Any], intent: SearchIntent) -> float:
    """Calculate final reranking score with bonus weights"""
    base_score = similarity_score
    bonus = 0.0
    
    # Soft preference bonuses (using enhanced fields from listings_v2)
    if intent.good_schools:
        # Use school_rating if available, otherwise fallback to neighborhoods
        school_rating = listing.get('school_rating')
        if school_rating and school_rating >= 8:
            bonus += 0.08
        else:
            # Fallback: assume good schools if in good neighborhoods
            good_neighborhoods = ['pacific heights', 'marina', 'nob hill', 'russian hill', 'presidio heights']
            address_lower = listing.get('address', '').lower()
            if any(neighborhood in address_lower for neighborhood in good_neighborhoods):
                bonus += 0.08
    
    if intent.parking and (listing.get('garage_number', 0) > 0 or listing.get('has_parking_lot')):
        bonus += 0.05
    
    if intent.yard and listing.get('has_yard'):
        bonus += 0.05
    
    if intent.walk_to_metro:
        # Use shopping_idx as proxy for walkability
        shopping_idx = listing.get('shopping_idx')
        if shopping_idx and shopping_idx >= 7:
            bonus += 0.06
        else:
            # Fallback: assume walkable if in urban areas
            urban_areas = ['downtown', 'financial district', 'soma', 'mission', 'hayes valley']
            address_lower = listing.get('address', '').lower()
            if any(area in address_lower for area in urban_areas):
                bonus += 0.06
    
    if intent.modern:
        # Fallback: assume modern if built recently or has modern keywords in title
        title_lower = listing.get('title', '').lower()
        if any(word in title_lower for word in ['modern', 'contemporary', 'new', 'updated']):
            bonus += 0.04
    
    if intent.renovated:
        # Fallback: assume renovated if has renovation keywords
        title_lower = listing.get('title', '').lower()
        if any(word in title_lower for word in ['renovated', 'remodeled', 'updated', 'newly']):
            bonus += 0.04
    
    if intent.ocean_view:
        # Fallback: assume ocean view if near water
        water_areas = ['marina', 'pacific heights', 'presidio', 'richmond', 'sunset']
        address_lower = listing.get('address', '').lower()
        if any(area in address_lower for area in water_areas):
            bonus += 0.07
    
    if intent.mountain_view:
        # Fallback: assume mountain view if in elevated areas
        elevated_areas = ['nob hill', 'russian hill', 'pacific heights', 'presidio heights']
        address_lower = listing.get('address', '').lower()
        if any(area in address_lower for area in elevated_areas):
            bonus += 0.05
    
    if intent.quiet:
        # Use crime_index as proxy for quietness (lower crime = quieter)
        crime_index = listing.get('crime_index')
        if crime_index and crime_index <= 3:
            bonus += 0.03
        else:
            # Fallback: assume quiet if in residential areas
            quiet_areas = ['pacific heights', 'presidio heights', 'russian hill', 'marina']
            address_lower = listing.get('address', '').lower()
            if any(area in address_lower for area in quiet_areas):
                bonus += 0.03
    
    if intent.family_friendly:
        # Use school_rating and crime_index for family friendliness
        school_rating = listing.get('school_rating')
        crime_index = listing.get('crime_index')
        if (school_rating and school_rating >= 7) and (crime_index and crime_index <= 4):
            bonus += 0.04
        else:
            # Fallback: assume family friendly if in good neighborhoods
            family_areas = ['pacific heights', 'presidio heights', 'marina', 'russian hill']
            address_lower = listing.get('address', '').lower()
            if any(area in address_lower for area in family_areas):
                bonus += 0.04
    
    # Final score: 85% similarity + 15% bonus
    final_score = 0.85 * base_score + 0.15 * bonus
    return min(final_score, 1.0)  # Cap at 1.0

def generate_template_reason(listing: Dict[str, Any], intent: SearchIntent) -> str:
    """Generate template-based recommendation reason"""
    reasons = []
    
    # Basic match reasons
    if intent.min_beds and listing.get('bedrooms', 0) >= intent.min_beds:
        reasons.append(f"{listing['bedrooms']} bedrooms")
    
    if intent.min_baths and listing.get('bathrooms', 0) >= intent.min_baths:
        reasons.append(f"{listing['bathrooms']} bathrooms")
    
    if intent.max_price_sale and listing.get('price_for_sale', 0) <= intent.max_price_sale:
        reasons.append(f"under ${intent.max_price_sale:,.0f}")
    
    if intent.max_price_rent and listing.get('price_per_month', 0) <= intent.max_price_rent:
        reasons.append(f"rent under ${intent.max_price_rent:,.0f}")
    
    if intent.city:
        reasons.append(f"in {intent.city}")
    
    # Feature matches
    if intent.garage_required and (listing.get('garage_number', 0) > 0 or listing.get('has_parking_lot')):
        reasons.append("with parking")
    
    if intent.walk_to_metro:
        # Fallback: assume walkable if in urban areas
        urban_areas = ['downtown', 'financial district', 'soma', 'mission', 'hayes valley']
        address_lower = listing.get('address', '').lower()
        if any(area in address_lower for area in urban_areas):
            reasons.append("near metro")
    
    if intent.good_schools:
        # Fallback: assume good schools if in good neighborhoods
        good_neighborhoods = ['pacific heights', 'marina', 'nob hill', 'russian hill', 'presidio heights']
        address_lower = listing.get('address', '').lower()
        if any(neighborhood in address_lower for neighborhood in good_neighborhoods):
            reasons.append("near good schools")
    
    if intent.ocean_view:
        # Fallback: assume ocean view if near water
        water_areas = ['marina', 'pacific heights', 'presidio', 'richmond', 'sunset']
        address_lower = listing.get('address', '').lower()
        if any(area in address_lower for area in water_areas):
            reasons.append("with ocean view")
    
    if intent.modern:
        # Fallback: assume modern if has modern keywords in title
        title_lower = listing.get('title', '').lower()
        if any(word in title_lower for word in ['modern', 'contemporary', 'new', 'updated']):
            reasons.append("modern design")
    
    if intent.renovated:
        # Fallback: assume renovated if has renovation keywords
        title_lower = listing.get('title', '').lower()
        if any(word in title_lower for word in ['renovated', 'remodeled', 'updated', 'newly']):
            reasons.append("recently renovated")
    
    if not reasons:
        reasons.append("matches your search criteria")
    
    return f"Matches your query for {' and '.join(reasons)}."

def generate_search_suggestions(intent: SearchIntent) -> str:
    """Generate helpful suggestions when no results are found"""
    suggestions = []
    
    # Price suggestions
    if intent.max_price_sale:
        suggestions.append(f"• Try increasing your budget to ${intent.max_price_sale * 1.2:,.0f} or higher")
    if intent.max_price_rent:
        suggestions.append(f"• Try increasing your budget to ${intent.max_price_rent * 1.2:,.0f}/month or higher")
    
    # Location suggestions
    if intent.city:
        suggestions.append(f"• Expand your search to nearby areas around {intent.city}")
        suggestions.append(f"• Try searching in the broader {intent.city} region")
    
    # Property type suggestions
    if intent.property_type == 'apartment':
        suggestions.append("• Consider condos or studios as alternatives")
    elif intent.property_type == 'house':
        suggestions.append("• Consider townhouses or condos as alternatives")
    
    # Bedroom suggestions
    if intent.min_beds:
        suggestions.append(f"• Consider properties with {max(1, intent.min_beds - 1)} bedrooms")
    
    # General suggestions
    suggestions.append("• Try removing some filters to see more options")
    suggestions.append("• Check back later for new listings")
    
    return "No exact matches found. Suggestions:\n" + "\n".join(suggestions)

# Pydantic Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language description of dream home")
    limit: Optional[int] = Field(10, description="Number of results to return (default: 10)")
    offset: Optional[int] = Field(0, description="Number of results to skip for pagination (default: 0)")
    reasons: Optional[bool] = Field(True, description="Whether to generate reasons for matches (default: True)")

class ListingResult(BaseModel):
    id: str
    title: Optional[str] = None
    address: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    square_feet: Optional[int] = None
    garage_number: Optional[int] = None
    price: Optional[float] = None
    images: Optional[List[str]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    neighborhood: Optional[str] = None
    description: Optional[str] = None
    amenities: Optional[List[str]] = None
    host_id: Optional[str] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    property_listing_type: Optional[str] = None
    year_built: Optional[int] = None
    year_renovated: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    similarity_score: float = Field(..., description="Final reranking score (0-1)")
    reason: Optional[str] = Field("", description="Generated reason for match")

class SearchResponse(BaseModel):
    items: List[ListingResult]
    query: str
    page: int
    limit: int
    has_more: bool
    generation_error: Optional[bool] = Field(False, description="Whether generation failed")

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

def get_complete_listing_query(where_clause: str, max_candidates: int) -> str:
    """Generate complete SQL query with all listing fields"""
    return f"""
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
        images
    FROM listings_v2 
    WHERE {where_clause}
    LIMIT {max_candidates}
    """

# Enhanced Search Functions
async def get_exact_matches(
    intent: SearchIntent,
    pool: asyncpg.Pool,
    max_candidates: int = 10000
) -> List[Dict[str, Any]]:
    """Get exact matches using strict filtering"""
    try:
        where_clause, params = build_exact_filter_conditions(intent)
        
        # Debug: Log the exact filter conditions
        logger.info(f"🎯 Exact filter conditions: {where_clause}")
        logger.info(f"🎯 Exact filter parameters: {params}")
        
        query = get_complete_listing_query(where_clause, max_candidates)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            exact_count = len(rows)
            logger.info(f"🎯 Exact matches found: {exact_count}")
            
            # Debug: Show sample of exact results
            if exact_count > 0:
                sample_listings = rows[:3]
                logger.info(f"🎯 Sample exact matches:")
                for i, row in enumerate(sample_listings):
                    logger.info(f"  {i+1}. {row['title']} - {row['address']} - ${row.get('price', 'N/A')}")
            
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Exact matching error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get exact matches")

async def get_progressive_relaxed_matches(
    intent: SearchIntent,
    pool: asyncpg.Pool,
    max_candidates: int = 10000
) -> List[Dict[str, Any]]:
    """Get progressively relaxed matches with multiple fallback levels"""
    logger.info("🔄 Starting progressive relaxation...")
    
    # Level 1: Slightly relaxed (20% price increase, nearby areas)
    logger.info("📊 Level 1: Slightly relaxed criteria...")
    level1_listings = await get_level1_relaxed_matches(intent, pool, max_candidates)
    if level1_listings:
        logger.info(f"✅ Level 1 found {len(level1_listings)} matches")
        return level1_listings
    
    # Level 2: More relaxed (50% price increase, broader area)
    logger.info("📊 Level 2: More relaxed criteria...")
    level2_listings = await get_level2_relaxed_matches(intent, pool, max_candidates)
    if level2_listings:
        logger.info(f"✅ Level 2 found {len(level2_listings)} matches")
        return level2_listings
    
    # Level 3: Very relaxed (similar properties in same city)
    logger.info("📊 Level 3: Very relaxed criteria...")
    level3_listings = await get_level3_relaxed_matches(intent, pool, max_candidates)
    if level3_listings:
        logger.info(f"✅ Level 3 found {len(level3_listings)} matches")
        return level3_listings
    
    logger.info("❌ No matches found even with progressive relaxation")
    return []

async def get_level1_relaxed_matches(
    intent: SearchIntent,
    pool: asyncpg.Pool,
    max_candidates: int = 10000
) -> List[Dict[str, Any]]:
    """Level 1: Slightly relaxed (20% price increase, nearby areas)"""
    try:
        # Relax price by 20%
        relaxed_price_sale = intent.max_price_sale * 1.2 if intent.max_price_sale else None
        relaxed_price_rent = intent.max_price_rent * 1.2 if intent.max_price_rent else None
        
        # Build relaxed conditions
        conditions = ["embedding IS NOT NULL"]
        params = []
        param_count = 0
        
        # Price relaxation
        if relaxed_price_sale:
            param_count += 1
            conditions.append(f"(price_for_sale <= ${param_count} OR price_for_sale IS NULL)")
            params.append(relaxed_price_sale)
        
        if relaxed_price_rent:
            param_count += 1
            conditions.append(f"(price_per_month <= ${param_count} OR price_per_month IS NULL)")
            params.append(relaxed_price_rent)
        
        # Property type (include similar types)
        if intent.property_type:
            param_count += 1
            conditions.append(f"(LOWER(property_type) ~ ${param_count} OR LOWER(title) ~ ${param_count})")
            if intent.property_type == 'apartment':
                params.append('apartment|condo|unit')
            elif intent.property_type == 'house':
                params.append('house|home|villa')
            else:
                params.append(intent.property_type)
        
        # Location (include nearby areas)
        if intent.city:
            param_count += 1
            conditions.append(f"(LOWER(city) = ${param_count} OR LOWER(address) LIKE ${param_count + 1})")
            params.extend([intent.city, f'%{intent.city}%'])
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            id, title, address, bedrooms, bathrooms, square_feet,
            garage_number, has_parking_lot, property_type,
            price_for_sale, price_per_month,
            has_yard, school_rating, crime_index, facing,
            shopping_idx, grocery_idx, tags, embedding_text,
            CASE 
                WHEN property_listing_type = 'sale' THEN price_for_sale
                WHEN property_listing_type = 'both' THEN price_per_month
                WHEN property_listing_type = 'rent' THEN price_per_month
                ELSE COALESCE(price_per_month, price_for_sale)
            END as price,
            CASE 
                WHEN images IS NOT NULL AND jsonb_array_length(images) > 0 
                THEN images->0 
                ELSE NULL 
            END as image_url
        FROM listings_v2 
        WHERE {where_clause}
        LIMIT {max_candidates}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Level 1 relaxation error: {e}")
        return []

async def get_level2_relaxed_matches(
    intent: SearchIntent,
    pool: asyncpg.Pool,
    max_candidates: int = 10000
) -> List[Dict[str, Any]]:
    """Level 2: More relaxed (50% price increase, broader area)"""
    try:
        # Relax price by 50%
        relaxed_price_sale = intent.max_price_sale * 1.5 if intent.max_price_sale else None
        relaxed_price_rent = intent.max_price_rent * 1.5 if intent.max_price_rent else None
        
        # Build very relaxed conditions
        conditions = ["embedding IS NOT NULL"]
        params = []
        param_count = 0
        
        # Price relaxation
        if relaxed_price_sale:
            param_count += 1
            conditions.append(f"(price_for_sale <= ${param_count} OR price_for_sale IS NULL)")
            params.append(relaxed_price_sale)
        
        if relaxed_price_rent:
            param_count += 1
            conditions.append(f"(price_per_month <= ${param_count} OR price_per_month IS NULL)")
            params.append(relaxed_price_rent)
        
        # Property type (very broad)
        if intent.property_type:
            param_count += 1
            conditions.append(f"(LOWER(property_type) ~ ${param_count} OR LOWER(title) ~ ${param_count})")
            params.append('apartment|condo|unit|house|home|villa|penthouse')
        
        # Location (same state if available)
        if intent.state:
            param_count += 1
            conditions.append(f"(LOWER(state) = ${param_count} OR LOWER(address) LIKE ${param_count + 1})")
            params.extend([intent.state, f'%{intent.state}%'])
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            id, title, address, bedrooms, bathrooms, square_feet,
            garage_number, has_parking_lot, property_type,
            price_for_sale, price_per_month,
            has_yard, school_rating, crime_index, facing,
            shopping_idx, grocery_idx, tags, embedding_text,
            CASE 
                WHEN property_listing_type = 'sale' THEN price_for_sale
                WHEN property_listing_type = 'both' THEN price_per_month
                WHEN property_listing_type = 'rent' THEN price_per_month
                ELSE COALESCE(price_per_month, price_for_sale)
            END as price,
            CASE 
                WHEN images IS NOT NULL AND jsonb_array_length(images) > 0 
                THEN images->0 
                ELSE NULL 
            END as image_url
        FROM listings_v2 
        WHERE {where_clause}
        LIMIT {max_candidates}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Level 2 relaxation error: {e}")
        return []

async def get_level3_relaxed_matches(
    intent: SearchIntent,
    pool: asyncpg.Pool,
    max_candidates: int = 10000
) -> List[Dict[str, Any]]:
    """Level 3: Very relaxed (similar properties in same city/state)"""
    try:
        # Only get properties that are at least somewhat similar
        conditions = ["embedding IS NOT NULL"]
        params = []
        param_count = 0
        
        # Property type (any residential)
        param_count += 1
        conditions.append(f"(LOWER(property_type) ~ ${param_count} OR LOWER(title) ~ ${param_count})")
        params.append('apartment|condo|unit|house|home|villa|penthouse')
        
        # Location (same city if available, otherwise same state)
        if intent.city:
            param_count += 1
            conditions.append(f"(LOWER(city) = ${param_count} OR LOWER(address) LIKE ${param_count + 1})")
            params.extend([intent.city, f'%{intent.city}%'])
        elif intent.state:
            param_count += 1
            conditions.append(f"(LOWER(state) = ${param_count} OR LOWER(address) LIKE ${param_count + 1})")
            params.extend([intent.state, f'%{intent.state}%'])
        
        # Price (at least within 3x the budget)
        if intent.max_price_sale:
            param_count += 1
            conditions.append(f"(price_for_sale <= ${param_count} OR price_for_sale IS NULL)")
            params.append(intent.max_price_sale * 3)
        
        if intent.max_price_rent:
            param_count += 1
            conditions.append(f"(price_per_month <= ${param_count} OR price_per_month IS NULL)")
            params.append(intent.max_price_rent * 3)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            id, title, address, bedrooms, bathrooms, square_feet,
            garage_number, has_parking_lot, property_type,
            price_for_sale, price_per_month,
            has_yard, school_rating, crime_index, facing,
            shopping_idx, grocery_idx, tags, embedding_text,
            CASE 
                WHEN property_listing_type = 'sale' THEN price_for_sale
                WHEN property_listing_type = 'both' THEN price_per_month
                WHEN property_listing_type = 'rent' THEN price_per_month
                ELSE COALESCE(price_per_month, price_for_sale)
            END as price,
            CASE 
                WHEN images IS NOT NULL AND jsonb_array_length(images) > 0 
                THEN images->0 
                ELSE NULL 
            END as image_url
        FROM listings_v2 
        WHERE {where_clause}
        ORDER BY price ASC
        LIMIT {max_candidates}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Level 3 relaxation error: {e}")
        return []

async def get_relaxed_matches(
    intent: SearchIntent,
    pool: asyncpg.Pool,
    max_candidates: int = 10000
) -> List[Dict[str, Any]]:
    """Get relaxed matches using flexible filtering"""
    try:
        where_clause, params = build_relaxed_filter_conditions(intent)
        
        # Debug: Log the relaxed filter conditions
        logger.info(f"🔍 Relaxed filter conditions: {where_clause}")
        logger.info(f"🔍 Relaxed filter parameters: {params}")
        
        # First, get total count before filtering
        total_query = "SELECT COUNT(*) as total FROM listings_v2 WHERE embedding IS NOT NULL"
        async with pool.acquire() as conn:
            total_result = await conn.fetchrow(total_query)
            total_listings = total_result["total"] if total_result else 0
            logger.info(f"📊 Total listings with embeddings: {total_listings}")
        
        query = f"""
        SELECT 
            id, title, address, bedrooms, bathrooms, square_feet,
            garage_number, has_parking_lot, property_type,
            price_for_sale, price_per_month,
            has_yard, school_rating, crime_index, facing,
            shopping_idx, grocery_idx, tags, embedding_text,
            CASE 
                WHEN property_listing_type = 'sale' THEN price_for_sale
                WHEN property_listing_type = 'both' THEN price_per_month
                WHEN property_listing_type = 'rent' THEN price_per_month
                ELSE COALESCE(price_per_month, price_for_sale)
            END as price,
            CASE 
                WHEN images IS NOT NULL AND jsonb_array_length(images) > 0 
                THEN images->0 
                ELSE NULL 
            END as image_url
        FROM listings_v2 
        WHERE {where_clause}
        LIMIT {max_candidates}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            relaxed_count = len(rows)
            logger.info(f"🔍 Relaxed matches found: {relaxed_count}")
            
            # Debug: Show sample of relaxed results
            if relaxed_count > 0:
                sample_listings = rows[:3]
                logger.info(f"🔍 Sample relaxed matches:")
                for i, row in enumerate(sample_listings):
                    logger.info(f"  {i+1}. {row['title']} - {row['address']} - ${row.get('price', 'N/A')}")
            
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Relaxed matching error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get relaxed matches")

async def hard_filter_listings(
    intent: SearchIntent,
    pool: asyncpg.Pool,
    max_candidates: int = 10000
) -> List[Dict[str, Any]]:
    """Apply hard filters to narrow down candidates with debug logging (legacy function)"""
    try:
        where_clause, params = build_filter_conditions(intent)
        
        # Debug: Log the filter conditions
        logger.info(f"🔍 Filter conditions: {where_clause}")
        logger.info(f"🔍 Filter parameters: {params}")
        
        # First, get total count before filtering
        total_query = "SELECT COUNT(*) as total FROM listings_v2 WHERE embedding IS NOT NULL"
        async with pool.acquire() as conn:
            total_result = await conn.fetchrow(total_query)
            total_listings = total_result["total"] if total_result else 0
            logger.info(f"📊 Total listings with embeddings: {total_listings}")
        
        # Apply filters with detailed logging
        query = f"""
        SELECT 
            id, title, address, bedrooms, bathrooms, square_feet,
            garage_number, has_parking_lot, property_type,
            price_for_sale, price_per_month,
            has_yard, school_rating, crime_index, facing,
            shopping_idx, grocery_idx, tags, embedding_text,
            CASE 
                WHEN property_listing_type = 'sale' THEN price_for_sale
                WHEN property_listing_type = 'both' THEN price_per_month
                WHEN property_listing_type = 'rent' THEN price_per_month
                ELSE COALESCE(price_per_month, price_for_sale)
            END as price,
            CASE 
                WHEN images IS NOT NULL AND jsonb_array_length(images) > 0 
                THEN images->0 
                ELSE NULL 
            END as image_url
        FROM listings_v2 
        WHERE {where_clause}
        LIMIT {max_candidates}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            filtered_count = len(rows)
            logger.info(f"📊 Filtered candidates: {filtered_count}")
            
            # Debug: Show sample of filtered results
            if filtered_count > 0:
                sample_listings = rows[:3]
                logger.info(f"📋 Sample filtered listings:")
                for i, row in enumerate(sample_listings):
                    logger.info(f"  {i+1}. {row['title']} - {row['address']} - ${row.get('price', 'N/A')}")
            
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Hard filtering error: {e}")
        raise HTTPException(status_code=500, detail="Failed to filter listings")

async def vector_search_candidates(
    query_embedding: List[float],
    candidate_ids: List[str],
    pool: asyncpg.Pool,
    top_k: int = 100
) -> List[Dict[str, Any]]:
    """Perform vector search on filtered candidates with debug logging"""
    try:
        if not candidate_ids:
            logger.info("📊 No candidate IDs provided for vector search")
            return []
        
        logger.info(f"🔍 Vector search on {len(candidate_ids)} candidates, top_k={top_k}")
        
        # Convert embedding to pgvector format
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Create placeholders for candidate IDs
        id_placeholders = ','.join([f"${i+2}" for i in range(len(candidate_ids))])
        
        query = f"""
        SELECT 
            id, title, address, bedrooms, bathrooms, square_feet,
            garage_number, has_parking_lot, property_type,
            price_for_sale, price_per_month,
            has_yard, school_rating, crime_index, facing,
            shopping_idx, grocery_idx, tags, embedding_text,
            CASE 
                WHEN property_listing_type = 'sale' THEN price_for_sale
                WHEN property_listing_type = 'both' THEN price_per_month
                WHEN property_listing_type = 'rent' THEN price_per_month
                ELSE COALESCE(price_per_month, price_for_sale)
            END as price,
            CASE 
                WHEN images IS NOT NULL AND jsonb_array_length(images) > 0 
                THEN images->0 
                ELSE NULL 
            END as image_url,
            embedding <=> $1::vector as distance,
            1 - (embedding <=> $1::vector) as similarity_score
        FROM listings_v2 
        WHERE id IN ({id_placeholders})
        ORDER BY embedding <=> $1::vector
        LIMIT {top_k}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, embedding_str, *candidate_ids)
            vector_results = [dict(row) for row in rows]
            
            logger.info(f"📊 Vector search returned {len(vector_results)} candidates")
            
            # Debug: Show similarity score range
            if vector_results:
                min_score = min(r.get('similarity_score', 0) for r in vector_results)
                max_score = max(r.get('similarity_score', 0) for r in vector_results)
                avg_score = sum(r.get('similarity_score', 0) for r in vector_results) / len(vector_results)
                logger.info(f"📈 Similarity scores - Min: {min_score:.3f}, Max: {max_score:.3f}, Avg: {avg_score:.3f}")
                
                # Show top 3 vector results
                logger.info(f"🏆 Top 3 vector results:")
                for i, result in enumerate(vector_results[:3]):
                    logger.info(f"  {i+1}. {result['title']} - Score: {result.get('similarity_score', 0):.3f}")
            
            return vector_results
            
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        raise HTTPException(status_code=500, detail="Failed to search listings")

async def rerank_listings(
    listings: List[Dict[str, Any]],
    intent: SearchIntent,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Rerank listings using similarity scores and soft preferences with debug logging"""
    try:
        logger.info(f"🔍 Reranking {len(listings)} listings with soft preferences")
        
        # Calculate final scores with detailed logging
        for listing in listings:
            similarity_score = float(listing.get('similarity_score', 0))
            final_score = calculate_reranking_score(similarity_score, listing, intent)
            listing['final_score'] = final_score
            
            # Debug: Log score changes for top candidates
            if len([l for l in listings if l.get('final_score', 0) > final_score]) < 5:
                score_change = final_score - similarity_score
                logger.info(f"📊 {listing['title']} - Vector: {similarity_score:.3f}, Final: {final_score:.3f}, Change: {score_change:+.3f}")
        
        # Sort by final score and return top results
        sorted_listings = sorted(listings, key=lambda x: x['final_score'], reverse=True)
        final_results = sorted_listings[:limit]
        
        logger.info(f"📊 Reranking completed - returning top {len(final_results)} results")
        
        # Debug: Show final ranking
        if final_results:
            logger.info(f"🏆 Final top {len(final_results)} results:")
            for i, result in enumerate(final_results):
                logger.info(f"  {i+1}. {result['title']} - Final Score: {result.get('final_score', 0):.3f}")
        
        return final_results
        
    except Exception as e:
        logger.error(f"Reranking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to rerank listings")

async def generate_enhanced_reasons(
    query: str, 
    listings: List[Dict[str, Any]],
    intent: SearchIntent
) -> Dict[str, str]:
    """Generate enhanced reasons using LLM or template fallback"""
    logger.info(f"Generating enhanced reasons for {len(listings)} listings")
    
    if not listings:
        return {}
    
    try:
        # Try LLM generation first
        reasons = await generate_llm_reasons(query, listings, intent)
        if reasons:
            return reasons
    except Exception as e:
        logger.warning(f"LLM generation failed, falling back to template: {e}")
    
    # Fallback to template-based reasons
    reasons = {}
    for listing in listings:
        listing_id = str(listing['id'])
        reasons[listing_id] = generate_template_reason(listing, intent)
    
    return reasons

async def generate_llm_reasons(
    query: str, 
    listings: List[Dict[str, Any]],
    intent: SearchIntent
) -> Dict[str, str]:
    """Generate reasons using OpenAI LLM"""
    try:
        # Build property summaries
        property_summaries = []
        for listing in listings:
            summary = build_property_summary(listing)
            property_summaries.append(f"ID: {listing['id']} | {summary}")
        
        properties_text = "\n".join(property_summaries)
        
        # Create enhanced prompt with intent information
        intent_summary = []
        if intent.city:
            intent_summary.append(f"Location: {intent.city}")
        if intent.min_beds:
            intent_summary.append(f"Bedrooms: {intent.min_beds}+")
        if intent.max_price_sale:
            intent_summary.append(f"Max price: ${intent.max_price_sale:,.0f}")
        if intent.good_schools:
            intent_summary.append("Good schools preferred")
        if intent.walk_to_metro:
            intent_summary.append("Walking distance to transit")
        
        intent_text = ", ".join(intent_summary) if intent_summary else "General preferences"
        
        system_prompt = "You are a helpful assistant that explains why each property matches the user's specific requirements. Respond strictly in minified JSON with no extra text."
        
        user_prompt = f"""User query: "{query}"
User requirements: {intent_text}

Properties:
{properties_text}

Generate a concise explanation (1-2 sentences) for why each property matches the user's requirements. Return as JSON array: [{{"id": "uuid", "reason": "explanation"}}]"""

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")
        
        result = json.loads(content)
        reasons = {}
        
        # Handle different response formats
        if isinstance(result, dict):
            if "reasons" in result:
                reasons_list = result["reasons"]
            elif "result" in result:
                reasons_list = result["result"]
            elif "results" in result:
                reasons_list = result["results"]
            elif "properties" in result:
                reasons_list = result["properties"]
            else:
                reasons_list = []
        elif isinstance(result, list):
            reasons_list = result
        else:
            reasons_list = []
        
        # Extract reasons by ID
        for item in reasons_list:
            if isinstance(item, dict) and "id" in item and "reason" in item:
                reasons[item["id"]] = item["reason"]
        
        return reasons
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise

def build_property_summary(listing: Dict[str, Any]) -> str:
    """Build a compact property summary for the generation prompt"""
    summary_parts = []
    
    # Basic location info
    if listing.get("address"):
        address = truncate_text(listing["address"], 80)
        summary_parts.append(f"Location: {address}")
    
    # Property details
    if listing.get("bedrooms"):
        summary_parts.append(f"{listing['bedrooms']} bed")
    if listing.get("bathrooms"):
        summary_parts.append(f"{listing['bathrooms']} bath")
    if listing.get("square_feet"):
        summary_parts.append(f"{listing['square_feet']} sqft")
    if listing.get("garage_number"):
        summary_parts.append(f"{listing['garage_number']} garage")
    
    # Price
    if listing.get("price"):
        summary_parts.append(f"${listing['price']:,.0f}")
    
    return " | ".join(summary_parts)

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max_length characters"""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text

# Enhanced Search Pipeline
async def enhanced_semantic_search(
    query: str,
    intent: SearchIntent,
    limit: int = 10,
    offset: int = 0,
    pool: asyncpg.Pool = None
) -> List[Dict[str, Any]]:
    """Complete enhanced search pipeline with intelligent filtering"""
    try:
        logger.info(f"Starting enhanced search for query: {query}")
        
        # Step 1: Try exact matching first
        logger.info("Step 1: Trying exact matching...")
        exact_listings = await get_exact_matches(intent, pool)
        logger.info(f"Exact matching returned {len(exact_listings)} candidates")
        
        # If we have exact matches, return only those (no relaxed matches)
        if exact_listings:
            logger.info(f"Found {len(exact_listings)} exact matches, returning only exact matches")
            
            # Generate reasons for the exact matches
            logger.info("Generating enhanced reasons for matches...")
            reasons = await generate_enhanced_reasons(query, exact_listings, intent)
            
            # Return exact matches with reasons
            for listing in exact_listings:
                listing['similarity_score'] = 1.0  # Perfect match score
                listing['reason'] = reasons.get(listing['id'], f"This property meets all your criteria: {intent.min_beds}+ bedrooms in {intent.city}.")
            
            logger.info(f"Returning {len(exact_listings)} exact matches only")
            return exact_listings
        else:
            logger.info("No exact matches found, trying progressive relaxation...")
        
        # Progressive relaxation when no exact matches
        if not exact_listings:
            
            # Step 2: Try progressive relaxation
            logger.info("Step 2: Applying progressive relaxation...")
            relaxed_listings = await get_progressive_relaxed_matches(intent, pool)
            logger.info(f"Progressive relaxation returned {len(relaxed_listings)} candidates")
            
            if not relaxed_listings:
                logger.info("No listings match any criteria, even with progressive relaxation")
                # Return empty list - the API will handle the response
                return []
            
            # Step 3: Generate query embedding
            logger.info("Step 3: Generating query embedding...")
            query_embedding = await get_embedding(query)
            
            # Step 4: Vector search on relaxed candidates
            logger.info("Step 4: Performing vector search...")
            candidate_ids = [listing['id'] for listing in relaxed_listings]
            vector_results = await vector_search_candidates(query_embedding, candidate_ids, pool, top_k=100)
            logger.info(f"Vector search returned {len(vector_results)} candidates")
            
            # Step 5: Reranking with relaxed match indicators
            logger.info("Step 5: Reranking candidates...")
            reranked_listings = await rerank_listings(vector_results, intent, limit=limit)
            logger.info(f"Reranking returned {len(reranked_listings)} final results")
            
            # Add relaxed match indicators to reasons
            for listing in reranked_listings:
                if 'reason' not in listing:
                    listing['reason'] = "Similar property found with relaxed criteria."
                listing['reason'] = f"[Relaxed Match] {listing['reason']}"
            
            return reranked_listings
        
    except Exception as e:
        logger.error(f"Enhanced search failed: {e}")
        raise

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
    description="Enhanced semantic property search using LLM embeddings, intent extraction, and reranking",
    version="2.0.0",
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
        "service": "dreamheaven-rag-enhanced",
        "version": "2.0.0"
    }

@app.post("/ai-search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Perform enhanced semantic search on property listings using natural language query.
    
    Features:
    - Intent extraction for structured filtering
    - Hard filtering based on extracted criteria
    - Vector similarity search with pgvector
    - Reranking using soft preferences
    - AI-generated explanations
    
    Example query: "modern 3-bedroom condo in San Francisco under $1M with good schools"
    """
    try:
        logger.info(f"Processing enhanced search query: {request.query}")
        
        # Step 1: Extract search intent
        logger.info("Extracting search intent...")
        intent = extract_search_intent(request.query)
        logger.info(f"Extracted intent: {intent}")
        
        # Step 2: Enhanced search pipeline
        similar_listings = await enhanced_semantic_search(
            query=request.query,
            intent=intent,
            limit=request.limit,
            offset=request.offset,
            pool=pool
        )
        
        # Step 3: Generate reasons
        reasons = {}
        generation_error = False
        
        if request.reasons and similar_listings:
            try:
                logger.info("Generating enhanced reasons for matches...")
                reasons = await generate_enhanced_reasons(request.query, similar_listings, intent)
                logger.info(f"Generated reasons for {len(reasons)} listings")
            except Exception as e:
                logger.error(f"Reason generation failed: {e}")
                generation_error = True
                reasons = {}
        
        # Step 4: Convert to response format
        results = []
        
        if not similar_listings:
            # Handle no results case with helpful suggestions
            logger.info("No results found, adding helpful suggestions")
            suggestions = generate_search_suggestions(intent)
            
            no_results_item = ListingResult(
                id="no_results",
                title="No exact matches found",
                address="",
                bedrooms=None,
                bathrooms=None,
                square_feet=None,
                garage_number=None,
                price=None,
                images=None,
                city=None,
                state=None,
                country=None,
                neighborhood=None,
                description=None,
                amenities=None,
                host_id=None,
                is_available=None,
                is_featured=None,
                latitude=None,
                longitude=None,
                rating=None,
                review_count=None,
                property_listing_type=None,
                year_built=None,
                year_renovated=None,
                created_at=None,
                updated_at=None,
                similarity_score=0.0,
                reason=suggestions
            )
            results = [no_results_item]
        else:
            for listing in similar_listings:
                listing_id = str(listing["id"])
                reason = reasons.get(listing_id, "")
                
                # Convert data types to match expected format
                images_data = listing.get("images")
                if isinstance(images_data, str):
                    # Parse JSON string to list
                    import json
                    try:
                        images_data = json.loads(images_data)
                    except:
                        images_data = []
                elif not isinstance(images_data, list):
                    images_data = []
                
                host_id_data = listing.get("host_id")
                if host_id_data:
                    host_id_data = str(host_id_data)
                
                created_at_data = listing.get("created_at")
                if created_at_data:
                    created_at_data = str(created_at_data)
                
                updated_at_data = listing.get("updated_at")
                if updated_at_data:
                    updated_at_data = str(updated_at_data)
                
                result = ListingResult(
                    id=listing_id,
                    title=listing.get("title"),
                    address=listing.get("address"),
                    bedrooms=listing.get("bedrooms"),
                    bathrooms=listing.get("bathrooms"),
                    square_feet=listing.get("square_feet"),
                    garage_number=listing.get("garage_number"),
                    price=listing.get("price"),
                    images=images_data,
                    city=listing.get("city"),
                    state=listing.get("state"),
                    country=listing.get("country"),
                    neighborhood=listing.get("neighborhood"),
                    description=listing.get("description"),
                    amenities=listing.get("amenities"),
                    host_id=host_id_data,
                    is_available=listing.get("is_available"),
                    is_featured=listing.get("is_featured"),
                    latitude=listing.get("latitude"),
                    longitude=listing.get("longitude"),
                    rating=listing.get("rating"),
                    review_count=listing.get("review_count"),
                    property_listing_type=listing.get("property_listing_type"),
                    year_built=listing.get("year_built"),
                    year_renovated=listing.get("year_renovated"),
                    created_at=created_at_data,
                    updated_at=updated_at_data,
                    similarity_score=float(listing.get("similarity_score", 0)),
                    reason=reason
                )
                results.append(result)
        
        logger.info(f"Enhanced search completed with {len(results)} results")
        
        return SearchResponse(
            items=results,
            query=request.query,
            page=request.offset // request.limit + 1,
            limit=request.limit,
            has_more=len(results) == request.limit,
            generation_error=generation_error
        )
        
    except Exception as e:
        logger.error(f"Enhanced search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats(pool: asyncpg.Pool = Depends(get_db_connection)):
    """Get statistics about the vector database"""
    try:
        async with pool.acquire() as conn:
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
        raise HTTPException(status_code=500, detail="Failed to get statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

