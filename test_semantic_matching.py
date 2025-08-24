#!/usr/bin/env python3
"""
Semantic Matching Test
Demonstrates how semantic matching works in the scoring engine
"""

import asyncio
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our components
from search_engine import SearchEngine
from database import DatabaseManager
from config import Config
from openai import AsyncOpenAI
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

async def test_semantic_matching():
    """Test semantic matching with detailed examples"""
    
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
    print("SEMANTIC MATCHING ANALYSIS")
    print("=" * 80)
    print(f"Query: {query}")
    print()
    
    # Extract intent
    intent = intent_extractor.extract_intent(query)
    print("EXTRACTED INTENT:")
    print(f"  • neighborhood: {intent.neighborhood}")
    print(f"  • short_term_rental: {intent.short_term_rental}")
    print(f"  • pet_friendly: {intent.pet_friendly}")
    print()
    
    # Get some sample listings
    results = await search_engine.search(
        query=query,
        limit=5,
        generate_reasons=True
    )
    
    print("SEMANTIC MATCHING EXAMPLES:")
    print("-" * 80)
    
    for i, result in enumerate(results.items[:3], 1):
        print(f"\nLISTING {i}: {result.title}")
        print(f"  City: {result.city}")
        print(f"  Neighborhood: {result.neighborhood}")
        print(f"  Property Type: {result.property_listing_type}")
        print(f"  Amenities: {result.amenities}")
        print(f"  Description: {result.description[:100]}..." if result.description else "No description")
        
        # Create a mock listing dict for semantic analysis
        listing_dict = {
            'title': result.title,
            'description': result.description,
            'city': result.city,
            'neighborhood': result.neighborhood,
            'property_listing_type': result.property_listing_type,
            'amenities': result.amenities,
            'address': result.address
        }
        
        # Analyze semantic matches
        semantic_matches = scoring_engine._analyze_semantic_matches(listing_dict, intent)
        soft_matches = scoring_engine._analyze_soft_preferences(listing_dict, intent)
        
        print(f"\n  SEMANTIC MATCHES:")
        if semantic_matches:
            for match in semantic_matches:
                print(f"    {match}")
        else:
            print("    None found")
        
        print(f"\n  SOFT PREFERENCE MATCHES:")
        if soft_matches:
            for match in soft_matches:
                print(f"    {match}")
        else:
            print("    None found")
        
        print(f"\n  FINAL SCORE: {result.similarity_score:.3f}")
        
        if hasattr(result, 'score_breakdown') and result.score_breakdown:
            print(f"  SCORE BREAKDOWN:")
            for component, score in result.score_breakdown.items():
                if component != 'final_score':
                    print(f"    • {component}: {score:.3f}")
    
    print("\n" + "=" * 80)
    print("SEMANTIC MATCHING LOGIC EXPLAINED")
    print("=" * 80)
    
    print("\n1. TITLE MATCHING:")
    print("   - Checks if property_type appears in listing title")
    print("   - Checks for renovation keywords: 'modern', 'updated', 'renovated', 'new'")
    print("   - Example: If intent.property_type = 'house', looks for 'house' in title")
    
    print("\n2. DESCRIPTION MATCHING:")
    print("   - Checks if property_type appears in listing description")
    print("   - Checks for renovation keywords in description")
    print("   - Example: If intent.renovated = True, looks for renovation keywords")
    
    print("\n3. LOCATION MATCHING:")
    print("   - Checks if city matches between intent and listing")
    print("   - Checks if neighborhood matches between intent and listing")
    print("   - Example: If intent.neighborhood = 'downtown', checks listing.neighborhood")
    
    print("\n4. FAMILY-FRIENDLY INDICATORS:")
    print("   - Looks for keywords: 'family', 'quiet', 'residential', 'school'")
    print("   - Only if intent.family_friendly = True")
    
    print("\n5. PET-FRIENDLY CHECKING:")
    print("   - Checks amenities array for 'pet' keyword")
    print("   - Example: Looks for 'Pet Friendly' in amenities list")
    
    print("\n6. SHORT-TERM RENTAL CHECKING:")
    print("   - Checks property_listing_type for 'rent' or 'both'")
    print("   - Example: If property_listing_type = 'rent', it's a rental")
    
    print("\n7. SOFT PREFERENCES (in _analyze_soft_preferences):")
    print("   - School ratings, crime index, walkability scores")
    print("   - Featured properties, yard availability")
    print("   - Modern design keywords, ocean view areas")
    print("   - Pet-friendly and short-term rental (duplicate checks)")
    
    print("\n" + "=" * 80)
    print("KEY DIFFERENCES: SEMANTIC vs STRUCTURED vs SOFT")
    print("=" * 80)
    
    print("\nSTRUCTURED MATCHING:")
    print("   - Exact field comparisons (bedrooms >= min_beds)")
    print("   - Numeric comparisons (price <= max_price)")
    print("   - Boolean checks (has_garage = True)")
    print("   - Contributes to match_percent (70% of final score)")
    
    print("\nSEMANTIC MATCHING:")
    print("   - Text-based keyword matching")
    print("   - Fuzzy matching in titles/descriptions")
    print("   - Used for generating reasons/explanations")
    print("   - Does NOT contribute to scoring (just for display)")
    
    print("\nSOFT PREFERENCES:")
    print("   - Bonus scoring for nice-to-have features")
    print("   - Contributes to soft_preference_bonus (10% of final score)")
    print("   - Includes both structured checks and semantic checks")
    
    # Cleanup
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_semantic_matching())
