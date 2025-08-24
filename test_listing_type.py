#!/usr/bin/env python3
from dotenv import load_dotenv
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

def test_listing_type():
    load_dotenv()
    scoring_engine = ScoringEngine()
    
    # Test query with listing type
    query = "Find me live/work lofts in Dogpatch suitable for artists. in San Francisco, CA for rent"
    
    # Extract intent
    intent_extractor = IntentExtractor()
    intent = intent_extractor.extract_intent(query)
    print(f"Query: {query}")
    print(f"Extracted Intent:")
    print(f"  property_type: {intent.property_type}")
    print(f"  listing_type: {intent.listing_type}")
    print(f"  city: {intent.city}")
    print(f"  state: {intent.state}")
    
    # Create test listings
    test_listings = [
        {
            'title': 'Live/Work Loft in Dogpatch',
            'description': 'Perfect for artists',
            'property_type': 'loft',
            'property_listing_type': 'rent',
            'city': 'San Francisco',
            'state': 'CA',
            'neighborhood': 'Dogpatch',
            'amenities': [],
            'address': '123 Dogpatch St',
            'bedrooms': 1,
            'bathrooms': 1,
            'square_feet': 1000,
            'price_for_sale': None,
            'price_per_month': 2500,
            'garage_number': 0,
            'has_parking_lot': False,
            'school_rating': 8.0,
            'crime_index': 3,
            'shopping_idx': 7,
            'grocery_idx': 6,
            'is_featured': False,
            'has_yard': False
        },
        {
            'title': 'Live/Work Loft in Dogpatch',
            'description': 'Perfect for artists',
            'property_type': 'loft',
            'property_listing_type': 'sale',  # Wrong listing type
            'city': 'San Francisco',
            'state': 'CA',
            'neighborhood': 'Dogpatch',
            'amenities': [],
            'address': '123 Dogpatch St',
            'bedrooms': 1,
            'bathrooms': 1,
            'square_feet': 1000,
            'price_for_sale': 500000,
            'price_per_month': None,
            'garage_number': 0,
            'has_parking_lot': False,
            'school_rating': 8.0,
            'crime_index': 3,
            'shopping_idx': 7,
            'grocery_idx': 6,
            'is_featured': False,
            'has_yard': False
        }
    ]
    
    for i, listing in enumerate(test_listings, 1):
        print(f"\n{'='*60}")
        print(f"Test Listing {i}: {listing['property_listing_type']} property")
        print(f"{'='*60}")
        
        # Get detailed matches
        detailed_matches = scoring_engine._calculate_detailed_matches(listing, intent)
        
        print(f"Match Details:")
        print(f"  structured: {detailed_matches['structured']}")
        print(f"  semantic: {detailed_matches['semantic']}")
        print(f"  soft_preferences: {detailed_matches['soft_preferences']}")
        print(f"  missing: {detailed_matches['missing']}")
        
        # Get score breakdown
        score_details = scoring_engine.calculate_score_with_details(listing, intent)
        print(f"\nScore Breakdown:")
        print(f"  final_score: {score_details['final_score']:.3f}")
        print(f"  similarity_score: {score_details['similarity_score']:.3f}")
        print(f"  match_percent: {score_details['match_percent']:.3f}")
        print(f"  soft_preference_bonus: {score_details['soft_preference_bonus']:.3f}")

if __name__ == "__main__":
    test_listing_type()
