# ETL Pipelines for Tags and Embedding Text

This document describes the ETL (Extract, Transform, Load) pipelines for generating tags and embedding text for property listings.

## Overview

The system implements two separate ETL pipelines:

1. **ETL #1: Structured Tags Generation** - Rule-based tag generation from structured fields
2. **ETL #2: Embedding Text Generation** - Semantic cue extraction from prose (title/description)

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   listings_v2   │    │   ETL #1        │    │   ETL #2        │
│                 │    │   Struct Tags   │    │   Embed Text    │
│ tags: NULL/[]   │───▶│                 │───▶│                 │
│                 │    │                 │    │                 │
│embedding_text:''│    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ETL #1: Structured Tags Generation

### Purpose
Generate canonical tags from structured listing fields using configurable rules.

### Configuration
- **File**: `config/tags_struct_rules.yaml`
- **Format**: YAML with rule definitions and thresholds

### Key Features
- **Normalization**: Unifies fields into comparable formats
- **Rule-based**: Configurable conditions → tag mappings
- **Idempotent**: Same input → same output
- **Auditable**: Tracks evidence and rule information

### Example Rules
```yaml
- name: "south_facing"
  condition: "facing == 'S'"
  tag: "south_facing"
  evidence_template: "Property faces south"

- name: "walk_to_metro"
  condition: "distance_to_metro_m <= 600"
  tag: "walk_to_metro"
  evidence_template: "Within {distance_to_metro_m}m of metro station"
```

### Global Thresholds
- `distance_to_metro_m`: 600 meters
- `school_rating`: 8/10
- `crime_index`: 0.3
- `year_renovated_recent`: 2020

## ETL #2: Embedding Text Generation

### Purpose
Build embedding-ready text from title and description using semantic cue extraction.

### Configuration
- **File**: `config/text_extraction_keywords.yaml`
- **Format**: YAML with keyword → cue mappings

### Key Features
- **Semantic Extraction**: Converts natural phrases to semantic cues
- **Composition**: Creates structured embedding text
- **Length Control**: Limits to ~500 characters for efficiency
- **Context Rules**: Handles complex patterns (years, distances)

### Example Keywords
```yaml
positive_keywords:
  "south-facing": "south_facing"
  "floor-to-ceiling windows": "good_light"
  "steps to": "walk_to_transit"
  "renovated": "renovated_recent"
```

### Embedding Text Structure
```
TITLE: [shortened title] | FACTS: [property facts] | TAGS: [extracted cues] | DESCRIPTION: [truncated description]
```

## Usage

### Prerequisites
1. Ensure `tags` and `embedding_text` are empty in `listings_v2`
2. Install required dependencies: `pip install pyyaml`

### Running ETL #1 (Structured Tags)

#### Dry Run (Recommended First)
```bash
python jobs/update_struct_tags.py --dry-run --verbose
```

#### Production Run
```bash
python jobs/update_struct_tags.py
```

### Running ETL #2 (Embedding Text)

#### Dry Run (Recommended First)
```bash
python jobs/update_embedding_text.py --dry-run --verbose
```

#### Production Run
```bash
python jobs/update_embedding_text.py
```

### Running Both ETLs in Sequence
```bash
# Step 1: Generate structured tags
python jobs/update_struct_tags.py

# Step 2: Generate embedding text
python jobs/update_embedding_text.py
```

## Configuration Tuning

### Adjusting Thresholds (ETL #1)
Edit `config/tags_struct_rules.yaml`:

```yaml
thresholds:
  distance_to_metro_m: 600  # Adjust walkability threshold
  school_rating: 8          # Adjust school quality threshold
  crime_index: 0.3          # Adjust safety threshold
```

### Adding New Rules (ETL #1)
Add to `config/tags_struct_rules.yaml`:

```yaml
- name: "new_feature"
  condition: "field_name == 'value'"
  tag: "new_tag"
  evidence_template: "Evidence description"
```

### Adding New Keywords (ETL #2)
Add to `config/text_extraction_keywords.yaml`:

```yaml
positive_keywords:
  "new phrase": "new_cue"
```

## Testing

### Unit Tests
```bash
# Test ETL #1
python -m unittest tests.test_etl_struct_tags

# Test ETL #2
python -m unittest tests.test_etl_embedding_text
```

