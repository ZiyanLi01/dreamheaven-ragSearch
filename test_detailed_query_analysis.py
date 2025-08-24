#!/usr/bin/env python3
"""
Detailed Query Analysis Test
Shows step-by-step breakdown of query processing for:
"Give me a short-term rental in downtown that allows pets"
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

async def analyze_query_detailed():
    """Analyze the query step by step"""
    
    # Initialize components
    config = Config()
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.initialize()
    
    openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    search_engine = SearchEngine(db_manager, openai_client)
    intent_extractor = IntentExtractor()
    
    query = "Give me a short-term rental in downtown that allows pets"
    
    print("=" * 80)
    print("DETAILED QUERY ANALYSIS")
    print("=" * 80)
    print(f"Query: {query}")
    print()
    
    # Step 1: Extract Intent
    print("STEP 1: INTENT EXTRACTION")
    print("-" * 40)
    try:
        intent = intent_extractor.extract_intent(query)
        print("✅ Intent extracted successfully")
        print()
        
        # Display intent object
        print("Intent Object:")
        print(json.dumps(intent.__dict__, indent=2, default=str))
        print()
        
    except Exception as e:
        print(f"❌ Intent extraction failed: {e}")
        return
    
    # Step 2: Generate "What You Need" Description
    print("STEP 2: 'WHAT YOU NEED' DESCRIPTION")
    print("-" * 40)
    try:
        what_you_need = search_engine._generate_what_you_need(intent)
        print("✅ 'What You Need' description generated")
        print()
        print("What You Need:")
        print(what_you_need)
        print()
        
    except Exception as e:
        print(f"❌ 'What You Need' generation failed: {e}")
        return
    
    # Step 3: Count Intent Fields (before structured filters)
    print("STEP 3: INTENT FIELD COUNT (BEFORE STRUCTURED FILTERS)")
    print("-" * 40)
    intent_fields = {k: v for k, v in intent.__dict__.items() if v is not None and v != ""}
    print(f"Number of non-empty intent fields: {len(intent_fields)}")
    print("Non-empty intent fields:")
    for field, value in intent_fields.items():
        print(f"  • {field}: {value}")
    print()
    
    # Step 4: Apply Structured Filters (if any)
    print("STEP 4: STRUCTURED FILTERS APPLICATION")
    print("-" * 40)
    structured_filters = {}  # No additional filters in this test
    if structured_filters:
        intent = search_engine._apply_structured_filters(intent, structured_filters)
        print("✅ Structured filters applied")
    else:
        print("ℹ️  No structured filters to apply")
    print()
    
    # Step 5: Count Intent Fields (after structured filters)
    print("STEP 5: INTENT FIELD COUNT (AFTER STRUCTURED FILTERS)")
    print("-" * 40)
    intent_fields_after = {k: v for k, v in intent.__dict__.items() if v is not None and v != ""}
    print(f"Number of non-empty intent fields: {len(intent_fields_after)}")
    print("Non-empty intent fields:")
    for field, value in intent_fields_after.items():
        print(f"  • {field}: {value}")
    print()
    
    # Step 6: Perform Search and Get Results
    print("STEP 6: SEARCH EXECUTION")
    print("-" * 40)
    try:
        results = await search_engine.search(
            query=query,
            limit=10,
            generate_reasons=True
        )
        print(f"✅ Search completed successfully")
        print(f"Number of results returned: {len(results.items)}")
        print()
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return
    
    # Step 7: Display Top 10 Results with Scores
    print("STEP 7: TOP 10 RESULTS WITH FINAL SCORES")
    print("-" * 40)
    print(f"{'Rank':<4} {'Score':<8} {'ID':<8} {'Title':<50} {'Location':<30}")
    print("-" * 100)
    
    for i, result in enumerate(results.items[:10], 1):
        score = result.similarity_score
        listing_id = result.id
        title = result.title[:47] + "..." if len(result.title) > 50 else result.title
        location = f"{result.city}, {result.state}" if result.city and result.state else "N/A"
        
        print(f"{i:<4} {score:<8.3f} {listing_id:<8} {title:<50} {location:<30}")
    
    print()
    
    # Step 8: Detailed Score Breakdown for Top Result
    if results.items:
        print("STEP 8: DETAILED SCORE BREAKDOWN (TOP RESULT)")
        print("-" * 40)
        top_result = results.items[0]
        print(f"Top Result ID: {top_result.id}")
        print(f"Title: {top_result.title}")
        print(f"Final Score: {top_result.similarity_score:.3f}")
        print()
        
        if hasattr(top_result, 'score_breakdown') and top_result.score_breakdown:
            print("Score Details:")
            score_details = top_result.score_breakdown
            for component, score in score_details.items():
                if component != 'final_score':
                    print(f"  • {component}: {score:.3f}")
        else:
            print("ℹ️  Score details not available")
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    # Cleanup
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(analyze_query_detailed())
