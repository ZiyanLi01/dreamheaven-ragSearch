# 🚀 ETL Pipeline Quick Reference

## 📋 **How to Check Listings Status**

### Check Recent Listings
```bash
# Check all recent listings and their status
python scripts/check_recent_listings.py

# Check with custom time period (e.g., last 14 days)
python scripts/check_recent_listings.py --days-back 14
```

### Check Environment Variables
```bash
# Verify all required environment variables are set
python test_env_variables.py
```

## 🔄 **How to Process Listings with Pipeline**

### Quick Start (Recommended)
```bash
# Interactive pipeline runner with environment checks
python run_recent_listings_pipeline.py
```

### Manual Processing
```bash
# Test run (no database changes)
python jobs/process_recent_listings.py --dry-run --days-back 7

# Process listings from last 7 days
python jobs/process_recent_listings.py --days-back 7

# Process listings from last 30 days
python jobs/process_recent_listings.py --days-back 30

# Process with verbose logging
python jobs/process_recent_listings.py --days-back 7 --verbose
```

## 📊 **What the Pipeline Does**

### For Each Listing, the Pipeline:
1. **Generates Structured Tags** (2-5 tags per listing)
   - Location-based tags (e.g., "Downtown", "Waterfront")
   - Property type tags (e.g., "Penthouse", "Condo")
   - Amenity tags (e.g., "Parking", "Metro Access")

2. **Creates Embedding Text** (500 characters)
   - Optimized text with semantic cues
   - Structured facts about the property
   - Enhanced for better embedding quality

3. **Calculates Embeddings** (1536 dimensions)
   - Uses OpenAI's text-embedding-3-small model
   - Vector representation for semantic search

## 🎯 **Pipeline Output Example**

```
🚀 Starting Recent Listings Pipeline Processing...
📦 Processing 3 recent listings...

🔄 Processing listing 1/3: abc-123
   Title: Beautiful South-Facing Apartment...
   ✅ Success: 4 tags, 500 chars, 1536 dims

🎉 Recent listings pipeline processing completed!
📊 Final Statistics:
   Total processed: 3
   Successfully updated: 3
   Tags added: 3
   Embedding text added: 3
   Embeddings added: 3
```

## 🔧 **Environment Variables Required**

Make sure these are set in your `.env` file:
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
DATABASE_URL=postgresql://...
OPENAI_API_KEY=your-openai-api-key
```

## 📅 **Automated Processing**

### Daily Processing (Cron Job)
```bash
# Add to crontab for daily processing at 2 AM
0 2 * * * cd /path/to/dreamheaven-rag && python jobs/process_recent_listings.py --days-back 1
```

### Weekly Processing (Cron Job)
```bash
# Add to crontab for weekly processing on Sundays at 3 AM
0 3 * * 0 cd /path/to/dreamheaven-rag && python jobs/process_recent_listings.py --days-back 7
```

## 🚨 **Troubleshooting**

### Common Issues
1. **Environment Variables Missing**
   ```bash
   python test_env_variables.py
   ```

2. **Database Connection Issues**
   ```bash
   python scripts/check_recent_listings.py
   ```

3. **Pipeline Errors**
   ```bash
   python jobs/process_recent_listings.py --dry-run --verbose
   ```

### Check Database Status
```bash
# Comprehensive database status check
python scripts/check_database_status.py
```

## 📈 **Monitoring Pipeline Success**

After running the pipeline, verify results:
```bash
# Check that all recent listings are complete
python scripts/check_recent_listings.py

# Look for: "Complete listings: X" and "Listings needing updates: 0"
```

## 🎯 **Key Commands Summary**

| Action | Command |
|--------|---------|
| Check listings | `python scripts/check_recent_listings.py` |
| Test environment | `python test_env_variables.py` |
| Quick pipeline | `python run_recent_listings_pipeline.py` |
| Process listings | `python jobs/process_recent_listings.py --days-back 7` |
| Dry run | `python jobs/process_recent_listings.py --dry-run` |
| Verbose mode | `python jobs/process_recent_listings.py --verbose` |

## 🔄 **Pipeline Logic**

1. **Automatic Discovery**: Finds listings with recent `updated_at` timestamps
2. **Smart Detection**: Identifies listings missing tags, embedding_text, or embeddings
3. **Complete Processing**: Generates all three components in one operation
4. **Database Updates**: Updates listings with complete data

The pipeline is designed to be **automatic** and **safe** - it only processes listings that actually need updates! 🚀
