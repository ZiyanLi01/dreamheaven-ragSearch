# DreamHeaven RAG - Cloud Deployment Guide

## Cloud Deployment Checklist

### 1. Environment Variables (Required)

Set these in your cloud platform (Railway, Heroku, AWS, etc.):

```bash
# Supabase Database
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
DATABASE_URL=postgresql://postgres.wmolhwclvmtepgucujsy:RNUQUVt5Ge1rC1qy@aws-0-us-west-1.pooler.supabase.com:6543/postgres
# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# Service Configuration
PORT=8001
HOST=0.0.0.0
```

### 2. CORS Configuration for Frontend

Update `main.py` to allow your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "https://your-frontend-domain.com",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

### 3. Railway Deployment

1. **Connect Repository**: Link your GitHub repo to Railway
2. **Set Environment Variables**: Add all required env vars in Railway dashboard
3. **Deploy**: Railway will auto-deploy using the Dockerfile
4. **Get URL**: Railway provides a public URL like `https://your-app.railway.app`

### 4. Frontend Integration

#### API Endpoints

**Health Check:**
```javascript
GET https://your-api-url.railway.app/health
```

**AI Search:**
```javascript
POST https://your-api-url.railway.app/ai-search
Content-Type: application/json

{
  "query": "Find me a 2-bedroom apartment in San Francisco under $3000",
  "limit": 20,
  "offset": 0,
  "reasons": true
}
```

**Response Format:**
```javascript
{
  "items": [
    {
      "id": "listing-id",
      "title": "Beautiful 2BR Apartment",
      "description": "...",
      "price": 2800,
      "bedrooms": 2,
      "bathrooms": 2,
      "sqft": 1200,
      "neighborhood": "Mission District",
      "listing_type": "rent",
      "property_type": "apartment",
      "match_score": 0.95,
      "match_reason": "Perfect match for your criteria...",
      "relaxation_info": "No relaxations needed"
    }
  ],
  "total": 20,
  "query": "Find me a 2-bedroom apartment in San Francisco under $3000",
  "processing_time": 1.2
}
```

#### Frontend Code Example

```javascript
// React/Next.js example
const searchProperties = async (query) => {
  try {
    const response = await fetch('https://your-api-url.railway.app/ai-search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        limit: 20,
        offset: 0,
        reasons: true
      })
    });
    
    const data = await response.json();
    return data.items;
  } catch (error) {
    console.error('Search failed:', error);
    throw error;
  }
};
```

### 5. Production Considerations

#### Security
- ✅ Use HTTPS in production
- ✅ Configure CORS properly for your domain
- ✅ Use environment variables for secrets
- ✅ Rate limiting (consider adding)
- ✅ API key validation

#### Performance
- ✅ Database connection pooling
- ✅ Vector search optimization
- ✅ Caching (consider Redis)
- ✅ Load balancing for high traffic

#### Monitoring
- ✅ Health check endpoint: `/health`
- ✅ Logging configured
- ✅ Error handling
- ✅ Performance metrics

### 6. Testing Your Deployment

1. **Health Check:**
```bash
curl https://your-api-url.railway.app/health
```

2. **Test Search:**
```bash
curl -X POST https://your-api-url.railway.app/ai-search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find me a 2-bedroom apartment in San Francisco", "limit": 5}'
```

3. **Frontend Integration:**
- Test CORS with your frontend
- Verify API responses
- Check error handling

### 7. Troubleshooting

#### Common Issues:
- **CORS errors**: Update allow_origins in main.py
- **Database connection**: Verify DATABASE_URL and Supabase credentials
- **OpenAI errors**: Check OPENAI_API_KEY and billing
- **Port issues**: Ensure PORT is set correctly for your platform

#### Logs:
- Check Railway logs for errors
- Monitor application logs
- Verify environment variables are set

### 8. Scaling

- **Railway**: Auto-scales based on traffic
- **Database**: Supabase handles scaling
- **Caching**: Consider Redis for frequent queries
- **CDN**: For static assets if needed

## Ready for Production!

Your RAG system is now ready for cloud deployment and frontend integration. The API provides semantic search capabilities that can power your real estate application with natural language queries.
