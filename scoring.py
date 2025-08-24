"""
Scoring engine module for DreamHeaven RAG API
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Calculate scores for property listings based on search intent"""
    
    def __init__(self):
        # Criteria weights for scoring
        self.criteria_weights = {
            'budget': 0.25,
            'bedrooms': 0.20,
            'bathrooms': 0.15,
            'garage': 0.10,
            'metro': 0.10,
            'property_type': 0.15,
            'renovated': 0.05
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
            
            # Final score: 70% similarity + 20% match percent + 10% soft preferences
            final_score = (
                0.7 * similarity_score +
                0.2 * match_percent +
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
            
            # Final score: 70% similarity + 20% match percent + 10% soft preferences
            final_score = (
                0.7 * similarity_score +
                0.2 * match_percent +
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
            total_weight += self.criteria_weights['budget']
            price = listing.get('price_for_sale')
            if price is not None and price <= intent.max_price_sale:
                matched_criteria.append('budget')
                weighted_score += self.criteria_weights['budget']
            else:
                unmatched_criteria.append('budget')
        
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
        
        if intent.property_type:
            try:
                listing_type = listing.get('property_type')
                if listing_type is None:
                    listing_type = ''
                elif not isinstance(listing_type, str):
                    listing_type = str(listing_type)
                
                listing_type = listing_type.lower()
                if intent.property_type.lower() in listing_type or listing_type in intent.property_type.lower():
                    matches['structured'].append(f"✓ {listing_type.title()} property type")
                else:
                    matches['missing'].append(f"✗ Need {intent.property_type}, got {listing_type}")
            except Exception as e:
                logger.error(f"Error in property type matching: {e}")
        
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
        
        if intent.renovated:
            year_renovated = listing.get('year_renovated')
            if year_renovated is not None and year_renovated >= 2020:
                matches['structured'].append(f"✓ Recently renovated ({year_renovated})")
            else:
                matches['missing'].append("✗ Not recently renovated")
        
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
        if intent.property_type and intent.property_type.lower() in title:
            matches.append(f"✓ Title mentions '{intent.property_type}'")
        
        if intent.renovated and any(word in title for word in ['modern', 'updated', 'renovated', 'new']):
            matches.append("✓ Title mentions modern/renovated features")
        
        # Check description matches
        description = listing.get('description', '').lower()
        if intent.renovated and any(word in description for word in ['modern', 'updated', 'renovated', 'new', 'recently']):
            matches.append("✓ Description mentions modern/renovated features")
        
        if intent.property_type and intent.property_type.lower() in description:
            matches.append(f"✓ Description mentions '{intent.property_type}'")
        
        # Check location matches
        address = listing.get('address', '').lower()
        city = listing.get('city', '').lower()
        neighborhood = listing.get('neighborhood', '').lower()
        
        if intent.city and (intent.city.lower() in address or intent.city.lower() in city):
            matches.append(f"✓ Located in {intent.city}")
        
        if intent.neighborhood and intent.neighborhood.lower() in neighborhood:
            matches.append(f"✓ Located in {intent.neighborhood}")
        
        # Check for family-friendly indicators
        if intent.family_friendly:
            family_indicators = ['family', 'quiet', 'residential', 'school']
            if any(indicator in description.lower() for indicator in family_indicators):
                matches.append("✓ Family-friendly area mentioned")
        
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
        
        return matches
    
    def normalize_similarity_score(self, similarity_score: float) -> float:
        """Normalize similarity score"""
        return max(0.0, min(1.0, similarity_score))
