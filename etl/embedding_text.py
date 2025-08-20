#!/usr/bin/env python3
"""
ETL #2: Embedding Text Generation
Build embedding_text from prose (title/description) using semantic cue extraction
"""

import yaml
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingTextETL:
    """ETL for generating embedding_text from title and description"""
    
    def __init__(self, config_path: str = "config/text_extraction_keywords.yaml"):
        """Initialize with configuration file"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.positive_keywords = self.config.get('positive_keywords', {})
        self.negative_keywords = self.config.get('negative_keywords', {})
        self.context_rules = self.config.get('context_rules', [])
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}
    
    def extract_text_cues(self, title: str, description: str) -> List[str]:
        """Extract semantic cues from title and description"""
        cues = set()
        text = f"{title} {description}".lower()
        
        # Extract positive keywords
        for phrase, cue in self.positive_keywords.items():
            if phrase.lower() in text:
                cues.add(cue)
        
        # Extract negative keywords
        for phrase, cue in self.negative_keywords.items():
            if phrase.lower() in text:
                cues.add(cue)
        
        # Apply context-specific rules
        for rule in self.context_rules:
            pattern = rule.get('pattern', '')
            condition = rule.get('condition', '')
            cue = rule.get('cue', '')
            
            if pattern and cue:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        # Evaluate condition if provided
                        if condition:
                            # Create a simple condition evaluator
                            condition_eval = condition.replace('match.group(1)', f"'{match.group(1)}'")
                            if eval(condition_eval):
                                cues.add(cue)
                        else:
                            cues.add(cue)
                    except Exception as e:
                        logger.warning(f"Error evaluating context rule: {e}")
                        continue
        
        return list(cues)
    
    def build_embedding_text(self, listing: Dict[str, Any], cues: List[str]) -> str:
        """Build embedding_text from listing data and extracted cues"""
        parts = []
        
        # Optional: Add title (first 50 chars)
        title = listing.get('title', '').strip()
        if title:
            title_short = title[:50] + "..." if len(title) > 50 else title
            parts.append(f"TITLE: {title_short}")
        
        # Optional: Add top 2-4 facts (non-numeric phrasing only)
        facts = []
        
        # Property type and basic info
        property_type = listing.get('property_type', '')
        bedrooms = listing.get('bedrooms', 0)
        bathrooms = listing.get('bathrooms', 0)
        city = listing.get('city', '')
        state = listing.get('state', '')
        
        if property_type and bedrooms and bathrooms:
            facts.append(f"{property_type} with {bedrooms} bedrooms and {bathrooms} bathrooms")
        
        if city and state:
            facts.append(f"Located in {city}, {state}")
        
        # Add neighborhood if available
        neighborhood = listing.get('neighborhood', '')
        if neighborhood:
            facts.append(f"Neighborhood: {neighborhood}")
        
        # Add amenities (top 3)
        amenities = listing.get('amenities', [])
        if amenities:
            top_amenities = amenities[:3]
            facts.append(f"Amenities: {', '.join(top_amenities)}")
        
        # Limit facts to 4
        facts = facts[:4]
        if facts:
            parts.append("FACTS: " + "; ".join(facts))
        
        # Add TAGS/CUES line
        if cues:
            parts.append("TAGS: " + ", ".join(cues))
        
        # Add compact description (first ~120-160 words)
        description = listing.get('description', '').strip()
        if description:
            # Split into words and take first 150 words
            words = description.split()
            if len(words) > 150:
                description_short = " ".join(words[:150]) + "..."
            else:
                description_short = description
            
            parts.append(f"DESCRIPTION: {description_short}")
        
        # Join all parts and limit total length
        embedding_text = " | ".join(parts)
        
        # Ensure it's not too long (max 500 characters for embedding efficiency)
        if len(embedding_text) > 500:
            embedding_text = embedding_text[:497] + "..."
        
        return embedding_text
    
    def process_listing(self, listing: Dict[str, Any]) -> str:
        """Process a single listing to generate embedding_text"""
        title = listing.get('title', '')
        description = listing.get('description', '')
        
        # Extract cues from text
        cues = self.extract_text_cues(title, description)
        
        # Build embedding text
        embedding_text = self.build_embedding_text(listing, cues)
        
        return embedding_text

def main():
    """Test the ETL with sample data"""
    etl = EmbeddingTextETL()
    
    # Sample listing data
    sample_listing = {
        'title': 'Beautiful South-Facing Apartment with Balcony',
        'description': 'This stunning apartment features a south-facing living room with floor-to-ceiling windows providing abundant natural light. Recently renovated in 2021 with a modern kitchen and updated appliances. Located just steps to the metro station and within walking distance to excellent schools. The property includes a private balcony, assigned parking, and is pet-friendly. The neighborhood is known for its safety and convenience to shopping and grocery stores.',
        'property_type': 'Apartment',
        'bedrooms': 2,
        'bathrooms': 2,
        'city': 'San Francisco',
        'state': 'CA',
        'neighborhood': 'Downtown',
        'amenities': ['WiFi', 'Balcony', 'Parking', 'Pet Friendly', 'Modern Kitchen']
    }
    
    # Process listing
    embedding_text = etl.process_listing(sample_listing)
    
    print("Sample embedding text:")
    print(embedding_text)
    print(f"\nLength: {len(embedding_text)} characters")

if __name__ == "__main__":
    main()