### Manual Testing
```bash
# Test ETL #1 with sample data
python etl/struct_tags.py

# Test ETL #2 with sample data
python etl/embedding_text.py
```

## Monitoring and Logging

### Job Output
Both jobs provide detailed logging:
- Processing statistics
- Individual listing updates
- Error reporting
- Summary at completion

### Example Output
```
2024-01-15 10:30:00 - INFO - Starting structured tags update job (dry_run: False)
2024-01-15 10:30:01 - INFO - Found 20 listings with empty tags
2024-01-15 10:30:02 - INFO - Listing abc123: Generated tags: ['south_facing', 'parking_available']
2024-01-15 10:30:03 - INFO - Listing abc123: Successfully updated with 2 tags
...
2024-01-15 10:30:10 - INFO - ==================================================
2024-01-15 10:30:10 - INFO - STRUCTURED TAGS UPDATE JOB SUMMARY
2024-01-15 10:30:10 - INFO - ==================================================
2024-01-15 10:30:10 - INFO - Processed: 20
2024-01-15 10:30:10 - INFO - Updated: 18
2024-01-15 10:30:10 - INFO - Skipped: 2
2024-01-15 10:30:10 - INFO - Errors: 0
```

## Data Flow

### Before ETL
```sql
-- Listings have empty tags and embedding_text
SELECT id, tags, embedding_text FROM listings_v2 LIMIT 3;
-- Result:
-- id1 | NULL | ""
-- id2 | []   | ""
-- id3 | NULL | ""
```

### After ETL #1
```sql
-- Tags populated from structured fields
SELECT id, tags FROM listings_v2 LIMIT 3;
-- Result:
-- id1 | ["south_facing", "parking_available", "good_school"]
-- id2 | ["walk_to_metro", "renovated_recent"]
-- id3 | ["safe_area", "shopping_convenient"]
```

### After ETL #2
```sql
-- Embedding text populated from prose
SELECT id, LEFT(embedding_text, 100) FROM listings_v2 LIMIT 3;
-- Result:
-- id1 | "TITLE: Beautiful South-Facing Apartment... | FACTS: Apartment with 2 bedrooms... | TAGS: south_facing, good_light... | DESCRIPTION: This stunning apartment..."
-- id2 | "TITLE: Modern Loft Near Metro... | FACTS: Loft with 1 bedroom... | TAGS: walk_to_transit, renovated_recent... | DESCRIPTION: Recently renovated loft..."
-- id3 | "TITLE: Safe Neighborhood Home... | FACTS: House with 3 bedrooms... | TAGS: safe_area, shopping_convenient... | DESCRIPTION: Located in a safe neighborhood..."
```

## Best Practices

### Development
1. **Always run dry-run first** to verify changes
2. **Test with small datasets** before production
3. **Monitor logs** for unexpected behavior
4. **Backup data** before running ETLs

### Production
1. **Run during low-traffic periods**
2. **Monitor database performance**
3. **Set up alerts** for job failures
4. **Keep configuration versioned**

### Maintenance
1. **Review and update rules** periodically
2. **Monitor tag distribution** for bias
3. **Validate embedding text quality**
4. **Archive old configurations**

## Troubleshooting

### Common Issues

#### ETL #1 Issues
- **No tags generated**: Check field values and rule conditions
- **Unexpected tags**: Verify rule logic and thresholds
- **Performance issues**: Consider batch processing for large datasets

#### ETL #2 Issues
- **No cues extracted**: Check keyword mappings and text content
- **Long embedding text**: Verify length limiting logic
- **Missing content**: Ensure title/description are not empty

### Debug Mode
Enable verbose logging for detailed debugging:
```bash
python jobs/update_struct_tags.py --verbose
python jobs/update_embedding_text.py --verbose
```

## Future Enhancements

### Planned Features
1. **Machine Learning Integration**: Use ML models for cue extraction
2. **Real-time Processing**: Stream processing for new listings
3. **A/B Testing Framework**: Test different rule configurations
4. **Performance Optimization**: Parallel processing for large datasets

### Configuration Management
1. **Environment-specific configs**: Dev/staging/production
2. **Configuration validation**: Schema validation for YAML files
3. **Rollback capabilities**: Revert to previous configurations
4. **Configuration UI**: Web interface for rule management
