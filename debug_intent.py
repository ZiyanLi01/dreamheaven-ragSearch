#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intent_extractor import IntentExtractor

def test_intent_extraction():
    extractor = IntentExtractor()
    query = "Give me a short-term rental in downtown that allows pets"
    
    print("=== INTENT EXTRACTION TEST ===")
    print(f"Query: '{query}'")
    print("=" * 50)
    
    intent = extractor.extract_intent(query)
    
    print("EXTRACTED INTENT:")
    print(f"  neighborhood: {intent.neighborhood}")
    print(f"  property_type: {intent.property_type}")
    print(f"  short_term_rental: {intent.short_term_rental}")
    print(f"  pet_friendly: {intent.pet_friendly}")
    print(f"  max_price_rent: {intent.max_price_rent}")
    print(f"  min_beds: {intent.min_beds}")
    print(f"  min_baths: {intent.min_baths}")
    print(f"  garage_required: {intent.garage_required}")
    print(f"  renovated: {intent.renovated}")
    print(f"  walk_to_metro: {intent.walk_to_metro}")
    
    print("\nEXPECTED:")
    print("  neighborhood: downtown")
    print("  property_type: None (should be None)")
    print("  short_term_rental: True")
    print("  pet_friendly: True")

if __name__ == "__main__":
    test_intent_extraction()
