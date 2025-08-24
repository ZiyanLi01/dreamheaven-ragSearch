#!/usr/bin/env python3
import asyncio
from dotenv import load_dotenv
from search_engine import SearchEngine
from database import DatabaseManager
from config import Config
from openai import AsyncOpenAI
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

async def test_new_query():
    load_dotenv()
    config = Config()
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.initialize()
    openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    search_engine = SearchEngine(db_manager, openai_client)
    scoring_engine = ScoringEngine()
    
    query = "Give me a short-term rental in downtown that allows pets in San Francisco, CA"
    
    # Extract intent
    intent_extractor = IntentExtractor()
    intent = intent_extractor.extract_intent(query)
    print(f"Intent: city={intent.city}, state={intent.state}, neighborhood={intent.neighborhood}")
    
    results = await search_engine.search(query, limit=1)
    result = results.items[0]
    
    print(f"\nListing: {result.title}")
    print(f"City: {result.city}")
    print(f"State: {result.state}")
    print(f"Neighborhood: {result.neighborhood}")
    
    # Create listing dict for detailed analysis
    listing_dict = {
        'title': result.title,
        'description': result.description,
        'city': result.city,
        'state': result.state,
        'neighborhood': result.neighborhood,
        'property_listing_type': result.property_listing_type,
        'amenities': result.amenities,
        'address': result.address
    }
    
    # Get detailed matches
    detailed_matches = scoring_engine._calculate_detailed_matches(listing_dict, intent)
    
    print(f"\nMatch Details:")
    print(f"  missing: {detailed_matches['missing']}")
    print(f"  semantic: {detailed_matches['semantic']}")
    print(f"  soft_preferences: {detailed_matches['soft_preferences']}")
    print(f"  structured: {detailed_matches['structured']}")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_new_query())
