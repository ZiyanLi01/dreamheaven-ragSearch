#!/usr/bin/env python3
"""
Match Details Structure Test
Shows the complete match details structure with unified labels
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

async def test_match_details_structure():
    """Test the complete match details structure"""
    
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
    print("MATCH DETAILS STRUCTURE ANALYSIS")
    print("=" * 80)
    print(f"Query: {query}")
    print()
    
    # Extract intent
    intent = intent_extractor.extract_intent(query)
    
    # Get results
    results = await search_engine.search(
        query=query,
        limit=3,
        generate_reasons=True
    )
    
    print("COMPLETE MATCH DETAILS STRUCTURE:")
    print("-" * 80)
    
    for i, result in enumerate(results.items[:2], 1):
        print(f"\nLISTING {i}: {result.title}")
        print(f"  Final Score: {result.similarity_score:.3f}")
        
        # Create a mock listing dict for detailed analysis
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
            'shopping_idx': 8,
            'grocery_idx': 7,
            'is_featured': False,
            'has_yard': False
        }
        
        # Get detailed matches
        detailed_matches = scoring_engine._calculate_detailed_matches(listing_dict, intent)
        
        print(f"\n  MATCH DETAILS:")
        print(f"    missing: {detailed_matches['missing']}")
        print(f"    semantic: {detailed_matches['semantic']}")
        print(f"    soft_preferences: {detailed_matches['soft_preferences']}")
        print(f"    structured: {detailed_matches['structured']}")
        
        # Show score breakdown
        if hasattr(result, 'score_breakdown') and result.score_breakdown:
            print(f"\n  SCORE BREAKDOWN:")
            for component, score in result.score_breakdown.items():
                if component != 'final_score':
                    print(f"    • {component}: {score:.3f}")
    
    print("\n" + "=" * 80)
    print("UNIFIED LABELS EXPLANATION")
    print("=" * 80)
    
    print("\nSTRUCTURED MATCHES (70% of score):")
    print("  • Location: '✓ Located in [city/state/neighborhood]'")
    print("  • Budget: '✓ Under $[amount]'")
    print("  • Bedrooms: '✓ [count] bedrooms (≥[min])'")
    print("  • Bathrooms: '✓ [count] bathrooms (≥[min])'")
    print("  • Square Feet: '✓ [sqft] sq ft (≥[min])'")
    print("  • Property Type: '✓ [type] property type'")
    print("  • Garage: '✓ Has parking/garage'")
    print("  • Metro: '✓ Metro accessible (walkability: [score]/10)'")
    print("  • Renovated: '✓ Recently renovated ([year])'")
    
    print("\nSEMANTIC MATCHES (display only):")
    print("  • Title mentions: '✓ Title mentions [property_type]'")
    print("  • Description mentions: '✓ Description mentions [property_type]'")
    print("  • Modern features: '✓ Title mentions modern/renovated features'")
    print("  • Family-friendly: '✓ Family-friendly area mentioned'")
    
    print("\nSOFT PREFERENCES (10% bonus):")
    print("  • Pet-friendly: '✓ Pet-friendly property'")
    print("  • Short-term rental: '✓ Short-term rental available'")
    print("  • Schools: '✓ Good schools nearby (rating: [score]/10)'")
    print("  • Safety: '✓ Safe area (crime index: [score]/10)'")
    print("  • Walkability: '✓ Walkable area (walkability: [score]/10)'")
    print("  • Featured: '✓ Featured property'")
    print("  • Yard: '✓ Has yard/outdoor space'")
    print("  • Grocery: '✓ Near grocery stores (accessibility: [score]/10)'")
    print("  • Modern: '✓ Modern design/features'")
    print("  • Ocean view: '✓ Ocean view area'")
    print("  • Quiet: '✓ Quiet neighborhood (crime index: [score]/10)'")
    
    print("\n" + "=" * 80)
    print("FRONTEND INTEGRATION")
    print("=" * 80)
    
    print("\nFor frontend, you can now:")
    print("1. Combine all matches into a single list")
    print("2. Remove duplicates based on the text content")
    print("3. Group by category (Location, Features, etc.)")
    print("4. Show missing criteria separately")
    
    print("\nExample frontend logic:")
    print("```javascript")
    print("const allMatches = [")
    print("  ...structured,")
    print("  ...semantic,")
    print("  ...soft_preferences")
    print("];")
    print("const uniqueMatches = [...new Set(allMatches)];")
    print("```")
    
    # Cleanup
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_match_details_structure())
