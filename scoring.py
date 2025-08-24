"""
Scoring engine module for DreamHeaven RAG API
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Calculate scores for property listings based on search intent"""
    
    def __init__(self):
        # Criteria weights for scoring - covers all must-have criteria
        self.criteria_weights = {
            'budget_sale': 0.15,      # max_price_sale
            'budget_rent': 0.15,      # max_price_rent
            'bedrooms': 0.15,         # min_beds
            'bathrooms': 0.10,        # min_baths
            'square_feet': 0.10,      # min_sqft
            'location': 0.15,         # city, state, neighborhood
            'garage': 0.05,           # garage_required
            'metro': 0.05,            # walk_to_metro
            'property_type': 0.10,    # property_type
            'renovated': 0.05         # renovated
        }
    
    def calculate_score(self, listing: Dict[str, Any], intent) -> float:
        """Calculate final score for a listing"""
        try:
            # Get similarity score from vector search
            similarity_score = listing.get('similarity_score')
            if similarity_score is None:
                similarity_score = 0.0
            else:
                similarity_score = float(similarity_score)
            
            # Calculate match percentage for structured criteria
            match_percent, _, _ = self._calculate_match_percent(listing, intent)
            
            # Calculate soft preference bonus
            soft_preference_bonus = self._calculate_soft_preference_bonus(listing, intent)
            
            # Final score: 50% matches + 40% semantic + 10% preference
            final_score = (
                0.5 * match_percent +
                0.4 * similarity_score +
                0.1 * soft_preference_bonus
            )
            
            return min(final_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating score for listing {listing.get('id', 'unknown')}: {e}")
            return 0.0
    
    def calculate_score_with_details(self, listing: Dict[str, Any], intent) -> Dict[str, Any]:
        """Calculate final score with detailed match information"""
        try:
            # Get similarity score from vector search
            similarity_score = listing.get('similarity_score')
            if similarity_score is None:
                similarity_score = 0.0
            else:
                similarity_score = float(similarity_score)
            
            # Calculate detailed matches
            matches = self._calculate_detailed_matches(listing, intent)
            
            # Calculate match percentage for structured criteria
            match_percent, _, _ = self._calculate_match_percent(listing, intent)
            
            # Calculate soft preference bonus
            soft_preference_bonus = self._calculate_soft_preference_bonus(listing, intent)
            
            # Final score: 50% matches + 40% semantic + 10% preference
            final_score = (
                0.5 * match_percent +
                0.4 * similarity_score +
                0.1 * soft_preference_bonus
            )
            
            return {
                'final_score': min(final_score, 1.0),
                'similarity_score': similarity_score,
                'match_percent': match_percent,
                'soft_preference_bonus': soft_preference_bonus,
                'matches': matches
            }
            
        except Exception as e:
            logger.error(f"Error calculating score with details for listing {listing.get('id', 'unknown')}: {e}")
            return {
                'final_score': 0.0,
                'similarity_score': 0.0,
                'match_percent': 0.0,
                'soft_preference_bonus': 0.0,
                'matches': {'structured': [], 'semantic': [], 'soft_preferences': [], 'missing': []}
            }
    
    def _calculate_match_percent(self, listing: Dict[str, Any], intent) -> tuple:
        """Calculate match percentage for structured criteria"""
        matched_criteria = []
        unmatched_criteria = []
        total_weight = 0.0
        weighted_score = 0.0
        
        # Check each criterion
        if intent.max_price_sale:
            total_weight += self.criteria_weights['budget_sale']
            price = listing.get('price_for_sale')
            if price is not None and price <= intent.max_price_sale:
                matched_criteria.append('budget_sale')
                weighted_score += self.criteria_weights['budget_sale']
            else:
                unmatched_criteria.append('budget_sale')
        
        if intent.max_price_rent:
            total_weight += self.criteria_weights['budget_rent']
            rent = listing.get('price_per_month')
            if rent is not None and rent <= intent.max_price_rent:
                matched_criteria.append('budget_rent')
                weighted_score += self.criteria_weights['budget_rent']
            else:
                unmatched_criteria.append('budget_rent')
        
        if intent.min_beds:
            total_weight += self.criteria_weights['bedrooms']
            beds = listing.get('bedrooms')
            if beds is not None and beds >= intent.min_beds:
                matched_criteria.append('bedrooms')
                weighted_score += self.criteria_weights['bedrooms']
            else:
                unmatched_criteria.append('bedrooms')
        
        if intent.min_baths:
            total_weight += self.criteria_weights['bathrooms']
            baths = listing.get('bathrooms')
            if baths is not None and baths >= intent.min_baths:
                matched_criteria.append('bathrooms')
                weighted_score += self.criteria_weights['bathrooms']
            else:
                unmatched_criteria.append('bathrooms')
        
        if intent.min_sqft:
            total_weight += self.criteria_weights['square_feet']
            sqft = listing.get('square_feet')
            if sqft is not None and sqft >= intent.min_sqft:
                matched_criteria.append('square_feet')
                weighted_score += self.criteria_weights['square_feet']
            else:
                unmatched_criteria.append('square_feet')
        
        # Location matching (city, state, neighborhood)
        location_matched = False
        location_weight = self.criteria_weights['location']
        
        if intent.city or intent.state or intent.neighborhood:
            total_weight += location_weight
            
            # Check city match
            if intent.city:
                listing_city = listing.get('city', '').lower()
                if listing_city == intent.city.lower():
                    location_matched = True
            
            # Check state match
            if intent.state:
                listing_state = listing.get('state', '').lower()
                if listing_state == intent.state.lower():
                    location_matched = True
            
            # Check neighborhood match
            if intent.neighborhood:
                listing_neighborhood = listing.get('neighborhood', '').lower()
                if listing_neighborhood == intent.neighborhood.lower():
                    location_matched = True
            
            if location_matched:
                matched_criteria.append('location')
                weighted_score += location_weight
            else:
                unmatched_criteria.append('location')
        
        if intent.garage_required:
            total_weight += self.criteria_weights['garage']
            garage_number = listing.get('garage_number')
            has_parking_lot = listing.get('has_parking_lot', False)
            has_garage = (garage_number is not None and garage_number > 0) or has_parking_lot
            if has_garage:
                matched_criteria.append('garage')
                weighted_score += self.criteria_weights['garage']
            else:
                unmatched_criteria.append('garage')
        
        if intent.walk_to_metro:
            total_weight += self.criteria_weights['metro']
            shopping_idx = listing.get('shopping_idx')
            if shopping_idx is not None and shopping_idx >= 7:
                matched_criteria.append('metro')
                weighted_score += self.criteria_weights['metro']
            else:
                unmatched_criteria.append('metro')
        
        # Property type matching
        if intent.property_type:
            try:
                total_weight += self.criteria_weights['property_type']
                listing_type = listing.get('property_type')
                
                # Handle different data types for property_type
                if listing_type is None:
                    listing_type = ''
                elif not isinstance(listing_type, str):
                    # Convert non-string types to string
                    listing_type = str(listing_type)
                
                listing_type = listing_type.lower()
                if intent.property_type and (intent.property_type.lower() in listing_type or listing_type in intent.property_type.lower()):
                    matched_criteria.append('property_type')
                    weighted_score += self.criteria_weights['property_type']
                else:
                    unmatched_criteria.append('property_type')
            except Exception as e:
                logger.error(f"Error in property_type matching: {e}")
                logger.error(f"intent.property_type: {intent.property_type}")
                logger.error(f"listing: {listing}")
                # Continue without property_type matching
                pass
        
        # Renovated matching
        if intent.renovated:
            renovated_weight = 0.05
            total_weight += renovated_weight
            year_renovated = listing.get('year_renovated')
            if year_renovated is not None and year_renovated >= 2020:
                matched_criteria.append('renovated')
                weighted_score += renovated_weight
            else:
                unmatched_criteria.append('renovated')
        
        match_percent = weighted_score / total_weight if total_weight > 0 else 0.0
        return match_percent, matched_criteria, unmatched_criteria
    
    def _calculate_soft_preference_bonus(self, listing: Dict[str, Any], intent) -> float:
        """Calculate soft preference bonus"""
        bonus = 0.0
        
        school_rating = listing.get('school_rating')
        if intent.good_schools and school_rating is not None and school_rating >= 8:
            bonus += 0.08
        
        crime_index = listing.get('crime_index')
        if intent.safe_area and crime_index is not None and crime_index <= 3:
            bonus += 0.06
        
        shopping_idx = listing.get('shopping_idx')
        if intent.walkable and shopping_idx is not None and shopping_idx >= 7:
            bonus += 0.05
        
        if intent.featured and listing.get('is_featured', False):
            bonus += 0.06
        
        if intent.yard and listing.get('has_yard', False):
            bonus += 0.05
        
        grocery_idx = listing.get('grocery_idx')
        if intent.near_grocery and grocery_idx is not None and grocery_idx >= 7:
            bonus += 0.05
        if intent.modern:
            # Check title for modern keywords
            title = listing.get('title')
            if title:
                title_lower = title.lower()
                if any(word in title_lower for word in ['modern', 'contemporary', 'new', 'updated']):
                    bonus += 0.04
        if intent.ocean_view:
            # Check if in water-adjacent areas
            water_areas = ['marina', 'pacific heights', 'presidio', 'richmond', 'sunset']
            address = listing.get('address')
            if address:
                address_lower = address.lower()
                if any(area in address_lower for area in water_areas):
                    bonus += 0.07
        if intent.quiet:
            # Use crime_index as proxy for quietness
            crime_index = listing.get('crime_index')
            if crime_index is not None and crime_index <= 3:
                bonus += 0.03
            else:
                # Fallback: assume quiet if in residential areas
                quiet_areas = ['pacific heights', 'presidio heights', 'russian hill', 'marina']
                address = listing.get('address')
                if address:
                    address_lower = address.lower()
                    if any(area in address_lower for area in quiet_areas):
                        bonus += 0.03
        
        # Check for pet-friendly in amenities
        if intent.pet_friendly:
            amenities = listing.get('amenities', [])
            if isinstance(amenities, list) and any('pet' in amenity.lower() for amenity in amenities):
                bonus += 0.08
        
        # Check for short-term rental
        if intent.short_term_rental:
            property_type = listing.get('property_listing_type', '').lower()
            if property_type in ['rent', 'both']:
                bonus += 0.06
        
        return min(bonus, 0.5)  # Cap bonus at 0.5
    
    def _calculate_detailed_matches(self, listing: Dict[str, Any], intent) -> Dict[str, List[str]]:
        """Calculate detailed match information"""
        matches = {
            'structured': [],
            'semantic': [],
            'soft_preferences': [],
            'missing': []
        }
        
        # Check structured criteria matches
        if intent.max_price_sale:
            price = listing.get('price_for_sale')
            if price is not None and price <= intent.max_price_sale:
                matches['structured'].append(f"✓ Under ${intent.max_price_sale:,.0f} (${price:,.0f})")
            else:
                matches['missing'].append(f"✗ Over budget > ${intent.max_price_sale:,.0f}")
        
        if intent.max_price_rent:
            rent = listing.get('price_per_month')
            if rent is not None and rent <= intent.max_price_rent:
                matches['structured'].append(f"✓ Under ${intent.max_price_rent:,.0f}/month (${rent:,.0f})")
            else:
                matches['missing'].append(f"✗ Over budget > ${intent.max_price_rent:,.0f}/month")
        
        if intent.min_beds:
            beds = listing.get('bedrooms')
            if beds is not None and beds >= intent.min_beds:
                matches['structured'].append(f"✓ {beds} bedrooms (≥{intent.min_beds})")
            else:
                matches['missing'].append(f"✗ Need {intent.min_beds}+ bedrooms, got {beds}")
        
        if intent.min_baths:
            baths = listing.get('bathrooms')
            if baths is not None and baths >= intent.min_baths:
                matches['structured'].append(f"✓ {baths} bathrooms (≥{intent.min_baths})")
            else:
                matches['missing'].append(f"✗ Need {intent.min_baths}+ bathrooms, got {baths}")
        
        if intent.min_sqft:
            sqft = listing.get('square_feet')
            if sqft is not None and sqft >= intent.min_sqft:
                matches['structured'].append(f"✓ {sqft} sq ft (≥{intent.min_sqft})")
            else:
                matches['missing'].append(f"✗ Need {intent.min_sqft}+ sq ft, got {sqft}")
        
        # Location matching
        if intent.city or intent.state or intent.neighborhood:
            location_matches = []
            location_mismatches = []
            
            # Get location data
            listing_city = listing.get('city', '')
            listing_state = listing.get('state', '')
            listing_neighborhood = listing.get('neighborhood', '')
            
            # Check city and state matches
            city_match = False
            state_match = False
            
            if intent.city:
                if listing_city and listing_city.lower() == intent.city.lower():
                    city_match = True
                else:
                    location_mismatches.append(f"Looking for {intent.city}, got {listing_city}")
            
            if intent.state:
                if listing_state and listing_state.lower() == intent.state.lower():
                    state_match = True
                else:
                    location_mismatches.append(f"Looking for {intent.state}, got {listing_state}")
            
            # Combine city and state into a single location reason
            if city_match and state_match:
                location_matches.append(f"Located in {listing_city}, {listing_state}")
            elif city_match:
                location_matches.append(f"Located in {listing_city}")
            elif state_match:
                location_matches.append(f"Located in {listing_state}")
            
            # Check neighborhood match
            if intent.neighborhood:
                if listing_neighborhood and listing_neighborhood.lower() == intent.neighborhood.lower():
                    location_matches.append(f"Located in {listing_neighborhood}")
                else:
                    location_mismatches.append(f"Looking for {intent.neighborhood}, got {listing_neighborhood}")
            
            if location_matches:
                matches['structured'].extend([f"✓ {match}" for match in location_matches])
            if location_mismatches:
                matches['missing'].append(f"✗ Location: {', '.join(location_mismatches)}")
        
        if intent.property_type:
            try:
                listing_type = listing.get('property_type')
                if listing_type is None:
                    listing_type = ''
                elif not isinstance(listing_type, str):
                    listing_type = str(listing_type)
                
                listing_type = listing_type.lower()
                if intent.property_type.lower() in listing_type or listing_type in intent.property_type.lower():
                    matches['structured'].append(f"✓ {intent.property_type.title()} property type")
                else:
                    matches['missing'].append(f"✗ Need {intent.property_type}, got {listing_type}")
            except Exception as e:
                logger.error(f"Error in property type matching: {e}")
        
        # Check renovated/modern features
        if intent.renovated or intent.modern:
            title = listing.get('title', '').lower()
            description = listing.get('description', '').lower()
            if any(word in title for word in ['modern', 'updated', 'renovated', 'new']) or \
               any(word in description for word in ['modern', 'updated', 'renovated', 'new', 'recently']):
                matches['structured'].append("✓ Modern/renovated features")
        
        if intent.garage_required:
            garage_number = listing.get('garage_number')
            has_parking_lot = listing.get('has_parking_lot', False)
            has_garage = (garage_number is not None and garage_number > 0) or has_parking_lot
            if has_garage:
                matches['structured'].append("✓ Has parking/garage")
            else:
                matches['missing'].append("✗ No parking/garage")
        
        if intent.walk_to_metro:
            shopping_idx = listing.get('shopping_idx')
            if shopping_idx is not None and shopping_idx >= 7:
                matches['structured'].append(f"✓ Metro accessible (walkability: {shopping_idx}/10)")
            else:
                matches['missing'].append(f"✗ Limited transit access (walkability: {shopping_idx}/10)")
        
        # Note: renovated/modern features are handled in the earlier section
        
        # Check semantic matches
        semantic_matches = self._analyze_semantic_matches(listing, intent)
        matches['semantic'] = semantic_matches
        
        # Check soft preferences
        soft_matches = self._analyze_soft_preferences(listing, intent)
        matches['soft_preferences'] = soft_matches
        
        return matches
    
    def _analyze_semantic_matches(self, listing: Dict[str, Any], intent) -> List[str]:
        """Analyze semantic matches between listing and intent"""
        matches = []
        
        # Check title matches
        title = listing.get('title', '').lower()
        
        # Check description matches
        description = listing.get('description', '').lower()
        
        # Check location matches in text content (only show if intent specifies location)
        address = listing.get('address', '').lower()
        city = listing.get('city', '')
        state = listing.get('state', '')
        
        # Only show location if intent specifies it and it matches
        if intent.city and city and city.lower() == intent.city.lower():
            if intent.state and state and state.lower() == intent.state.lower():
                matches.append(f"✓ Located in {city}, {state}")
            else:
                matches.append(f"✓ Located in {city}")
        elif intent.state and state and state.lower() == intent.state.lower():
            matches.append(f"✓ Located in {state}")
        
        # Check if intent criteria match in text content (for additional context)
        if intent.neighborhood and intent.neighborhood.lower() in address:
            matches.append(f"✓ Located in {intent.neighborhood}")
        
        # Check for family-friendly indicators
        if intent.family_friendly:
            family_indicators = ['family', 'quiet', 'residential', 'school']
            if any(indicator in description.lower() for indicator in family_indicators):
                matches.append("✓ Family-friendly area mentioned")
        
        # Note: Pet-friendly and short-term rental are handled in soft preferences to avoid duplicates
        
        return matches
    
    def _analyze_soft_preferences(self, listing: Dict[str, Any], intent) -> List[str]:
        """Analyze soft preference matches"""
        matches = []
        
        school_rating = listing.get('school_rating')
        if intent.good_schools and school_rating is not None and school_rating >= 8:
            matches.append(f"✓ Good schools nearby (rating: {school_rating}/10)")
        
        crime_index = listing.get('crime_index')
        if intent.safe_area and crime_index is not None and crime_index <= 3:
            matches.append(f"✓ Safe area (crime index: {crime_index}/10)")
        
        shopping_idx = listing.get('shopping_idx')
        if intent.walkable and shopping_idx is not None and shopping_idx >= 7:
            matches.append(f"✓ Walkable area (walkability: {shopping_idx}/10)")
        
        if intent.featured and listing.get('is_featured', False):
            matches.append("✓ Featured property")
        
        if intent.yard and listing.get('has_yard', False):
            matches.append("✓ Has yard/outdoor space")
        
        grocery_idx = listing.get('grocery_idx')
        if intent.near_grocery and grocery_idx is not None and grocery_idx >= 7:
            matches.append(f"✓ Near grocery stores (accessibility: {grocery_idx}/10)")
        
        if intent.modern:
            title = listing.get('title', '').lower()
            if any(word in title for word in ['modern', 'contemporary', 'new', 'updated']):
                matches.append("✓ Modern design/features")
        
        if intent.ocean_view:
            water_areas = ['marina', 'pacific heights', 'presidio', 'richmond', 'sunset']
            address = listing.get('address', '').lower()
            if any(area in address for area in water_areas):
                matches.append("✓ Ocean view area")
        
        if intent.quiet:
            crime_index = listing.get('crime_index')
            if crime_index is not None and crime_index <= 3:
                matches.append(f"✓ Quiet neighborhood (crime index: {crime_index}/10)")
            else:
                quiet_areas = ['pacific heights', 'presidio heights', 'russian hill', 'marina']
                address = listing.get('address', '').lower()
                if any(area in address for area in quiet_areas):
                    matches.append("✓ Quiet residential area")
        
        # Check for pet-friendly in amenities
        if intent.pet_friendly:
            amenities = listing.get('amenities', [])
            if isinstance(amenities, list) and any('pet' in amenity.lower() for amenity in amenities):
                matches.append("✓ Pet-friendly property")
        
        # Check for short-term rental
        if intent.short_term_rental:
            property_type = listing.get('property_listing_type', '').lower()
            if property_type in ['rent', 'both']:
                matches.append("✓ Short-term rental available")
        
        # Check for mountain view
        if intent.mountain_view:
            mountain_areas = ['twin peaks', 'diamond heights', 'bernal heights', 'glen park']
            address = listing.get('address', '').lower()
            if any(area in address for area in mountain_areas):
                matches.append("✓ Mountain view area")
        
        # Check for dining options
        if intent.dining_options:
            dining_indicators = ['restaurant', 'cafe', 'dining', 'food']
            description = listing.get('description', '').lower()
            if any(indicator in description for indicator in dining_indicators):
                matches.append("✓ Dining options nearby")
        
        # Check for walk to metro (separate from walkable)
        if intent.walk_to_metro:
            transit_indicators = ['metro', 'bart', 'subway', 'transit', 'train']
            description = listing.get('description', '').lower()
            if any(indicator in description for indicator in transit_indicators):
                matches.append("✓ Walk to metro/transit")
        
        return matches
    
    def normalize_similarity_score(self, similarity_score: float) -> float:
        """Normalize similarity score"""
        return max(0.0, min(1.0, similarity_score))
