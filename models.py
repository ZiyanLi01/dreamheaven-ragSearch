"""
Pydantic models for DreamHeaven RAG API
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language description of dream home")
    limit: Optional[int] = Field(10, description="Number of results to return (default: 10)")
    offset: Optional[int] = Field(0, description="Number of results to skip for pagination (default: 0)")
    reasons: Optional[bool] = Field(True, description="Whether to generate reasons for matches (default: True)")
    
    # Structured filter parameters (when "apply filter" is checked)
    city: Optional[str] = Field(None, description="City filter")
    state: Optional[str] = Field(None, description="State filter")
    property_type: Optional[str] = Field(None, description="Property type (sale/rent)")
    min_bedrooms: Optional[int] = Field(None, description="Minimum number of bedrooms")
    max_bedrooms: Optional[int] = Field(None, description="Maximum number of bedrooms")
    min_bathrooms: Optional[int] = Field(None, description="Minimum number of bathrooms")
    max_bathrooms: Optional[int] = Field(None, description="Maximum number of bathrooms")
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    sort_by: Optional[str] = Field(None, description="Sort field (price, bedrooms, etc.)")
    sort_order: Optional[str] = Field(None, description="Sort order (asc, desc)")
    
    def get_structured_filters(self) -> dict:
        """Get structured filters as a dictionary"""
        return {
            'city': self.city,
            'state': self.state,
            'property_type': self.property_type,
            'min_bedrooms': self.min_bedrooms,
            'max_bedrooms': self.max_bedrooms,
            'min_bathrooms': self.min_bathrooms,
            'max_bathrooms': self.max_bathrooms,
            'min_price': self.min_price,
            'max_price': self.max_price,
            'sort_by': self.sort_by,
            'sort_order': self.sort_order
        }


class ListingResult(BaseModel):
    id: str
    title: Optional[str] = None
    address: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    square_feet: Optional[int] = None
    garage_number: Optional[int] = None
    price: Optional[float] = None
    images: Optional[List[str]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    neighborhood: Optional[str] = None
    description: Optional[str] = None
    amenities: Optional[List[str]] = None
    host_id: Optional[str] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    property_listing_type: Optional[str] = None
    year_built: Optional[int] = None
    year_renovated: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    similarity_score: float = Field(..., description="Final reranking score (0-1)")
    reason: Optional[str] = Field("", description="Generated reason for match")
    score_breakdown: Optional[dict] = Field(None, description="Detailed score breakdown")
    match_details: Optional[dict] = Field(None, description="Detailed match information")


class SearchResponse(BaseModel):
    items: List[ListingResult]
    query: str
    page: int
    limit: int
    has_more: bool
    generation_error: Optional[bool] = Field(False, description="Whether generation failed")
    what_you_need: Optional[str] = Field(None, description="User-friendly description of search requirements")
