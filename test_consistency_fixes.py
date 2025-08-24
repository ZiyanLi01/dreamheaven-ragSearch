#!/usr/bin/env python3
from dotenv import load_dotenv
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

def test_consistency_fixes():
    load_dotenv()
    scoring_engine = ScoringEngine()
    
    # Test queries
    test_cases = [
        {
            'query': 'Looking for a studio near Golden Gate Park in San Francisco, CA',
            'description': 'Studio property type and location consistency'
        },
        {
            'query': 'Show me modern apartments in downtown',
            'description': 'Modern/renovated features consistency'
        },
        {
            'query': 'Find me a 2-bedroom house in Nob Hill',
            'description': 'Bedrooms and property type consistency'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print(f"{'='*60}")
        
        # Extract intent
        intent_extractor = IntentExtractor()
        intent = intent_extractor.extract_intent(test_case['query'])
        print(f"Intent: {intent}")
        
        # Create a test listing
        listing_dict = {
            'title': 'Beautiful Studio Apartment in Golden Gate Park',
            'description': 'This modern studio apartment is perfect for single professionals',
            'property_type': 'studio',
            'property_listing_type': 'rent',
            'city': 'San Francisco',
            'state': 'CA',
            'neighborhood': 'Golden Gate Park',
            'amenities': ['pet friendly', 'parking'],
            'address': '123 Park Street',
            'bedrooms': 2,
            'bathrooms': 1,
            'square_feet': 800,
            'price_for_sale': None,
            'price_per_month': 2500,
            'garage_number': 1,
            'has_parking_lot': True,
            'school_rating': 8.5,
            'crime_index': 2,
            'shopping_idx': 8,
            'grocery_idx': 7,
            'is_featured': True,
            'has_yard': False
        }
        
        # Get detailed matches
        detailed_matches = scoring_engine._calculate_detailed_matches(listing_dict, intent)
        
        print(f"\nMatch Details:")
        print(f"  structured: {detailed_matches['structured']}")
        print(f"  semantic: {detailed_matches['semantic']}")
        print(f"  soft_preferences: {detailed_matches['soft_preferences']}")
        print(f"  missing: {detailed_matches['missing']}")
        
        # Check for consistency issues
        print(f"\nConsistency Analysis:")
        
        # Property type consistency
        structured_property = [m for m in detailed_matches['structured'] if 'property type' in m]
        semantic_property = [m for m in detailed_matches['semantic'] if 'property type' in m]
        
        if structured_property and semantic_property:
            if structured_property[0] == semantic_property[0]:
                print(f"  ✅ Property Type: Consistent - {structured_property[0]}")
            else:
                print(f"  ❌ Property Type: Inconsistent")
                print(f"     Structured: {structured_property[0]}")
                print(f"     Semantic: {semantic_property[0]}")
        
        # Location consistency
        structured_location = [m for m in detailed_matches['structured'] if 'Located in' in m]
        semantic_location = [m for m in detailed_matches['semantic'] if 'Located in' in m]
        
        if structured_location and semantic_location:
            if structured_location[0] == semantic_location[0]:
                print(f"  ✅ Location: Consistent - {structured_location[0]}")
            else:
                print(f"  ❌ Location: Inconsistent")
                print(f"     Structured: {structured_location[0]}")
                print(f"     Semantic: {semantic_location[0]}")
        
        # Modern/renovated consistency
        structured_modern = [m for m in detailed_matches['structured'] if 'modern' in m.lower() or 'renovated' in m.lower()]
        semantic_modern = [m for m in detailed_matches['semantic'] if 'modern' in m.lower() or 'renovated' in m.lower()]
        
        if structured_modern or semantic_modern:
            if structured_modern == semantic_modern:
                print(f"  ✅ Modern/Renovated: Consistent")
            else:
                print(f"  ❌ Modern/Renovated: Inconsistent")
                print(f"     Structured: {structured_modern}")
                print(f"     Semantic: {semantic_modern}")

if __name__ == "__main__":
    test_consistency_fixes()
