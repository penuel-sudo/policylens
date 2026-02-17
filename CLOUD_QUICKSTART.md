# Quick Start: Cloud Deployment

Get your Web Scraping API running in the cloud in under 10 minutes.

## Option 1: Railway (Recommended - Easiest)

**Time**: 5 minutes | **Cost**: Free tier available

### Steps

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   # or
   powershell -c "iwr https://railway.app/install.ps1 | iex"
   ```

2. **Login**
   ```bash
   railway login
   ```

3. **Deploy** (from project directory)
   ```bash
   cd c:\Users\dadla\Desktop\PolicyLens
   railway init
   railway up
   ```

4. **Get URL**
   ```bash
   railway domain
   ```

5. **Test**
   ```bash
   curl https://your-app.railway.app/health
   ```

✅ **Done!** Your API is live.

---

## Option 2: Render (Best Free Tier)

**Time**: 5 minutes | **Cost**: Free (with cold starts)

### Steps

1. **Push to GitHub** (if not already)
   ```bash
   cd c:\Users\dadla\Desktop\PolicyLens
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create web-scraper-api --public --push --source .
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render auto-detects Dockerfile
   - Click "Create Web Service"

3. **Wait 2-3 minutes** for build

4. **Get URL** from dashboard: `https://your-app.onrender.com`

5. **Test**
   ```bash
   curl https://your-app.onrender.com/health
   ```

✅ **Done!** Free tier includes:
- Automatic SSL
- Automatic deployments on git push
- Free tier spins down after 15 min (cold start ~30s)

---

## Option 3: Google Cloud Run (Best for Scaling)

**Time**: 10 minutes | **Cost**: Free tier, then pay-per-use

### Prerequisites
- Google Cloud account
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed

### Steps

1. **Login and Set Project**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable APIs**
   ```bash
   gcloud services enable run.googleapis.com containerregistry.googleapis.com
   ```

3. **Build and Deploy** (one command!)
   ```bash
   cd c:\Users\dadla\Desktop\PolicyLens
   
   gcloud run deploy scraper-api \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8000
   ```

4. **Wait for deployment** (~5 minutes)

5. **Test** (URL shown in output)
   ```bash
   curl https://scraper-api-xxx-uc.a.run.app/health
   ```

✅ **Done!** Benefits:
- Scales to zero (no cost when idle)
- Auto-scales to millions of requests
- Pay only for what you use

---

## Local Testing First

Before deploying, test locally:

### Option A: Docker Compose (Recommended)

```bash
cd c:\Users\dadla\Desktop\PolicyLens
docker-compose up
```

Access at: `http://localhost:8000`

### Option B: Direct Python

```bash
cd c:\Users\dadla\Desktop\PolicyLens
pip install -r requirements.txt -r requirements-api.txt
python -m nltk.downloader punkt
python api.py
```

Access at: `http://localhost:8000`

### Test Endpoints

**Health Check**:
```bash
curl http://localhost:8000/health
```

**Simple Scrape**:
```bash
curl -X POST http://localhost:8000/scrape/simple \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://example.com\"}"
```

**Full Scrape**:
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://en.wikipedia.org/wiki/Python_(programming_language)\", \"preset\": \"articles\"}"
```

---

## Using Your Deployed API

### From Python

```python
import requests

API_URL = "https://your-app.railway.app"  # Replace with your URL

# Simple scraping
response = requests.post(
    f"{API_URL}/scrape/simple",
    json={"url": "https://example.com/article"}
)
text = response.json()["text"]
print(f"Got {len(text)} characters")

# Get chunks for LLM
response = requests.post(
    f"{API_URL}/scrape/chunks",
    json={
        "url": "https://example.com/article",
        "preset": "llm",
        "chunk_method": "token"
    }
)
chunks = response.json()["chunks"]
print(f"Got {len(chunks)} chunks")
```

### From JavaScript

```javascript
const API_URL = 'https://your-app.railway.app';

