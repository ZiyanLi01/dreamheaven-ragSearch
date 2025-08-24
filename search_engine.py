"""
Search engine module for DreamHeaven RAG API
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from openai import AsyncOpenAI

from models import SearchRequest, SearchResponse, ListingResult
from database import DatabaseManager
from intent_extractor import IntentExtractor
from scoring import ScoringEngine

logger = logging.getLogger(__name__)


from intent_extractor import SearchIntent


class SearchEngine:
    """Main search engine for property recommendations"""
    
    def __init__(self, db_manager: DatabaseManager, openai_client: AsyncOpenAI):
        self.db_manager = db_manager
        self.openai_client = openai_client
        self.intent_extractor = IntentExtractor()
        self.scoring_engine = ScoringEngine()
    
    async def search(
        self, 
        query: str, 
        limit: int = 10, 
        offset: int = 0, 
        generate_reasons: bool = True,
        structured_filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Main search method"""
        try:
            logger.info(f"Processing search query: {query}")
            
            # Step 1: Extract search intent
            try:
                intent = self.intent_extractor.extract_intent(query)
                logger.info(f"Intent extracted: property_type={intent.property_type}, min_beds={intent.min_beds}")
            except Exception as e:
                logger.error(f"Error extracting intent: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error args: {e.args}")
                raise Exception(f"Intent extraction failed: {str(e)}")
            
            # Step 2: Apply structured filters if provided
            if structured_filters:
                intent = self._apply_structured_filters(intent, structured_filters)
            
            # Step 3: Generate "What You Need" description
            what_you_need = self._generate_what_you_need(intent)
            
            # Step 4: Perform search
            results, used_fallback = await self._perform_search(query, intent, limit)
            
            # Add fallback information if used
            if used_fallback:
                what_you_need += "\n\nNote: No exact matches found with your specific criteria, so we expanded the search to find the most relevant properties available."
            
            # Step 5: Handle empty results
            if not results:
                return self._create_empty_response(query, limit, what_you_need)
            
            # Step 6: Generate reasons if requested
            if generate_reasons:
                await self._generate_reasons(query, results, intent)
            
            # Step 7: Convert to API response format
            items = self._convert_to_listing_results(results)
            
            logger.info(f"Search completed with {len(items)} results")
            
            return SearchResponse(
                items=items,
                query=query,
                page=1,
                limit=limit,
                has_more=len(items) == limit,
                generation_error=False,
                what_you_need=what_you_need
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            raise
    
    def _apply_structured_filters(self, intent: SearchIntent, filters: Dict[str, Any]) -> SearchIntent:
        """Apply structured filters to intent"""
        if filters.get('city'):
            intent.city = filters['city']
        if filters.get('state'):
            intent.state = filters['state']
        if filters.get('property_type'):
            intent.property_type = filters['property_type']
        if filters.get('min_bedrooms'):
            intent.min_beds = filters['min_bedrooms']
        if filters.get('min_bathrooms'):
            intent.min_baths = filters['min_bathrooms']
        if filters.get('max_price'):
            intent.max_price_sale = filters['max_price']
        
        return intent
    
    def _generate_what_you_need(self, intent: SearchIntent) -> str:
        """Generate enhanced user-friendly description of requirements with must-have vs nice-to-have separation"""
        must_have = []
        nice_to_have = []
        
        # Hard Filters (Must Have)
        if intent.city:
            must_have.append(f"in {intent.city}")
        if intent.state:
            must_have.append(f"in {intent.state}")
        if intent.neighborhood:
            must_have.append(f"in {intent.neighborhood}")
        if intent.max_price_sale:
            must_have.append(f"under ${intent.max_price_sale:,.0f}")
        if intent.max_price_rent:
            must_have.append(f"under ${intent.max_price_rent:,.0f}/month")
        if intent.min_beds:
            must_have.append(f"at least {intent.min_beds} bedroom(s)")
        if intent.min_baths:
            must_have.append(f"at least {intent.min_baths} bathroom(s)")
        if intent.min_sqft:
            must_have.append(f"at least {intent.min_sqft} sq ft")
        if intent.garage_required:
            must_have.append("with parking/garage")
        if intent.property_type:
            must_have.append(f"preferably a {intent.property_type}")
        
        # Soft Preferences (Nice to Have)
        if intent.good_schools:
            nice_to_have.append("good schools nearby")
        if intent.yard:
            nice_to_have.append("with yard/garden")
        if intent.family_friendly:
            nice_to_have.append("family-friendly")
        if intent.walk_to_metro:
            nice_to_have.append("near public transit")
        if intent.modern:
            nice_to_have.append("modern/contemporary")
        if intent.renovated:
            nice_to_have.append("recently renovated")
        if intent.ocean_view:
            nice_to_have.append("ocean view")
        if intent.mountain_view:
            nice_to_have.append("mountain view")
        if intent.quiet:
            nice_to_have.append("quiet neighborhood")
        if intent.featured:
            nice_to_have.append("featured/premium")
        if intent.near_grocery:
            nice_to_have.append("near grocery stores")
        if intent.near_shopping:
            nice_to_have.append("near shopping")
        if intent.safe_area:
            nice_to_have.append("safe area")
        if intent.walkable:
            nice_to_have.append("walkable neighborhood")
        if intent.dining_options:
            nice_to_have.append("dining options nearby")
        if intent.short_term_rental:
            nice_to_have.append("short-term rental")
        if intent.pet_friendly:
            nice_to_have.append("pet-friendly")
        
        # Generate the enhanced response
        if not must_have and not nice_to_have:
            return "No specific requirements specified"
        
        result = "Here is what you are looking for:\n"
        
        if must_have:
            result += "must have:\n"
            for req in must_have:
                result += f"• {req}\n"
        
        if nice_to_have:
            if must_have:
                result += "\n"
            result += "nice to have:\n"
            for req in nice_to_have:
                result += f"• {req}\n"
        
        return result.strip()
    
    async def _perform_search(self, query: str, intent: SearchIntent, limit: int) -> Tuple[List[Dict[str, Any]], bool]:
        """Perform the actual search. Returns (results, used_fallback)"""
        try:
            # Step 1: Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Step 2: Build filter conditions
            where_clause, params = self._build_filter_conditions(intent)
            
            # Step 3: Get candidates
            candidates = await self._get_candidates(where_clause, params)
        
        except Exception as e:
            logger.error(f"Error in _perform_search: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error args: {e.args}")
            raise Exception(f"Search failed: {str(e)}")
        
        # Step 4: Smart Vector Search with Fallback
        used_fallback = False
        if candidates:
            # Use filtered candidate pool (efficient)
            candidate_ids = [c['id'] for c in candidates]
            logger.info(f"Using structured filtering with {len(candidates)} candidates")
            try:
                vector_results = await self.db_manager.vector_search(query_embedding, candidate_ids, top_k=200)
                logger.info(f"Vector search on filtered candidates returned {len(vector_results)} results")
            except Exception as e:
                logger.error(f"Error in vector search on filtered candidates: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error args: {e.args}")
                raise Exception(f"Vector search failed: {str(e)}")
        else:
            # Fallback: semantic search on entire database (comprehensive)
            used_fallback = True
            logger.info("No candidates from structured filtering, falling back to full semantic search")
            try:
                vector_results = await self.db_manager.vector_search(query_embedding, [], top_k=200)
                logger.info(f"Full semantic search returned {len(vector_results)} results")
            except Exception as e:
                logger.error(f"Error in full semantic search: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error args: {e.args}")
                raise Exception(f"Full semantic search failed: {str(e)}")
        
        # Step 5: Score and rank
        scored_results = []
        logger.info(f"Starting to score {len(vector_results)} listings")
        
        for i, listing in enumerate(vector_results):
            try:
                logger.debug(f"Scoring listing {i+1}/{len(vector_results)}: {listing.get('id', 'unknown')}")
                score_details = self.scoring_engine.calculate_score_with_details(listing, intent)
                listing['final_score'] = score_details['final_score']
                listing['score_details'] = score_details
                scored_results.append(listing)
            except Exception as e:
                logger.error(f"Error scoring listing {listing.get('id', 'unknown')}: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error args: {e.args}")
                logger.error(f"Listing keys: {list(listing.keys()) if listing else 'None'}")
                logger.error(f"Intent property_type: {getattr(intent, 'property_type', 'Not found')}")
                # Skip this listing and continue
                continue
        
        # Step 6: Sort and limit
        scored_results.sort(key=lambda x: x['final_score'], reverse=True)
        return scored_results[:limit], used_fallback
    
    def _build_filter_conditions(self, intent: SearchIntent) -> Tuple[str, List[Any]]:
        """Build SQL WHERE conditions"""
        conditions = ["embedding IS NOT NULL"]
        params = []
        param_count = 1
        
        if intent.city:
            conditions.append(f"LOWER(city) = ${param_count}")
            params.append(intent.city.lower())
            param_count += 1
        
        if intent.state:
            conditions.append(f"LOWER(state) = ${param_count}")
            params.append(intent.state.lower())
            param_count += 1
        
        if intent.max_price_sale:
            conditions.append(f"price_for_sale <= ${param_count}")
            params.append(intent.max_price_sale)
            param_count += 1
        
        if intent.max_price_rent:
            conditions.append(f"price_per_month <= ${param_count}")
            params.append(intent.max_price_rent)
            param_count += 1
        
        if intent.min_beds:
            conditions.append(f"bedrooms >= ${param_count}")
            params.append(intent.min_beds)
            param_count += 1
        
        if intent.min_baths:
            conditions.append(f"bathrooms >= ${param_count}")
            params.append(intent.min_baths)
            param_count += 1
        
        if intent.garage_required:
            conditions.append("(garage_number > 0 OR has_parking_lot = true)")
        
        if intent.property_type:
            conditions.append(f"LOWER(property_type) = ${param_count}")
            params.append(intent.property_type.lower())
            param_count += 1
        
        where_clause = " AND ".join(conditions)
        return where_clause, params
    
    async def _get_candidates(self, where_clause: str, params: List[Any]) -> List[Dict[str, Any]]:
        """Get candidate listings from database"""
        query = f"""
        SELECT 
            id, title, address, bedrooms, bathrooms, square_feet,
            garage_number, has_parking_lot, property_type,
            price_for_sale, price_per_month,
            has_yard, school_rating, crime_index, facing,
            shopping_idx, grocery_idx, tags, embedding_text,
            city, state, country, neighborhood,
            description, amenities, host_id, is_available, is_featured,
            latitude, longitude, rating, review_count,
            property_listing_type, year_built, year_renovated,
            created_at, updated_at,
            CASE 
                WHEN property_listing_type = 'sale' THEN price_for_sale
                WHEN property_listing_type = 'both' THEN price_per_month
                WHEN property_listing_type = 'rent' THEN price_per_month
                ELSE COALESCE(price_per_month, price_for_sale)
            END as price,
            images
        FROM listings_v2 
        WHERE {where_clause}
        LIMIT 10000
        """
        
        return await self.db_manager.execute_query(query, *params)
    
    async def _generate_reasons(self, query: str, results: List[Dict[str, Any]], intent: SearchIntent):
        """Generate reasons for search results"""
        try:
            # Simple template-based reasons for now
            for listing in results:
                listing['reason'] = self._generate_simple_reason(listing, intent)
        except Exception as e:
            logger.warning(f"Reason generation failed: {e}")
    
    def _generate_simple_reason(self, listing: Dict[str, Any], intent: SearchIntent) -> str:
        """Generate a detailed reason for the match using score details"""
        if 'score_details' not in listing:
            # Fallback to simple reason if no score details available
            reasons = []
            
            bedrooms = listing.get('bedrooms')
            if intent.min_beds and bedrooms is not None and bedrooms >= intent.min_beds:
                reasons.append(f"{bedrooms} bedrooms")
            
            price = listing.get('price_for_sale')
            if intent.max_price_sale and price is not None and price <= intent.max_price_sale:
                reasons.append(f"under ${intent.max_price_sale:,.0f}")
            
            city = listing.get('city')
            if intent.city and city and city.lower() == intent.city.lower():
                reasons.append(f"in {intent.city}")
            
            if reasons:
                return f"Matches your search: {', '.join(reasons)}"
            else:
                return "Recommended based on semantic similarity"
        
        # Use detailed score information
        score_details = listing['score_details']
        matches = score_details['matches']
        
        reason_parts = []
        
        # Structured matches
        if matches['structured']:
            reason_parts.append("Matches your requirements: " + ", ".join(matches['structured']))
        
        # Semantic matches
        if matches['semantic']:
            reason_parts.append("Semantic matches: " + ", ".join(matches['semantic']))
        
        # Soft preferences
        if matches['soft_preferences']:
            reason_parts.append("Bonus features: " + ", ".join(matches['soft_preferences']))
        
        # Missing requirements (show if there are any, but limit to 2)
        if matches['missing']:
            reason_parts.append("Note: " + ", ".join(matches['missing'][:2]))  # Limit to 2 missing items
        
        if reason_parts:
            return " | ".join(reason_parts)
        else:
            return "Recommended based on semantic similarity"
    
    def _convert_to_listing_results(self, results: List[Dict[str, Any]]) -> List[ListingResult]:
        """Convert search results to ListingResult objects"""
        items = []
        for listing in results:
            # Handle data type conversions
            images_data = listing.get("images")
            if isinstance(images_data, str):
                try:
                    images_data = json.loads(images_data)
                except:
                    images_data = []
            elif not isinstance(images_data, list):
                images_data = []
            
            # Get score details if available
            score_details = listing.get("score_details", {})
            score_breakdown = None
            match_details = None
            
            if score_details:
                score_breakdown = {
                    "final_score": score_details.get("final_score", 0.0),
                    "similarity_score": score_details.get("similarity_score", 0.0),
                    "match_percent": score_details.get("match_percent", 0.0),
                    "soft_preference_bonus": score_details.get("soft_preference_bonus", 0.0)
                }
                match_details = score_details.get("matches", {})
            
            item = ListingResult(
                id=str(listing["id"]),
                title=listing.get("title"),
                address=listing.get("address"),
                bedrooms=listing.get("bedrooms"),
                bathrooms=listing.get("bathrooms"),
                square_feet=listing.get("square_feet"),
                garage_number=listing.get("garage_number"),
                price=listing.get("price"),
                images=images_data,
                city=listing.get("city"),
                state=listing.get("state"),
                country=listing.get("country"),
                neighborhood=listing.get("neighborhood"),
                description=listing.get("description"),
                amenities=listing.get("amenities"),
                host_id=str(listing.get("host_id")) if listing.get("host_id") else None,
                is_available=listing.get("is_available"),
                is_featured=listing.get("is_featured"),
                latitude=listing.get("latitude"),
                longitude=listing.get("longitude"),
                rating=listing.get("rating"),
                review_count=listing.get("review_count"),
                property_listing_type=listing.get("property_listing_type"),
                year_built=listing.get("year_built"),
                year_renovated=listing.get("year_renovated"),
                created_at=str(listing.get("created_at")) if listing.get("created_at") else None,
                updated_at=str(listing.get("updated_at")) if listing.get("updated_at") else None,
                similarity_score=listing.get("final_score", 0.0),
                reason=listing.get("reason", ""),
                score_breakdown=score_breakdown,
                match_details=match_details
            )
            items.append(item)
        
        return items
    
    def _create_empty_response(self, query: str, limit: int, what_you_need: str) -> SearchResponse:
        """Create empty response when no results found"""
        no_results_item = ListingResult(
            id="no_results",
            title="No matching properties found",
            address="",
            bedrooms=None,
            bathrooms=None,
            square_feet=None,
            garage_number=None,
            price=None,
            images=None,
            city=None,
            state=None,
            country=None,
            neighborhood=None,
            description=None,
            amenities=None,
            host_id=None,
            is_available=None,
            is_featured=None,
            latitude=None,
            longitude=None,
            rating=None,
            review_count=None,
            property_listing_type=None,
            year_built=None,
            year_renovated=None,
            created_at=None,
            updated_at=None,
            similarity_score=0.0,
            reason="No properties found matching your requirements. Try adjusting your criteria or expanding your search area."
        )
        
        return SearchResponse(
            items=[no_results_item],
            query=query,
            page=1,
            limit=limit,
            has_more=False,
            generation_error=False,
            what_you_need=what_you_need
        )
