#!/usr/bin/env python3
from dotenv import load_dotenv
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

def test_property_type_consistency():
    load_dotenv()
    scoring_engine = ScoringEngine()
    
    # Test query with studio property type
    query = "Looking for a studio near Golden Gate Park"
    
    # Extract intent
    intent_extractor = IntentExtractor()
    intent = intent_extractor.extract_intent(query)
    print(f"Intent: property_type={intent.property_type}")
    
    # Create a test listing with studio in title and description
    listing_dict = {
        'title': 'Beautiful Studio Apartment in Golden Gate Park',
        'description': 'This cozy studio apartment is perfect for single professionals',
        'property_listing_type': 'rent',
        'city': 'San Francisco',
        'state': 'CA',
        'neighborhood': 'Golden Gate Park',
        'amenities': [],
        'address': '123 Park Street',
        'bedrooms': 0,
        'bathrooms': 1,
        'square_feet': 500,
        'price_for_sale': None,
        'price_per_month': 2500,
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
    
    print(f"\nMatch Details:")
    print(f"  structured: {detailed_matches['structured']}")
    print(f"  semantic: {detailed_matches['semantic']}")
    print(f"  soft_preferences: {detailed_matches['soft_preferences']}")
    print(f"  missing: {detailed_matches['missing']}")
    
    # Check for consistency
    structured_property = [m for m in detailed_matches['structured'] if 'property type' in m]
    semantic_property = [m for m in detailed_matches['semantic'] if 'property type' in m]
    
    print(f"\nProperty Type Consistency Check:")
    print(f"  Structured: {structured_property}")
    print(f"  Semantic: {semantic_property}")
    
    if structured_property and semantic_property:
        print(f"  ✅ Consistent: Both show '{structured_property[0]}'")
    else:
        print(f"  ❌ Inconsistent: Structured={structured_property}, Semantic={semantic_property}")

if __name__ == "__main__":
    test_property_type_consistency()
