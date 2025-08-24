# Improved House Recommendation Algorithm

## Overview

The improved house recommendation algorithm implements a sophisticated multi-stage approach that combines permanent hard constraints, progressive relaxation, and adaptive scoring to provide more intelligent and user-friendly property recommendations.

## Algorithm Architecture

### Step 1: Intent Extraction
Extracts both **hard constraints** and **soft preferences** from user queries:

#### Hard Constraints (Red Lines)
- **City/State**: Geographic boundaries that cannot be relaxed
- **Price Limits**: When explicitly stated as "cannot exceed" or "must be under"
- **Minimum Bedrooms/Bathrooms**: Essential space requirements
- **Must-have Tags**: Critical features like garage, pet-friendly
- **Negative Constraints**: Explicit exclusions (e.g., "no apartments")

#### Soft Preferences
- **Orientation**: South-facing, sunlight preferences
- **Style**: Modern, renovated properties
- **Location Features**: Near metro, walkability, school quality
- **Amenities**: Yard, grocery proximity, featured status

### Step 2a: Permanent Hard Constraints
- Applies **red line** constraints that must never be relaxed
- Uses strict SQL WHERE clauses for efficient filtering
- If zero results → returns empty result with explanation
- Optional: Provides "Try with relaxed conditions" button

### Step 2b: Progressive Relaxation Strategy
Implements a 3-level relaxation system:

#### Level 1: Slight Relaxation (+10% price, +3km radius)
- Price: +10% increase
- Geographic: +3km radius expansion
- Bedrooms/Bathrooms: No relaxation (preserves core requirements)

#### Level 2: Moderate Relaxation (+20% price, +8km radius)
- Price: +20% increase
- Geographic: +8km radius expansion
- Bedrooms/Bathrooms: -1 with strong penalty

#### Level 3: Significant Relaxation (+35% price, +15km radius)
- Price: +35% increase
- Geographic: +15km radius expansion
- Bedrooms/Bathrooms: -1 with maximum penalty

### Step 3: Adaptive Semantic Search & Reranking

#### Candidate Selection
- Vector search using OpenAI embeddings (1536d) + pgvector
- Top-K candidates (default: 200) by cosine similarity
- Normalized similarity scores using quantile scaling

#### Adaptive Scoring Function
```
final_score = α × match_percent + (1-α) × similarity_score - penalty_relax + soft_preference_bonus
```

Where:
- **α (Adaptive Weight)**: `clamp(0.4 + 0.1 × info_density, 0.4, 0.85)`
  - Higher α when query has many structured conditions
  - Lower α when query is sparse/ambiguous
- **match_percent**: Weighted criteria match (0-1)
- **similarity_score**: Normalized semantic similarity (0-1)
- **penalty_relax**: Progressive penalty for each relaxation level
- **soft_preference_bonus**: +0.03 to +0.08 for matching preferences

#### Match Percentage Calculation
```
match_percent = Σ(w_i × hit_or_proximity_i) / Σ(w_i)
```

Weights:
- Budget: 0.35
- Bedrooms: 0.25
- Bathrooms: 0.15
- Garage: 0.10
- Metro: 0.10
- School: 0.05

#### Diversity Control
- Deduplicates by neighborhood, floor plan, price band
- Ensures top results are not overly homogeneous
- Maximum 2 properties per neighborhood in top results

## Key Features

### 1. Permanent Hard Constraints (Red Lines)
```python
# Example: "cannot exceed budget"
if "cannot exceed" in query.lower():
    permanent_constraints.append(PermanentConstraint(
        constraint_type='price_max',
        field='price_for_sale',
        value=max_price,
        description=f"Price cannot exceed ${max_price:,}"
    ))
```

### 2. Progressive Relaxation
```python
relaxation_levels = [
    {'price_increase': 0.10, 'geo_radius': 3, 'description': '+10% price, +3km radius'},
    {'price_increase': 0.20, 'geo_radius': 8, 'description': '+20% price, +8km radius'},
    {'price_increase': 0.35, 'geo_radius': 15, 'description': '+35% price, +15km radius'}
]
```

### 3. Adaptive Alpha Calculation
```python
def calculate_query_information_density(query: str, intent: SearchIntent) -> float:
    density = 0.0
    
    # Count explicit criteria
    if intent.city: density += 1
    if intent.max_price_sale: density += 1
    if intent.min_beds: density += 1
    # ... more criteria
    
    # Normalize by query length
    query_words = len(query.split())
    if query_words > 0:
        density = density / query_words
    
    return min(density, 5.0)
```

