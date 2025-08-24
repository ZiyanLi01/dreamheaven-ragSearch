#!/usr/bin/env python3
from dotenv import load_dotenv
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

def test_all_criteria_consistency():
    load_dotenv()
    scoring_engine = ScoringEngine()
    
    # Define all criteria categories
    must_have_criteria = [
        'city', 'state', 'neighborhood', 'max_price_sale', 'max_price_rent', 
        'min_beds', 'min_baths', 'min_sqft', 'garage_required', 'property_type'
    ]
    
    nice_to_have_criteria = [
        'good_schools', 'yard', 'family_friendly', 'walk_to_metro', 'modern', 
        'renovated', 'ocean_view', 'mountain_view', 'quiet', 'featured', 
        'near_grocery', 'near_shopping', 'safe_area', 'walkable', 
        'dining_options', 'short_term_rental', 'pet_friendly'
    ]
    
    print("🔍 Testing All Criteria Consistency")
    print("=" * 80)
    
    # Test 1: Must-Have Criteria
    print("\n📋 MUST-HAVE CRITERIA TEST")
    print("-" * 40)
    
    must_have_query = "Find me a 2-bedroom apartment in downtown San Francisco, CA with at least 1000 sq ft, 2 bathrooms, garage, under $500k"
    intent = IntentExtractor().extract_intent(must_have_query)
    
    print(f"Query: {must_have_query}")
    print(f"Extracted Intent:")
    for criterion in must_have_criteria:
        value = getattr(intent, criterion)
        if value is not None and value != False:
            print(f"  ✓ {criterion}: {value}")
        else:
            print(f"  ✗ {criterion}: {value}")
    
    # Create test listing that matches all criteria
    listing_dict = {
        'title': 'Beautiful 2-Bedroom Apartment in Downtown',
        'description': 'Modern apartment with garage',
        'property_type': 'apartment',
        'property_listing_type': 'sale',
        'city': 'San Francisco',
        'state': 'CA',
        'neighborhood': 'downtown',
        'amenities': [],
        'address': '123 Downtown St',
        'bedrooms': 2,
        'bathrooms': 2,
        'square_feet': 1200,
        'price_for_sale': 450000,
        'price_per_month': None,
        'garage_number': 1,
        'has_parking_lot': True,
        'school_rating': 8.5,
        'crime_index': 2,
        'shopping_idx': 8,
        'grocery_idx': 7,
        'is_featured': False,
        'has_yard': False
    }
    
    detailed_matches = scoring_engine._calculate_detailed_matches(listing_dict, intent)
    
    print(f"\nMatch Results:")
    print(f"  structured: {detailed_matches['structured']}")
    print(f"  semantic: {detailed_matches['semantic']}")
    print(f"  soft_preferences: {detailed_matches['soft_preferences']}")
    print(f"  missing: {detailed_matches['missing']}")
    
    # Test 2: Nice-to-Have Criteria
    print("\n📋 NICE-TO-HAVE CRITERIA TEST")
    print("-" * 40)
    
    nice_to_have_query = "Show me featured apartments with good schools, yard, family-friendly, near metro, modern, renovated, ocean view, mountain view, quiet, near grocery, near shopping, safe area, walkable, dining options, short-term rental, pet-friendly"
    intent = IntentExtractor().extract_intent(nice_to_have_query)
    
    print(f"Query: {nice_to_have_query}")
    print(f"Extracted Intent:")
    for criterion in nice_to_have_criteria:
        value = getattr(intent, criterion)
        if value is not None and value != False:
            print(f"  ✓ {criterion}: {value}")
        else:
            print(f"  ✗ {criterion}: {value}")
    
    # Create test listing that matches many nice-to-have criteria
    listing_dict = {
        'title': 'Featured Modern Ocean View Apartment near Metro',
        'description': 'Renovated family-friendly apartment with mountain views, quiet neighborhood, near dining and restaurants. Pet-friendly with short-term rental available.',
        'property_type': 'apartment',
        'property_listing_type': 'rent',
        'city': 'San Francisco',
        'state': 'CA',
        'neighborhood': 'twin peaks',
        'amenities': ['pet friendly', 'parking', 'yard', 'metro access'],
        'address': '456 Twin Peaks Blvd',
        'bedrooms': 2,
        'bathrooms': 2,
        'square_feet': 1500,
        'price_for_sale': None,
        'price_per_month': 3500,
        'garage_number': 1,
        'has_parking_lot': True,
        'school_rating': 9.0,
        'crime_index': 1,
        'shopping_idx': 9,
        'grocery_idx': 8,
        'is_featured': True,
        'has_yard': True
    }
    
    detailed_matches = scoring_engine._calculate_detailed_matches(listing_dict, intent)
    
    print(f"\nMatch Results:")
    print(f"  structured: {detailed_matches['structured']}")
    print(f"  semantic: {detailed_matches['semantic']}")
    print(f"  soft_preferences: {detailed_matches['soft_preferences']}")
    print(f"  missing: {detailed_matches['missing']}")
    
    # Test 3: Consistency Analysis
    print("\n📋 CONSISTENCY ANALYSIS")
    print("-" * 40)
    
    # Check for duplicate reasons between structured and semantic
    structured_reasons = set(detailed_matches['structured'])
    semantic_reasons = set(detailed_matches['semantic'])
    soft_preference_reasons = set(detailed_matches['soft_preferences'])
    
    # Find duplicates
    structured_semantic_duplicates = structured_reasons.intersection(semantic_reasons)
    structured_soft_duplicates = structured_reasons.intersection(soft_preference_reasons)
    semantic_soft_duplicates = semantic_reasons.intersection(soft_preference_reasons)
    
    print(f"Duplicate Analysis:")
    if structured_semantic_duplicates:
        print(f"  ❌ Structured-Semantic duplicates: {structured_semantic_duplicates}")
    else:
        print(f"  ✅ No Structured-Semantic duplicates")
    
    if structured_soft_duplicates:
        print(f"  ❌ Structured-Soft duplicates: {structured_soft_duplicates}")
    else:
        print(f"  ✅ No Structured-Soft duplicates")
    
    if semantic_soft_duplicates:
        print(f"  ❌ Semantic-Soft duplicates: {semantic_soft_duplicates}")
    else:
        print(f"  ✅ No Semantic-Soft duplicates")
    
    # Check categorization logic
    print(f"\nCategorization Logic:")
    print(f"  Structured: Must-have criteria (hard filters)")
    print(f"  Semantic: Text-based matches for must-have criteria")
    print(f"  Soft Preferences: Nice-to-have criteria (bonus features)")
    
    # Check specific criteria handling
    print(f"\nSpecific Criteria Handling:")
    
    # Must-have criteria should be in structured
    must_have_in_structured = []
    for criterion in must_have_criteria:
        if any(criterion.replace('_', ' ') in reason.lower() for reason in detailed_matches['structured']):
            must_have_in_structured.append(criterion)
    
    print(f"  Must-have in structured: {must_have_in_structured}")
    
    # Nice-to-have criteria should be in soft_preferences
    nice_to_have_in_soft = []
    for criterion in nice_to_have_criteria:
        if any(criterion.replace('_', ' ') in reason.lower() for reason in detailed_matches['soft_preferences']):
            nice_to_have_in_soft.append(criterion)
    
    print(f"  Nice-to-have in soft_preferences: {nice_to_have_in_soft}")

if __name__ == "__main__":
    test_all_criteria_consistency()
