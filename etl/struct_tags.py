#!/usr/bin/env python3
"""
ETL #1: Structured Tags Generation
Generate tags from structured listing fields using rule-based configuration
"""

import yaml
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TagHit:
    """Represents a tag match with evidence"""
    tag: str
    evidence: str
    source: str = "structured"
    rule_name: str = ""
    rule_version: str = ""

class StructuredTagsETL:
    """ETL for generating tags from structured listing fields"""
    
    def __init__(self, config_path: str = "config/tags_struct_rules.yaml"):
        """Initialize with configuration file"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.thresholds = self.config.get('thresholds', {})
        self.rules = self.config.get('rules', [])
        self.rule_version = self.config.get('rule_version', '1.0.0')
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}
    
    def normalize_facing(self, facing: Optional[str]) -> Optional[str]:
        """Normalize facing direction to enum values"""
        if not facing:
            return None
        
        # Convert to uppercase and validate
        facing = facing.upper()
        valid_facings = {'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}
        
        return facing if facing in valid_facings else None
    
    def normalize_distance(self, distance: Optional[float]) -> Optional[float]:
        """Normalize distance to meters"""
        if distance is None:
            return None
        return float(distance)
    
    def normalize_boolean(self, value: Any) -> bool:
        """Normalize boolean values"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {'true', '1', 'yes', 'on'}
        if isinstance(value, (int, float)):
            return bool(value)
        return False
    
    def normalize_year(self, year: Optional[int]) -> Optional[int]:
        """Normalize year values"""
        if year is None:
            return None
        year = int(year)
        # Basic validation: reasonable year range
        if 1900 <= year <= 2030:
            return year
        return None
    
    def evaluate_condition(self, condition: str, listing: Dict[str, Any]) -> bool:
        """Evaluate a condition string against listing data"""
        try:
            # Create a safe evaluation context with defaults for missing fields
            context = {
                'facing': self.normalize_facing(listing.get('facing')),
                'distance_to_metro_m': self.normalize_distance(listing.get('distance_to_metro_m')),
                'has_parking_lot': self.normalize_boolean(listing.get('has_parking_lot')),
                'garage_number': listing.get('garage_number', 0),
                'year_renovated': self.normalize_year(listing.get('year_renovated')),
                'school_rating': listing.get('school_rating'),
                'crime_index': listing.get('crime_index'),
                'has_yard': self.normalize_boolean(listing.get('has_yard')),
                'shopping_idx': listing.get('shopping_idx'),
                'grocery_idx': listing.get('grocery_idx'),
                'property_type': listing.get('property_type'),
                'square_feet': listing.get('square_feet'),
                'bedrooms': listing.get('bedrooms'),
                'bathrooms': listing.get('bathrooms'),
            }
            
            # Handle OR conditions first
            if " OR " in condition:
                parts = condition.split(" OR ")
                return any(self.evaluate_condition(part.strip(), listing) for part in parts)
            
            # Handle AND conditions
            if " AND " in condition:
                parts = condition.split(" AND ")
                return all(self.evaluate_condition(part.strip(), listing) for part in parts)
            
            # Handle individual conditions
            condition_eval = condition.strip()
            
            # Handle string equality
            if " == '" in condition_eval:
                # Extract field and value
                field_part = condition_eval.split(" == '")[0].strip()
                value_part = condition_eval.split(" == '")[1].split("'")[0]
                field_value = context.get(field_part)
                return field_value == value_part
            
            # Handle numeric comparisons
            for op in ['<=', '>=', '>', '<', '==']:
                if op in condition_eval:
                    field_part = condition_eval.split(op)[0].strip()
                    value_part = condition_eval.split(op)[1].strip()
                    field_value = context.get(field_part)
                    
                    # Skip if field is None
                    if field_value is None:
                        return False
                    
                    try:
                        if op == '<=':
                            return field_value <= float(value_part)
                        elif op == '>=':
                            return field_value >= float(value_part)
                        elif op == '>':
                            return field_value > float(value_part)
                        elif op == '<':
                            return field_value < float(value_part)
                        elif op == '==':
                            return field_value == float(value_part)
                    except (ValueError, TypeError):
                        # If value_part is not a number, try string comparison
                        return field_value == value_part
            
            # Handle boolean comparisons
            if " == true" in condition_eval:
                field_part = condition_eval.split(" == true")[0].strip()
                field_value = context.get(field_part)
                return field_value is True
            elif " == false" in condition_eval:
                field_part = condition_eval.split(" == false")[0].strip()
                field_value = context.get(field_part)
                return field_value is False
            
            # Handle list membership (e.g., "property_type in ['Penthouse', 'Villa']")
            if " in [" in condition_eval:
                field_part = condition_eval.split(" in [")[0].strip()
                values_part = condition_eval.split(" in [")[1].split("]")[0]
                field_value = context.get(field_part)
                
                # Parse the list of values
                values = [v.strip().strip("'") for v in values_part.split(",")]
                return field_value in values
            
            return False
            
        except Exception as e:
            logger.warning(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def format_evidence(self, template: str, listing: Dict[str, Any]) -> str:
        """Format evidence using template and listing data"""
        try:
            return template.format(**listing)
        except Exception as e:
            logger.warning(f"Error formatting evidence template '{template}': {e}")
            return template
    
    def extract_struct_tags(self, listing: Dict[str, Any]) -> List[TagHit]:
        """Extract structured tags from listing data"""
        tag_hits = []
        
        for rule in self.rules:
            try:
                condition = rule.get('condition', '')
                if not condition:
                    continue
                
                # Evaluate the condition
                if self.evaluate_condition(condition, listing):
                    tag = rule.get('tag', '')
                    evidence_template = rule.get('evidence_template', '')
                    rule_name = rule.get('name', '')
                    
                    if tag:
                        evidence = self.format_evidence(evidence_template, listing)
                        tag_hit = TagHit(
                            tag=tag,
                            evidence=evidence,
                            source="structured",
                            rule_name=rule_name,
                            rule_version=self.rule_version
                        )
                        tag_hits.append(tag_hit)
                        
            except Exception as e:
                logger.warning(f"Error processing rule {rule.get('name', 'unknown')}: {e}")
                continue
        
        return tag_hits
    
    def get_tag_names(self, tag_hits: List[TagHit]) -> List[str]:
        """Extract just the tag names from TagHit objects"""
        return [hit.tag for hit in tag_hits]
    
    def get_tag_objects(self, tag_hits: List[TagHit]) -> List[Dict[str, Any]]:
        """Convert TagHit objects to dictionary format for JSONB storage"""
        return [
            {
                'tag': hit.tag,
                'evidence': hit.evidence,
                'source': hit.source,
                'rule_name': hit.rule_name,
                'rule_version': hit.rule_version
            }
            for hit in tag_hits
        ]

def main():
    """Test the ETL with sample data"""
    etl = StructuredTagsETL()
    
    # Sample listing data
    sample_listing = {
        'facing': 'S',
        'distance_to_metro_m': 500,
        'has_parking_lot': True,
        'garage_number': 1,
        'year_renovated': 2021,
        'school_rating': 9,
        'crime_index': 0.2,
        'has_yard': True,
        'shopping_idx': 85,
        'grocery_idx': 90,
        'property_type': 'Penthouse',
        'square_feet': 2500,
        'bedrooms': 3,
        'bathrooms': 2
    }
    
    # Extract tags
    tag_hits = etl.extract_struct_tags(sample_listing)
    
    print("Sample listing tags:")
    for hit in tag_hits:
        print(f"  {hit.tag}: {hit.evidence}")

if __name__ == "__main__":
    main()
