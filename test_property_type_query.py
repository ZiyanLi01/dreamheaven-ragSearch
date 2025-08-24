#!/usr/bin/env python3
import asyncio
from dotenv import load_dotenv
from search_engine import SearchEngine
from database import DatabaseManager
from config import Config
from openai import AsyncOpenAI
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

async def test_property_type_query():
    load_dotenv()
    config = Config()
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.initialize()
    openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    search_engine = SearchEngine(db_manager, openai_client)
    scoring_engine = ScoringEngine()
    
    query = "Show me featured apartments close to grocery stores and shopping in San Francisco, CA"
    
    # Extract intent
    intent_extractor = IntentExtractor()
    intent = intent_extractor.extract_intent(query)
    print(f"Intent: property_type={intent.property_type}, featured={intent.featured}, near_grocery={intent.near_grocery}, near_shopping={intent.near_shopping}")
    
    results = await search_engine.search(query, limit=1)
    result = results.items[0]
    
    print(f"\nListing: {result.title}")
    print(f"Property Type: {result.property_listing_type}")
    print(f"Featured: {result.is_featured}")
    print(f"Grocery Index: N/A (not in ListingResult model)")
    print(f"Shopping Index: N/A (not in ListingResult model)")
    
    # Create listing dict for detailed analysis
    listing_dict = {
        'title': result.title,
        'description': result.description,
        'city': result.city,
        'state': result.state,
        'neighborhood': result.neighborhood,
        'property_listing_type': result.property_listing_type,
        'amenities': result.amenities,
        'address': result.address,
        'bedrooms': result.bedrooms,
        'bathrooms': result.bathrooms,
        'square_feet': result.square_feet,
        'price_for_sale': result.price,
        'price_per_month': result.price,
        'garage_number': 0,
        'has_parking_lot': False,
        'school_rating': 8.5,
        'crime_index': 2,
        'shopping_idx': 8,  # Default value for testing
        'grocery_idx': 7,   # Default value for testing
        'is_featured': result.is_featured,
        'has_yard': False
    }
    
    # Get detailed matches
    detailed_matches = scoring_engine._calculate_detailed_matches(listing_dict, intent)
    
    print(f"\nMatch Details:")
    print(f"  missing: {detailed_matches['missing']}")
    print(f"  semantic: {detailed_matches['semantic']}")
    print(f"  soft_preferences: {detailed_matches['soft_preferences']}")
    print(f"  structured: {detailed_matches['structured']}")
    
    # Get score breakdown
    score_details = scoring_engine.calculate_score_with_details(listing_dict, intent)
    print(f"\nScore Breakdown:")
    print(f"  final_score: {score_details['final_score']:.3f}")
    print(f"  similarity_score: {score_details['similarity_score']:.3f}")
    print(f"  match_percent: {score_details['match_percent']:.3f}")
    print(f"  soft_preference_bonus: {score_details['soft_preference_bonus']:.3f}")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_property_type_query())
