#!/usr/bin/env python3
"""
Debug Script for Scoring Issues
Investigates:
1. Why structured filtering finds 17 candidates but structured reasons are empty
2. Why pet-friendly listings aren't showing in semantic reasons
"""

import asyncio
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging to see detailed output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our components
from search_engine import SearchEngine
from database import DatabaseManager
from config import Config
from openai import AsyncOpenAI
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

async def debug_scoring_issues():
    """Debug the scoring issues"""
    
    # Initialize components
    config = Config()
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.initialize()
    
    openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    search_engine = SearchEngine(db_manager, openai_client)
    intent_extractor = IntentExtractor()
    scoring_engine = ScoringEngine()
    
    query = "Give me a short-term rental in downtown that allows pets"
    
    print("=" * 80)
    print("DEBUGGING SCORING ISSUES")
    print("=" * 80)
    print(f"Query: {query}")
    print()
    
    # Step 1: Extract Intent
    intent = intent_extractor.extract_intent(query)
    print("EXTRACTED INTENT:")
    print(json.dumps(intent.__dict__, indent=2, default=str))
    print()
    
    # Step 2: Check what structured criteria are being evaluated
    print("STRUCTURED CRITERIA ANALYSIS:")
    print("-" * 40)
    print("The scoring engine only evaluates these structured criteria:")
    print("• max_price_sale (budget)")
    print("• min_beds (bedrooms)")
    print("• min_baths (bathrooms)")
    print("• garage_required (garage)")
    print("• walk_to_metro (metro)")
    print("• property_type")
    print("• renovated")
    print()
    print("Your intent has these structured criteria:")
    structured_criteria = []
    if intent.max_price_sale:
        structured_criteria.append(f"max_price_sale: ${intent.max_price_sale}")
    if intent.min_beds:
        structured_criteria.append(f"min_beds: {intent.min_beds}")
    if intent.min_baths:
        structured_criteria.append(f"min_baths: {intent.min_baths}")
    if intent.garage_required:
        structured_criteria.append("garage_required: True")
    if intent.walk_to_metro:
        structured_criteria.append("walk_to_metro: True")
    if intent.property_type:
        structured_criteria.append(f"property_type: {intent.property_type}")
    if intent.renovated:
        structured_criteria.append("renovated: True")
    
    if structured_criteria:
        for criterion in structured_criteria:
            print(f"  • {criterion}")
    else:
        print("  • None! This explains why structured reasons are empty.")
    print()
    
    # Step 3: Check what soft preferences are being evaluated
    print("SOFT PREFERENCES ANALYSIS:")
    print("-" * 40)
    print("Your intent has these soft preferences:")
    soft_preferences = []
    if intent.short_term_rental:
        soft_preferences.append("short_term_rental: True")
    if intent.pet_friendly:
        soft_preferences.append("pet_friendly: True")
    if intent.good_schools:
        soft_preferences.append("good_schools: True")
    if intent.safe_area:
        soft_preferences.append("safe_area: True")
    if intent.walkable:
        soft_preferences.append("walkable: True")
    if intent.featured:
        soft_preferences.append("featured: True")
    if intent.yard:
        soft_preferences.append("yard: True")
    if intent.near_grocery:
        soft_preferences.append("near_grocery: True")
    if intent.modern:
        soft_preferences.append("modern: True")
    if intent.ocean_view:
        soft_preferences.append("ocean_view: True")
    if intent.quiet:
        soft_preferences.append("quiet: True")
    
    for preference in soft_preferences:
        print(f"  • {preference}")
    print()
    
    # Step 4: Get some sample listings to check their data
    print("SAMPLE LISTING DATA ANALYSIS:")
    print("-" * 40)
    
    # Get a few listings to examine their data structure
    try:
        results = await search_engine.search(
            query=query,
            limit=5,
            generate_reasons=True
        )
        
        print(f"Found {len(results.items)} results")
        print()
        
        for i, result in enumerate(results.items[:3], 1):
            print(f"LISTING {i}:")
            print(f"  ID: {result.id}")
            print(f"  Title: {result.title}")
            print(f"  City: {result.city}")
            print(f"  State: {result.state}")
            print(f"  Neighborhood: {result.neighborhood}")
            print(f"  Property Type: {result.property_listing_type}")
            print(f"  Description: {result.description[:100]}..." if result.description else "No description")
            print(f"  Amenities: {result.amenities}")
            print(f"  Final Score: {result.similarity_score:.3f}")
            
            if hasattr(result, 'score_breakdown') and result.score_breakdown:
                print(f"  Score Breakdown:")
                for component, score in result.score_breakdown.items():
                    if component != 'final_score':
                        print(f"    • {component}: {score:.3f}")
            
            print()
            
    except Exception as e:
        print(f"Error getting sample listings: {e}")
    
    # Step 5: Check if pet-friendly is in the database schema
    print("DATABASE SCHEMA CHECK:")
    print("-" * 40)
    try:
        # Get a sample listing to see all available fields
        sample_query = "SELECT * FROM listings LIMIT 1"
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow(sample_query)
            if row:
                print("Available fields in listings table:")
                for key in row.keys():
                    print(f"  • {key}")
            else:
                print("No listings found in database")
    except Exception as e:
        print(f"Error checking database schema: {e}")
    
    print()
    print("=" * 80)
    print("DEBUGGING COMPLETE")
    print("=" * 80)
    
    # Cleanup
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(debug_scoring_issues())
