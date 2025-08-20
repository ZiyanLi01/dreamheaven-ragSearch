#!/usr/bin/env python3
"""
Unit tests for ETL #1: Structured Tags Generation
"""

import unittest
import sys
import os
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from etl.struct_tags import StructuredTagsETL, TagHit

class TestStructuredTagsETL(unittest.TestCase):
    """Test cases for StructuredTagsETL"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.etl = StructuredTagsETL()
    
    def test_normalize_facing(self):
        """Test facing direction normalization"""
        # Valid facings
        self.assertEqual(self.etl.normalize_facing('S'), 'S')
        self.assertEqual(self.etl.normalize_facing('n'), 'N')
        self.assertEqual(self.etl.normalize_facing('NE'), 'NE')
        
        # Invalid facings
        self.assertIsNone(self.etl.normalize_facing('X'))
        self.assertIsNone(self.etl.normalize_facing(''))
        self.assertIsNone(self.etl.normalize_facing(None))
    
    def test_normalize_distance(self):
        """Test distance normalization"""
        self.assertEqual(self.etl.normalize_distance(500), 500.0)
        self.assertEqual(self.etl.normalize_distance(500.5), 500.5)
        self.assertIsNone(self.etl.normalize_distance(None))
    
    def test_normalize_boolean(self):
        """Test boolean normalization"""
        # True values
        self.assertTrue(self.etl.normalize_boolean(True))
        self.assertTrue(self.etl.normalize_boolean('true'))
        self.assertTrue(self.etl.normalize_boolean('1'))
        self.assertTrue(self.etl.normalize_boolean(1))
        
        # False values
        self.assertFalse(self.etl.normalize_boolean(False))
        self.assertFalse(self.etl.normalize_boolean('false'))
        self.assertFalse(self.etl.normalize_boolean('0'))
        self.assertFalse(self.etl.normalize_boolean(0))
        self.assertFalse(self.etl.normalize_boolean(None))
    
    def test_normalize_year(self):
        """Test year normalization"""
        # Valid years
        self.assertEqual(self.etl.normalize_year(2020), 2020)
        self.assertEqual(self.etl.normalize_year(1995), 1995)
        
        # Invalid years
        self.assertIsNone(self.etl.normalize_year(1800))  # Too old
        self.assertIsNone(self.etl.normalize_year(2050))  # Too new
        self.assertIsNone(self.etl.normalize_year(None))
    
    def test_extract_struct_tags_south_facing(self):
        """Test extraction of south-facing tag"""
        listing = {
            'facing': 'S',
            'property_type': 'Apartment',
            'bedrooms': 2,
            'bathrooms': 2
        }
        
        tag_hits = self.etl.extract_struct_tags(listing)
        tag_names = self.etl.get_tag_names(tag_hits)
        
        self.assertIn('south_facing', tag_names)
    
    def test_extract_struct_tags_parking(self):
        """Test extraction of parking tag"""
        listing = {
            'has_parking_lot': True,
            'garage_number': 0,
            'property_type': 'Apartment'
        }
        
        tag_hits = self.etl.extract_struct_tags(listing)
        tag_names = self.etl.get_tag_names(tag_hits)
        
        self.assertIn('parking_available', tag_names)
    
    def test_extract_struct_tags_renovated(self):
        """Test extraction of renovated tag"""
        listing = {
            'year_renovated': 2021,
            'property_type': 'Apartment'
        }
        
        tag_hits = self.etl.extract_struct_tags(listing)
        tag_names = self.etl.get_tag_names(tag_hits)
        
        self.assertIn('renovated_recent', tag_names)
    
    def test_extract_struct_tags_good_school(self):
        """Test extraction of good school tag"""
        listing = {
            'school_rating': 9,
            'property_type': 'Apartment'
        }
        
        tag_hits = self.etl.extract_struct_tags(listing)
        tag_names = self.etl.get_tag_names(tag_hits)
        
        self.assertIn('good_school', tag_names)
    
    def test_extract_struct_tags_safe_area(self):
        """Test extraction of safe area tag"""
        listing = {
            'crime_index': 0.2,
            'property_type': 'Apartment'
        }
        
        tag_hits = self.etl.extract_struct_tags(listing)
        tag_names = self.etl.get_tag_names(tag_hits)
        
        self.assertIn('safe_area', tag_names)
    
    def test_extract_struct_tags_luxury_property(self):
        """Test extraction of luxury property tag"""
        listing = {
            'property_type': 'Penthouse',
            'square_feet': 2500,
            'bedrooms': 3,
            'bathrooms': 2
        }
        
        tag_hits = self.etl.extract_struct_tags(listing)
        tag_names = self.etl.get_tag_names(tag_hits)
        
        self.assertIn('luxury_property', tag_names)
    
    def test_threshold_edge_cases(self):
        """Test threshold edge cases"""
        # Test distance threshold edge case
        listing_600m = {
            'distance_to_metro_m': 600,
            'property_type': 'Apartment'
        }
        listing_601m = {
            'distance_to_metro_m': 601,
            'property_type': 'Apartment'
        }
        
        tag_hits_600 = self.etl.extract_struct_tags(listing_600m)
        tag_hits_601 = self.etl.extract_struct_tags(listing_601m)
        
        tag_names_600 = self.etl.get_tag_names(tag_hits_600)
        tag_names_601 = self.etl.get_tag_names(tag_hits_601)
        
        # 600m should get walk_to_metro tag, 601m should not
        self.assertIn('walk_to_metro', tag_names_600)
        self.assertNotIn('walk_to_metro', tag_names_601)
        
        # Test school rating edge case
        listing_rating_8 = {
            'school_rating': 8,
            'property_type': 'Apartment'
        }
        listing_rating_7 = {
            'school_rating': 7,
            'property_type': 'Apartment'
        }
        
        tag_hits_8 = self.etl.extract_struct_tags(listing_rating_8)
        tag_hits_7 = self.etl.extract_struct_tags(listing_rating_7)
        
        tag_names_8 = self.etl.get_tag_names(tag_hits_8)
        tag_names_7 = self.etl.get_tag_names(tag_hits_7)
        
        # Rating 8 should get good_school tag, rating 7 should not
        self.assertIn('good_school', tag_names_8)
        self.assertNotIn('good_school', tag_names_7)
    
    def test_get_tag_objects(self):
        """Test conversion to tag objects"""
        tag_hit = TagHit(
            tag="south_facing",
            evidence="Property faces south",
            source="structured",
            rule_name="south_facing",
            rule_version="1.0.0"
        )
        
        tag_objects = self.etl.get_tag_objects([tag_hit])
        
        self.assertEqual(len(tag_objects), 1)
        self.assertEqual(tag_objects[0]['tag'], 'south_facing')
        self.assertEqual(tag_objects[0]['evidence'], 'Property faces south')
        self.assertEqual(tag_objects[0]['source'], 'structured')

if __name__ == '__main__':
    unittest.main()
