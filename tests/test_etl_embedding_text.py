#!/usr/bin/env python3
"""
Unit tests for ETL #2: Embedding Text Generation
"""

import unittest
import sys
import os
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from etl.embedding_text import EmbeddingTextETL

class TestEmbeddingTextETL(unittest.TestCase):
    """Test cases for EmbeddingTextETL"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.etl = EmbeddingTextETL()
    
    def test_extract_text_cues_south_facing(self):
        """Test extraction of south-facing cue"""
        title = "Beautiful South-Facing Apartment"
        description = "This apartment features a south-facing living room"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('south_facing', cues)
    
    def test_extract_text_cues_good_light(self):
        """Test extraction of good light cues"""
        title = "Bright Apartment with Natural Light"
        description = "Floor-to-ceiling windows provide abundant natural light"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('good_light', cues)
    
    def test_extract_text_cues_walk_to_transit(self):
        """Test extraction of walk to transit cues"""
        title = "Convenient Location"
        description = "Just steps to the metro station and walking distance to BART"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('walk_to_transit', cues)
    
    def test_extract_text_cues_renovated_recent(self):
        """Test extraction of renovated recent cues"""
        title = "Recently Renovated Apartment"
        description = "Newly renovated in 2021 with updated kitchen"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('renovated_recent', cues)
    
    def test_extract_text_cues_balcony(self):
        """Test extraction of balcony cues"""
        title = "Apartment with Balcony"
        description = "Features a private balcony and terrace"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('balcony', cues)
    
    def test_extract_text_cues_parking_available(self):
        """Test extraction of parking cues"""
        title = "Apartment with Parking"
        description = "Includes assigned parking and garage space"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('parking_available', cues)
    
    def test_extract_text_cues_pet_friendly(self):
        """Test extraction of pet friendly cues"""
        title = "Pet Friendly Apartment"
        description = "Dogs and cats are welcome"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('pet_friendly', cues)
    
    def test_extract_text_cues_luxury_property(self):
        """Test extraction of luxury property cues"""
        title = "Luxury Penthouse"
        description = "High-end penthouse with premium amenities"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('luxury_property', cues)
    
    def test_extract_text_cues_negative_keywords(self):
        """Test extraction of negative cues"""
        title = "Apartment Available"
        description = "No parking available, street parking only"
        
        cues = self.etl.extract_text_cues(title, description)
        
        self.assertIn('no_parking', cues)
    
    def test_build_embedding_text_basic(self):
        """Test basic embedding text building"""
        listing = {
            'title': 'Beautiful 2-Bedroom Apartment',
            'description': 'This stunning apartment features modern amenities',
            'property_type': 'Apartment',
            'bedrooms': 2,
            'bathrooms': 2,
            'city': 'San Francisco',
            'state': 'CA',
            'neighborhood': 'Downtown',
            'amenities': ['WiFi', 'Kitchen', 'Parking']
        }
        
        cues = ['south_facing', 'good_light', 'walk_to_transit']
        
        embedding_text = self.etl.build_embedding_text(listing, cues)
        
        # Should contain all expected parts
        self.assertIn('TITLE:', embedding_text)
        self.assertIn('FACTS:', embedding_text)
        self.assertIn('TAGS:', embedding_text)
        self.assertIn('DESCRIPTION:', embedding_text)
        
        # Should contain specific content
        self.assertIn('Apartment with 2 bedrooms and 2 bathrooms', embedding_text)
        self.assertIn('Located in San Francisco, CA', embedding_text)
        self.assertIn('Neighborhood: Downtown', embedding_text)
        self.assertIn('Amenities: WiFi, Kitchen, Parking', embedding_text)
        self.assertIn('south_facing, good_light, walk_to_transit', embedding_text)
    
    def test_build_embedding_text_length_limit(self):
        """Test embedding text length limiting"""
        # Create a very long description
        long_description = "This is a very long description. " * 50  # ~1000 characters
        
        listing = {
            'title': 'Test Apartment',
            'description': long_description,
            'property_type': 'Apartment',
            'bedrooms': 1,
            'bathrooms': 1,
            'city': 'Test City',
            'state': 'CA'
        }
        
        cues = ['test_cue']
        
        embedding_text = self.etl.build_embedding_text(listing, cues)
        
        # Should be limited to 500 characters
        self.assertLessEqual(len(embedding_text), 500)
        self.assertIn('...', embedding_text)  # Should be truncated
    
    def test_build_embedding_text_no_cues(self):
        """Test embedding text building with no cues"""
        listing = {
            'title': 'Simple Apartment',
            'description': 'Basic apartment description',
            'property_type': 'Apartment',
            'bedrooms': 1,
            'bathrooms': 1,
            'city': 'Test City',
            'state': 'CA'
        }
        
        cues = []
        
        embedding_text = self.etl.build_embedding_text(listing, cues)
        
        # Should still build text without cues
        self.assertIn('TITLE:', embedding_text)
        self.assertIn('FACTS:', embedding_text)
        self.assertIn('DESCRIPTION:', embedding_text)
        self.assertNotIn('TAGS:', embedding_text)  # No tags section
    
    def test_process_listing_complete(self):
        """Test complete listing processing"""
        listing = {
            'title': 'Beautiful South-Facing Apartment with Balcony',
            'description': 'This stunning apartment features a south-facing living room with floor-to-ceiling windows providing abundant natural light. Recently renovated in 2021 with a modern kitchen and updated appliances. Located just steps to the metro station and within walking distance to excellent schools. The property includes a private balcony, assigned parking, and is pet-friendly.',
            'property_type': 'Apartment',
            'bedrooms': 2,
            'bathrooms': 2,
            'city': 'San Francisco',
            'state': 'CA',
            'neighborhood': 'Downtown',
            'amenities': ['WiFi', 'Balcony', 'Parking', 'Pet Friendly']
        }
        
        embedding_text = self.etl.process_listing(listing)
        
        # Should extract multiple cues
        self.assertIn('south_facing', embedding_text)
        self.assertIn('good_light', embedding_text)
        self.assertIn('walk_to_transit', embedding_text)
        self.assertIn('renovated_recent', embedding_text)
        self.assertIn('balcony', embedding_text)
        self.assertIn('parking_available', embedding_text)
        self.assertIn('pet_friendly', embedding_text)
        
        # Should be properly formatted
        self.assertIn('TITLE:', embedding_text)
        self.assertIn('FACTS:', embedding_text)
        self.assertIn('TAGS:', embedding_text)
        self.assertIn('DESCRIPTION:', embedding_text)
        
        # Should be within length limits
        self.assertLessEqual(len(embedding_text), 500)
    
    def test_context_rules_year_extraction(self):
        """Test context rules for year extraction"""
        title = "Renovated Apartment"
        description = "This apartment was renovated in 2022 with modern fixtures"
        
        cues = self.etl.extract_text_cues(title, description)
        
        # Should extract renovated_recent due to year 2022
        self.assertIn('renovated_recent', cues)
    
    def test_context_rules_distance_extraction(self):
        """Test context rules for distance extraction"""
        title = "Convenient Location"
        description = "Just 3 blocks to the subway station"
        
        cues = self.etl.extract_text_cues(title, description)
        
        # Should extract walk_to_transit due to 3 blocks
        self.assertIn('walk_to_transit', cues)

if __name__ == '__main__':
    unittest.main()
