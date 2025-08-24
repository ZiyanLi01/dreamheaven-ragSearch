"""
Intent extraction module for DreamHeaven RAG API
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchIntent:
    """Search intent extracted from natural language query"""
    # Hard filters
    city: Optional[str] = None
    state: Optional[str] = None
    neighborhood: Optional[str] = None
    max_price_sale: Optional[float] = None
    max_price_rent: Optional[float] = None
    min_beds: Optional[int] = None
    min_baths: Optional[int] = None
    min_sqft: Optional[int] = None
    garage_required: bool = False
    property_type: Optional[str] = None
    listing_type: Optional[str] = None  # 'rent', 'sale', or None
    
    # Soft preferences (for reranking)
    good_schools: bool = False
    parking: bool = False
    yard: bool = False
    walk_to_metro: bool = False
    modern: bool = False
    renovated: bool = False
    ocean_view: bool = False
    mountain_view: bool = False
    quiet: bool = False
    family_friendly: bool = False
    featured: bool = False
    near_grocery: bool = False
    near_shopping: bool = False
    safe_area: bool = False
    walkable: bool = False
    dining_options: bool = False
    short_term_rental: bool = False
    pet_friendly: bool = False


class IntentExtractor:
    """Extract structured search intent from natural language queries"""
    
    def __init__(self):
        # Intent extraction patterns
        self.intent_patterns = {
            # Cities and states
            'city_state': [
                r'\b(san francisco|sf|new york|nyc|los angeles|la|chicago|miami|seattle|boston|austin|denver|portland|atlanta|phoenix|las vegas|houston|dallas|philadelphia|washington dc|dc)\b',
                r'\b(california|ca|new york|ny|texas|tx|florida|fl|illinois|il|washington|wa|massachusetts|ma|colorado|co|oregon|or|georgia|ga|arizona|az|nevada|nv|pennsylvania|pa|virginia|va)\b'
            ],
            
            # Neighborhoods
            'neighborhood': [
                r'\b(nob hill|mission district|marina|pacific heights|russian hill|presidio heights|hayes valley|soma|financial district|castro|noe valley|bernal heights|glen park|inner sunset|outer sunset|richmond|sunset|twin peaks|downtown|uptown|midtown|west village|east village|chelsea|soho|tribeca|brooklyn heights|williamsburg|park slope|astoria|long island city|queens|manhattan|brooklyn|bronx|staten island)\b'
            ],
            
            # Price ranges
            'price_sale': [
                r'\bunder\s+\$?([0-9,]+(?:k|m)?)\b(?!\s+per\s+month|\s*/\s*month)',
                r'\bless than\s+\$?([0-9,]+(?:k|m)?)\b(?!\s+per\s+month|\s*/\s*month)',
                r'\bmax\s+\$?([0-9,]+(?:k|m)?)\b(?!\s+per\s+month|\s*/\s*month)',
                r'\bup to\s+\$?([0-9,]+(?:k|m)?)\b(?!\s+per\s+month|\s*/\s*month)'
            ],
            'price_rent': [
                r'\brent\s+under\s+\$?([0-9,]+)\b',
                r'\brental\s+max\s+\$?([0-9,]+)\b',
                r'\bunder\s+\$?([0-9,]+)\s+per\s+month\b',
                r'\bunder\s+\$?([0-9,]+)\s*/\s*month\b',
                r'\bmax\s+\$?([0-9,]+)\s+per\s+month\b',
                r'\bmax\s+\$?([0-9,]+)\s*/\s*month\b'
            ],
            
            # Bedrooms and bathrooms
            'beds': [
                r'\b([1-5])\s*(?:bed|bedroom|br)s?\b',
                r'\b([1-5])\s*bed\b',
                r'\b([1-5])-bedroom\b',
                r'\b([1-5])-bed\b',
                r'\b([1-5])\+\s*(?:bed|bedroom|br)s?\b',
                r'\b([1-5])\+\s*bed\b'
            ],
            'baths': [
                r'\b([1-4])\s*(?:bath|bathroom)s?\b',
                r'\b([1-4])\s*bath\b',
                r'\b([1-4])-bath\b',
                r'\b([1-4])-bathroom\b'
            ],
            
            # Square footage
            'sqft': [
                r'\b(?:at least|minimum|with at least)\s+([0-9,]+)\s*(?:sq\s*ft|square\s*feet|square\s*foot)\b',
                r'\b([0-9,]+)\s*(?:sq\s*ft|square\s*feet|square\s*foot)\s*(?:or more|minimum|at least)\b',
                r'\b(?:minimum|at least)\s+([0-9,]+)\s*(?:sq\s*ft|square\s*feet|square\s*foot)\b',
                r'\b([0-9,]+)\+\s*(?:sq\s*ft|square\s*feet|square\s*foot)\b'
            ],
            
            # Property features
            'garage': [
                r'\bgarage\b',
                r'\bparking\b',
                r'\bcar space\b'
            ],
            'property_type': [
                r'\b(condo|apartment|apartments|house|houses|townhouse|townhouses|single family|multi family|duplex|duplexes|loft|lofts|studio|studios)\b'
            ],
            
            # Listing type (rent/sale)
            'listing_type': [
                r'\bfor\s+rent\b',
                r'\brental\b',
                r'\brenting\b',
                r'\bto\s+rent\b',
                r'\bfor\s+sale\b',
                r'\bbuying\b',
                r'\bto\s+buy\b',
                r'\bpurchase\b'
            ],
            
            # Soft preferences
            'good_schools': [
                r'\bgood school\b',
                r'\bexcellent school\b',
                r'\bgreat school\b',
                r'\bhigh rated school\b',
                r'\bgood schools\b',
                r'\bexcellent schools\b',
                r'\bgreat schools\b',
                r'\bhigh rated schools\b'
            ],
            'yard': [
                r'\byard\b',
                r'\bgarden\b',
                r'\bbackyard\b',
                r'\bfront yard\b',
                r'\boutdoor space\b',
                r'\bpatio\b',
                r'\bdeck\b'
            ],
            'walk_to_metro': [
                r'\bwalk to metro\b',
                r'\bwalking distance to transit\b',
                r'\bnear metro\b',
                r'\bclose to subway\b',
                r'\bwalk to train\b',
                r'\bnear bart\b',
                r'\bbart station\b',
                r'\bclose to bart\b'
            ],
            'modern': [
                r'\bmodern\b',
                r'\bcontemporary\b',
                r'\bnew\b',
                r'\bupdated\b'
            ],
            'renovated': [
                r'\brenovated\b',
                r'\bremodeled\b',
                r'\bupdated\b',
                r'\bnewly renovated\b'
            ],
            'ocean_view': [
                r'\bocean view\b',
                r'\bwaterfront\b',
                r'\bsea view\b',
                r'\bwater view\b'
            ],
            'mountain_view': [
                r'\bmountain view\b',
                r'\bhills view\b',
                r'\bscenic view\b'
            ],
            'quiet': [
                r'\bquiet\b',
                r'\bpeaceful\b',
                r'\bcalm\b',
                r'\bno noise\b'
            ],
            'family_friendly': [
                r'\bfamily friendly\b',
                r'\bkid friendly\b',
                r'\bgood for family\b',
                r'\bsafe neighborhood\b',
                r'\bfamily house\b',
                r'\bfamily home\b',
                r'\bfamily property\b'
            ],
            'featured': [
                r'\bfeatured\b',
                r'\bpremium\b',
                r'\bhighlighted\b',
                r'\bspecial\b',
                r'\bexclusive\b'
            ],
            'near_grocery': [
                r'\bclose to grocery\b',
                r'\bnear grocery\b',
                r'\bwalking distance to grocery\b',
                r'\bgrocery stores\b',
                r'\bsupermarket\b'
            ],
            'near_shopping': [
                r'\bclose to shopping\b',
                r'\bnear shopping\b',
                r'\bwalking distance to shopping\b',
                r'\bshopping\b',
                r'\bretail\b',
                r'\bstores\b'
            ],
            'safe_area': [
                r'\bsafe\s+areas?\b',
                r'\bsafe\s+neighborhoods?\b',
                r'\bsafe\s+communities?\b',
                r'\bsecure\s+areas?\b',
                r'\b(?:low|good)\s+crime\s+(?:areas?|neighborhoods?)\b'
            ],
            'walkable': [
                r'\bwalk(?:ing)?\s+(?:distance|to|from)\b',
                r'\bwalkable\b',
                r'\b(?:near|close\s+to)\s+(?:restaurants?|cafes?|shops?|stores?)\b',
                r'\b(?:restaurants?|cafes?|shops?|stores?)\s+(?:nearby|within\s+walking\s+distance)\b'
            ],
            'dining_options': [
                r'\brestaurants?\b',
                r'\bcafes?\b',
                r'\bdining\s+options?\b',
                r'\bfood\s+(?:options?|choices?)\b'
            ],
            'short_term_rental': [
                r'\bshort\s*[-]?\s*term\s+rental\b',
                r'\bshort\s*[-]?\s*term\s+lease\b',
                r'\btemporary\s+rental\b',
                r'\bmonth\s*to\s*month\b',
                r'\bflexible\s+lease\b'
            ],
            'pet_friendly': [
                r'\ballows?\s+pets?\b',
                r'\bpet\s+friendly\b',
                r'\bpets?\s+allowed\b',
                r'\bpets?\s+welcome\b',
                r'\bdog\s+friendly\b',
                r'\bcat\s+friendly\b'
            ]
        }
    
    def extract_intent(self, query: str) -> SearchIntent:
        """Extract structured search intent from natural language query"""
        query_lower = query.lower()
        intent = SearchIntent()
        
        # Extract city/state
        for pattern in self.intent_patterns['city_state']:
            matches = re.findall(pattern, query_lower)
            if matches:
                match = matches[0]
                # Check if it's a state abbreviation
                if match in ['ca', 'ny', 'tx', 'fl', 'il', 'wa', 'ma', 'co', 'or', 'ga', 'az', 'nv', 'pa', 'va']:
                    intent.state = match
                # Check if it's a full state name
                elif match in ['california', 'new york', 'texas', 'florida', 'illinois', 'washington', 'massachusetts', 'colorado', 'oregon', 'georgia', 'arizona', 'nevada', 'pennsylvania', 'virginia']:
                    intent.state = match
                # Otherwise treat as city
                else:
                    intent.city = match
        
        # Extract neighborhood
        for pattern in self.intent_patterns['neighborhood']:
            matches = re.findall(pattern, query_lower)
            if matches:
                intent.neighborhood = matches[0]
                logger.info(f"🔍 Extracted neighborhood: {intent.neighborhood}")
        
        # Extract price ranges - check rent first to avoid conflicts
        for pattern in self.intent_patterns['price_rent']:
            matches = re.findall(pattern, query_lower)
            if matches:
                intent.max_price_rent = float(matches[0].replace(',', ''))
                logger.info(f"🔍 Extracted max_price_rent: {intent.max_price_rent}")
                break
        
        # Only check sale patterns if no rent pattern matched
        if intent.max_price_rent is None:
            for pattern in self.intent_patterns['price_sale']:
                matches = re.findall(pattern, query_lower)
                if matches:
                    price_str = matches[0].replace(',', '')
                    if 'k' in price_str:
                        intent.max_price_sale = float(price_str.replace('k', '')) * 1000
                    elif 'm' in price_str:
                        intent.max_price_sale = float(price_str.replace('m', '')) * 1000000
                    else:
                        intent.max_price_sale = float(price_str)
                    break
        
        # Extract bedrooms/bathrooms
        for pattern in self.intent_patterns['beds']:
            matches = re.findall(pattern, query_lower)
            if matches:
                intent.min_beds = int(matches[0])
        
        for pattern in self.intent_patterns['baths']:
            matches = re.findall(pattern, query_lower)
            if matches:
                intent.min_baths = int(matches[0])
                logger.info(f"🔍 Extracted min_baths: {intent.min_baths}")
        
        # Extract square footage
        for pattern in self.intent_patterns['sqft']:
            matches = re.findall(pattern, query_lower)
            if matches:
                intent.min_sqft = int(matches[0].replace(',', ''))
                logger.info(f"🔍 Extracted min_sqft: {intent.min_sqft}")
                break
        
        # Extract property type
        for pattern in self.intent_patterns['property_type']:
            matches = re.findall(pattern, query_lower)
            if matches:
                property_type = matches[0]
                # Map plural forms to singular forms
                property_type_mapping = {
                    'condos': 'condo',
                    'apartments': 'apartment',
                    'houses': 'house',
                    'townhouses': 'townhouse',
                    'duplexes': 'duplex',
                    'lofts': 'loft',
                    'studios': 'studio'
                }
                intent.property_type = property_type_mapping.get(property_type, property_type)
                logger.info(f"🔍 Extracted property_type: {intent.property_type}")
                break
        
        # Extract listing type (rent/sale)
        for pattern in self.intent_patterns['listing_type']:
            if re.search(pattern, query_lower):
                if any(word in query_lower for word in ['for rent', 'rental', 'renting', 'to rent']):
                    intent.listing_type = 'rent'
                    logger.info(f"🔍 Extracted listing_type: {intent.listing_type}")
                    break
                elif any(word in query_lower for word in ['for sale', 'buying', 'to buy', 'purchase']):
                    intent.listing_type = 'sale'
                    logger.info(f"🔍 Extracted listing_type: {intent.listing_type}")
                    break
        
        # Extract soft preferences
        intent.garage_required = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['garage'])
        intent.good_schools = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['good_schools'])
        intent.yard = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['yard'])
        intent.walk_to_metro = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['walk_to_metro'])
        intent.modern = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['modern'])
        intent.renovated = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['renovated'])
        intent.ocean_view = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['ocean_view'])
        intent.mountain_view = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['mountain_view'])
        intent.quiet = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['quiet'])
        intent.family_friendly = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['family_friendly'])
        intent.featured = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['featured'])
        intent.near_grocery = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['near_grocery'])
        intent.near_shopping = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['near_shopping'])
        intent.safe_area = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['safe_area'])
        intent.walkable = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['walkable'])
        intent.dining_options = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['dining_options'])
        intent.short_term_rental = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['short_term_rental'])
        intent.pet_friendly = any(re.search(pattern, query_lower) for pattern in self.intent_patterns['pet_friendly'])
        
        return intent