async function scrapeUrl(url) {
  const response = await fetch(`${API_URL}/scrape/simple`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url})
  });
  
  const result = await response.json();
  return result.text;
}

// Usage
const text = await scrapeUrl('https://example.com/article');
console.log(`Got ${text.length} characters`);
```

### From cURL

```bash
# Set your URL
API_URL="https://your-app.railway.app"

# Scrape
curl -X POST "${API_URL}/scrape/simple" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## Environment Variables

For production, set these in your cloud platform:

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000
MAX_CONCURRENT_REQUESTS=10
ALLOWED_ORIGINS=*
```

**Railway**: Settings → Variables  
**Render**: Environment → Environment Variables  
**Cloud Run**: `--set-env-vars` flag or Console

---

## Cost Estimates

### Free Tiers

| Platform | Free Tier | Limits |
|----------|-----------|--------|
| **Railway** | $5 credit | 500 hours/month |
| **Render** | Unlimited | Spins down after 15 min |
| **Google Cloud Run** | 2M requests | 360,000 GB-seconds/month |

### Paid (Monthly Estimates)

**Light Use** (100 requests/day):
- Railway: $0-5
- Render: $0 (free tier)
- Cloud Run: $0 (free tier)

**Medium Use** (1,000 requests/day):
- Railway: $5-10
- Render: $7 (Starter plan)
- Cloud Run: $1-5

**Heavy Use** (10,000 requests/day):
- Railway: $15-30
- Render: $25 (Standard plan)
- Cloud Run: $10-20

---

## Troubleshooting

### Build Fails

**Issue**: Docker build fails  
**Fix**: Test locally first
```bash
docker build -t scraper-api .
docker run -p 8000:8000 scraper-api
```

### Timeout Errors

**Issue**: Requests timing out  
**Fix**: Increase timeout in cloud platform settings
- Railway: No change needed
- Render: Upgrade to paid plan (free tier has 30s limit)
- Cloud Run: Add `--timeout 300` flag

### Memory Issues

**Issue**: Out of memory crashes  
**Fix**: Increase memory limit
- Railway: Upgrade plan
- Render: Settings → Memory (512MB → 1GB)
- Cloud Run: `--memory 1Gi` flag

### Cold Starts (Render Free Tier)

**Issue**: First request takes 30+ seconds  
**Fix**: Either:
1. Use Railway instead (no cold starts)
2. Upgrade to Render paid plan ($7/month)
3. Accept cold starts for free hosting

---

## Security Checklist

Before production use:

- [ ] Enable HTTPS (automatic on all platforms)
- [ ] Add API key authentication
- [ ] Set up rate limiting
- [ ] Configure CORS properly
- [ ] Add request logging
- [ ] Set up error monitoring (Sentry)
- [ ] Enable firewall rules
- [ ] Review URL validation

See [API_DEPLOYMENT.md](API_DEPLOYMENT.md#security-considerations) for implementation.

---

## Next Steps

1. ✅ **Deploy** using one of the options above
2. ✅ **Test** your live API
3. ✅ **Integrate** into your project (examples above)
4. 📖 **Read** [API_REFERENCE.md](API_REFERENCE.md) for all endpoints
5. 🔒 **Secure** your API for production use
6. 📊 **Monitor** with logging and error tracking

---

## Quick Links

- **Full Deployment Guide**: [API_DEPLOYMENT.md](API_DEPLOYMENT.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Client Examples**: [api_client_examples.py](api_client_examples.py)
- **Main Documentation**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Support

Having issues? Check:

1. **Logs** in your cloud platform dashboard
2. **Local testing** - does it work with `docker-compose up`?
3. **Documentation** - check all the guides above
4. **API health** - hit the `/health` endpoint

Common issues:
- Missing environment variables
- Memory/CPU limits too low
- Timeout too short
- NLTK data not downloaded (should be in Dockerfile)
