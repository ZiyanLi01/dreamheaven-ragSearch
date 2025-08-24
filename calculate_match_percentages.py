import asyncio
import aiohttp
import json

async def get_candidate_details():
    """Get the actual candidate details to calculate match percentages"""
    url = "http://localhost:8001/ai-search"
    payload = {
        "query": "Find me a renovated condo near a BART station with parking.",
        "limit": 10,
        "reasons": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('items', [])
            return []

def calculate_match_percent_for_candidate(listing, intent):
    """Calculate match percentage for a specific candidate"""
    criteria_weights = {
        'budget': 0.35,
        'bedrooms': 0.25,
        'bathrooms': 0.15,
        'garage': 0.10,
        'metro': 0.10,
        'school': 0.05
    }
    
    matched_criteria = []
    unmatched_criteria = []
    total_weight = 0.0
    weighted_score = 0.0
    
    # For this query, we have:
    # - garage_required = True
    # - walk_to_metro = True
    # - property_type = 'condo'
    # - renovated = True
    
    # Check garage requirement
    if intent.get('garage_required'):
        total_weight += criteria_weights['garage']
        has_garage = listing.get('garage_number', 0) > 0 or listing.get('has_parking_lot', False)
        if has_garage:
            matched_criteria.append('garage')
            weighted_score += criteria_weights['garage']
        else:
            unmatched_criteria.append('garage')
    
    # Check walk to metro
    if intent.get('walk_to_metro'):
        total_weight += criteria_weights['metro']
        shopping_idx = listing.get('shopping_idx')
        if shopping_idx is not None and shopping_idx >= 7:
            matched_criteria.append('metro')
            weighted_score += criteria_weights['metro']
        else:
            unmatched_criteria.append('metro')
    
    # Check property type (condo)
    # This would be part of the structured filtering, not the match percent calculation
    
    match_percent = weighted_score / total_weight if total_weight > 0 else 0.0
    return match_percent, matched_criteria, unmatched_criteria

async def analyze_candidates():
    print("=== MATCH PERCENTAGE ANALYSIS ===")
    print("Query: Find me a renovated condo near a BART station with parking.")
    print()
    
    # Intent for this query
    intent = {
        'garage_required': True,
        'walk_to_metro': True,
        'property_type': 'condo',
        'renovated': True
    }
    
    candidates = await get_candidate_details()
    
    if not candidates or candidates[0].get('id') == 'no_results':
        print("No candidates found")
        return
    
    print(f"Found {len(candidates)} candidates")
    print()
    
    for i, candidate in enumerate(candidates, 1):
        print(f"=== CANDIDATE {i} ===")
        print(f"Title: {candidate.get('title', 'N/A')}")
        print(f"Address: {candidate.get('address', 'N/A')}")
        print(f"Property Type: {candidate.get('property_type', 'N/A')}")
        print(f"Garage Number: {candidate.get('garage_number', 'N/A')}")
        print(f"Shopping Index: {candidate.get('shopping_idx', 'N/A')}")
        print(f"Year Renovated: {candidate.get('year_renovated', 'N/A')}")
        print(f"Final Score: {candidate.get('similarity_score', 'N/A'):.2%}")
        print(f"Reason: {candidate.get('reason', 'N/A')}")
        
        # Calculate match percentage
        match_percent, matched, unmatched = calculate_match_percent_for_candidate(candidate, intent)
        print(f"Match Percentage: {match_percent:.1%}")
        print(f"Matched Criteria: {matched}")
        print(f"Unmatched Criteria: {unmatched}")
        print()

if __name__ == "__main__":
    asyncio.run(analyze_candidates())
