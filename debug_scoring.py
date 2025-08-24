#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intent_extractor import IntentExtractor
from scoring import ScoringEngine

def test_scoring():
    extractor = IntentExtractor()
    scoring_engine = ScoringEngine()
    
    query = "Give me a short-term rental in downtown that allows pets"
    intent = extractor.extract_intent(query)
    
    print("=== SCORING TEST ===")
    print(f"Query: '{query}'")
    print("=" * 50)
    
    print("EXTRACTED INTENT:")
    print(f"  neighborhood: {intent.neighborhood}")
    print(f"  short_term_rental: {intent.short_term_rental}")
    print(f"  pet_friendly: {intent.pet_friendly}")
    
    # Create a mock listing that should have some matches
    mock_listing = {
        'id': 1,
        'title': 'Downtown Rental Studio - Pet Friendly',
        'description': 'A beautiful studio apartment in downtown area. Short-term rental available. Pets welcome!',
        'address': '123 Downtown Street, San Francisco, CA',
        'property_type': 'studio',
        'pets_allowed': True,
        'similarity_score': 0.359
    }
    
    print(f"\nMOCK LISTING (WITH MATCHES):")
    print(f"  title: {mock_listing['title']}")
    print(f"  property_type: {mock_listing['property_type']}")
    print(f"  pets_allowed: {mock_listing['pets_allowed']}")
    print(f"  similarity_score: {mock_listing['similarity_score']}")
    
    # Test scoring
    print(f"\nTESTING SCORING:")
    score_details = scoring_engine.calculate_score_with_details(mock_listing, intent)
    
    print(f"Final Score: {score_details['final_score']:.3f}")
    print(f"Similarity Score: {score_details['similarity_score']:.3f}")
    print(f"Match Percentage: {score_details['match_percent']:.3f}")
    print(f"Soft Bonus: {score_details['soft_preference_bonus']:.3f}")
    
    print(f"\nMATCH DETAILS:")
    for category, matches in score_details['matches'].items():
        print(f"  {category.upper()}:")
        if matches:
            for match in matches:
                print(f"    {match}")
        else:
            print(f"    [] (empty)")

if __name__ == "__main__":
    test_scoring()