### 4. Soft Preference Bonuses
```python
def calculate_soft_preference_bonus(listing: Dict[str, Any], intent: SearchIntent) -> float:
    bonus = 0.0
    
    if intent.good_schools and listing.get('school_rating', 0) >= 8:
        bonus += 0.08
    if intent.safe_area and listing.get('crime_index', 10) <= 3:
        bonus += 0.06
    if intent.walkable and listing.get('shopping_idx', 0) >= 7:
        bonus += 0.05
    # ... more preferences
    
    return bonus
```

## API Usage

### New Endpoint: `/improved-search`

```python
POST /improved-search
{
    "query": "3-bedroom house in San Francisco under $1.2M with garage, cannot exceed budget",
    "limit": 10,
    "reasons": true
}
```

### Response Format
```json
{
    "listings": [
        {
            "id": "uuid",
            "title": "Property Title",
            "address": "123 Main St, San Francisco, CA",
            "price": 1200000,
            "bedrooms": 3,
            "bathrooms": 2,
            "match_percent": 0.85,
            "similarity_score": 0.92,
            "final_score": 0.89,
            "matched_criteria": ["budget", "bedrooms", "garage"],
            "unmatched_criteria": ["school"],
            "relaxation_penalty": 0.0,
            "soft_preference_bonus": 0.08,
            "reason": "Excellent match (85%). Meets: budget, bedrooms, garage. High semantic similarity.",
            "relaxation_explanation": ""
        }
    ],
    "total_count": 10,
    "query": "3-bedroom house in San Francisco under $1.2M with garage, cannot exceed budget",
    "search_method": "improved_algorithm",
    "explanation": "Found 10 properties using improved recommendation algorithm with adaptive scoring.",
    "suggestions": [
        "Try adjusting your criteria for more options",
        "Consider nearby areas",
        "Explore different property types"
    ]
}
```

## Testing

Run the test script to see the algorithm in action:

```bash
python test_improved_algorithm.py
```

This will test various scenarios:
1. **Strict requirements** with hard constraints
2. **Flexible requirements** with soft preferences
3. **Very specific requirements** in particular neighborhoods
4. **Minimal requirements** that trigger semantic search
5. **Impossible requirements** that return empty results

## Advantages Over Previous Algorithm

### 1. **Intelligent Constraint Handling**
- Distinguishes between permanent and relaxable constraints
- Respects user's "red lines" while being flexible on preferences
- Provides clear explanations when constraints cannot be met

### 2. **Progressive Relaxation**
- Systematic approach to finding alternatives
- Transparent relaxation process with explanations
- Prevents over-relaxation that could lead to irrelevant results

### 3. **Adaptive Scoring**
- Balances structured criteria with semantic similarity
- Adjusts based on query information density
- More accurate for both specific and vague queries

### 4. **Better User Experience**
- Clear explanations for why properties were recommended
- Transparency about relaxation applied
- Helpful suggestions when no results are found

### 5. **Diversity Control**
- Prevents result clustering in same neighborhood
- Ensures variety in recommendations
- Better exploration of available options

## Configuration

### Relaxation Parameters
```python
# Adjust these values in the algorithm
relaxation_levels = [
    {'price_increase': 0.10, 'geo_radius': 3},  # Level 1
    {'price_increase': 0.20, 'geo_radius': 8},  # Level 2
    {'price_increase': 0.35, 'geo_radius': 15}  # Level 3
]
```

### Scoring Weights
```python
criteria_weights = {
    'budget': 0.35,
    'bedrooms': 0.25,
    'bathrooms': 0.15,
    'garage': 0.10,
    'metro': 0.10,
    'school': 0.05
}
```

### Soft Preference Bonuses
```python
# Adjust bonus values for different preferences
if intent.good_schools and school_rating >= 8:
    bonus += 0.08  # High bonus for good schools
if intent.safe_area and crime_index <= 3:
    bonus += 0.06  # Medium bonus for safe areas
```

## Future Enhancements

1. **Machine Learning Integration**: Learn from user feedback to improve scoring
2. **Dynamic Relaxation**: Adjust relaxation levels based on market conditions
3. **Personalization**: Consider user history and preferences
4. **Real-time Updates**: Incorporate market changes and new listings
5. **Advanced Diversity**: Consider more factors for result variety

