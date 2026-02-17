# Cloud Deployment Guide

This guide shows how to deploy the Web Scraping API to various cloud platforms.

## Table of Contents

1. [Quick Start (Railway - Easiest)](#railway-deployment)
2. [Render Deployment](#render-deployment)
3. [Google Cloud Run](#google-cloud-run)
4. [AWS ECS/Fargate](#aws-ecs-fargate)
5. [Azure Container Instances](#azure-container-instances)
6. [DigitalOcean App Platform](#digitalocean-app-platform)
7. [Cost Comparison](#cost-comparison)
8. [Performance Tuning](#performance-tuning)

---

## Railway Deployment

**Best for**: Quick deployment, free tier available, easiest setup

### Prerequisites
- [Railway account](https://railway.app/) (free tier available)
- GitHub account

### Steps

1. **Push to GitHub**
   ```bash
   cd c:\Users\dadla\Desktop\PolicyLens
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create web-scraper-api --public
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app/)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect the Dockerfile

3. **Configure Environment Variables**
   In Railway dashboard → Variables:
   ```
   PORT=8000
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   MAX_CONCURRENT_REQUESTS=5
   ```

4. **Get Your API URL**
   - Railway provides a URL like: `https://your-app.railway.app`
   - Test with: `curl https://your-app.railway.app/health`

### Cost
- Free tier: 500 hours/month, $5 credit
- After free tier: ~$5-20/month depending on usage

---

## Render Deployment

**Best for**: Simple deployment, generous free tier

### Steps

1. **Create render.yaml**
   Create `render.yaml` in your project root:
   ```yaml
   services:
     - type: web
       name: web-scraper-api
       env: docker
       plan: free  # or starter for $7/month
       healthCheckPath: /health
       envVars:
         - key: PORT
           value: 8000
         - key: ENVIRONMENT
           value: production
         - key: LOG_LEVEL
           value: INFO
   ```

2. **Deploy**
   - Go to [render.com](https://render.com/)
   - New → Blueprint
   - Connect your GitHub repository
   - Render will auto-deploy using render.yaml

3. **Access Your API**
   - URL: `https://your-app.onrender.com`
   - Free tier spins down after 15 min inactivity (cold start ~30s)

### Cost
- Free tier: Unlimited, but spins down when idle
- Starter: $7/month, always on
- Standard: $25/month, more resources

---

## Google Cloud Run

**Best for**: Scalability, pay-per-use, serverless

### Prerequisites
- [Google Cloud account](https://cloud.google.com/)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed

### Steps

1. **Build and Push to Google Container Registry**
   ```bash
   # Set project ID
   gcloud config set project YOUR_PROJECT_ID
   
   # Enable required APIs
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   
   # Build and push
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/scraper-api
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy scraper-api \
     --image gcr.io/YOUR_PROJECT_ID/scraper-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8000 \
     --memory 512Mi \
     --cpu 1 \
     --min-instances 0 \
     --max-instances 10 \
     --timeout 300 \
     --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO
   ```

3. **Get Your URL**
   ```bash
   gcloud run services describe scraper-api --region us-central1
   ```

### Cost
- Free tier: 2M requests/month, 360,000 GB-seconds/month
- After: ~$0.00024 per request (scales to zero when idle)
- Estimated: $5-15/month for moderate use

---

## AWS ECS Fargate

**Best for**: Enterprise, AWS ecosystem integration

### Prerequisites
- AWS account with CLI configured
- Docker installed locally

### Steps

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name scraper-api
   
   # Get login
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin \
     YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   ```

2. **Build and Push Image**
   ```bash
   docker build -t scraper-api .
   docker tag scraper-api:latest \
     YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/scraper-api:latest
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/scraper-api:latest
   ```

3. **Create Task Definition**
   Create `ecs-task-definition.json`:
   ```json
   {
     "family": "scraper-api",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "containerDefinitions": [
       {
         "name": "scraper-api",
         "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/scraper-api:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {"name": "ENVIRONMENT", "value": "production"},
           {"name": "LOG_LEVEL", "value": "INFO"}
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/scraper-api",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

4. **Deploy**
   ```bash
   # Create cluster
   aws ecs create-cluster --cluster-name scraper-cluster
   
   # Register task
   aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
   
   # Create service
   aws ecs create-service \
     --cluster scraper-cluster \
     --service-name scraper-api-service \
     --task-definition scraper-api \
     --desired-count 1 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
   ```

5. **Create Application Load Balancer** (for HTTPS)
   - Use AWS Console or CLI
   - Point to ECS service
   - Configure health check: `/health`

### Cost
- Fargate: ~$0.04048/hour for 0.25 vCPU, 0.5 GB
- Approximately $30/month for always-on
- Plus data transfer costs

---

## Azure Container Instances

**Best for**: Microsoft ecosystem, simple container hosting

### Prerequisites
- Azure account
- Azure CLI installed

### Steps

1. **Login and Create Resource Group**
   ```bash
   az login
   az group create --name scraper-rg --location eastus
   ```

2. **Create Azure Container Registry** (optional)
   ```bash
   az acr create --resource-group scraper-rg \
     --name scraperregistry --sku Basic
   
   az acr login --name scraperregistry
   
   docker tag scraper-api scraperregistry.azurecr.io/scraper-api:latest
   docker push scraperregistry.azurecr.io/scraper-api:latest
   ```

3. **Deploy Container**
   ```bash
   az container create \
     --resource-group scraper-rg \
     --name scraper-api \
     --image scraperregistry.azurecr.io/scraper-api:latest \
     --cpu 1 \
     --memory 1 \
     --registry-login-server scraperregistry.azurecr.io \
     --registry-username scraperregistry \
     --registry-password $(az acr credential show --name scraperregistry --query "passwords[0].value" -o tsv) \
     --ip-address Public \
     --ports 8000 \
     --environment-variables \
       ENVIRONMENT=production \
       LOG_LEVEL=INFO
   ```

4. **Get Public IP**
   ```bash
   az container show --resource-group scraper-rg --name scraper-api --query ipAddress.ip --output tsv
   ```

### Cost
- ~$0.0000133/vCPU-second + $0.0000015/GB-second
- Approximately $10-25/month for always-on

---

## DigitalOcean App Platform

**Best for**: Simple deployment, fixed pricing

### Steps

1. **Create App Spec**
   Create `.do/app.yaml`:
   ```yaml
   name: scraper-api
   services:
     - name: api
       dockerfile_path: Dockerfile
       github:
         repo: YOUR_USERNAME/web-scraper-api
         branch: main
         deploy_on_push: true
       health_check:
         http_path: /health
       envs:
         - key: ENVIRONMENT
           value: production
         - key: LOG_LEVEL
           value: INFO
       instance_count: 1
       instance_size_slug: basic-xxs
       http_port: 8000
       routes:
         - path: /
   ```

2. **Deploy via CLI**
   ```bash
   doctl apps create --spec .do/app.yaml
   ```

   Or use the web interface:
   - Go to [DigitalOcean Apps](https://cloud.digitalocean.com/apps)
   - Create App → GitHub repo
   - Configure build and run settings

3. **Access Your App**
   - URL: `https://your-app.ondigitalocean.app`

### Cost
- Basic: $5/month (512 MB RAM, 1 vCPU)
- Professional: $12/month (1 GB RAM, 1 vCPU)
- Fixed pricing, predictable costs

---

## Cost Comparison

| Platform | Free Tier | Paid (Monthly) | Best For |
|----------|-----------|----------------|----------|
| **Railway** | $5 credit, 500 hrs | $5-20 | Quick start, hobbyists |
| **Render** | Yes (sleeps) | $7-25 | Free projects, startups |
| **Google Cloud Run** | 2M requests | $5-15 | Pay-per-use, scaling |
| **AWS Fargate** | No | $30+ | Enterprise, AWS users |
| **Azure ACI** | No | $10-25 | Microsoft ecosystem |
| **DigitalOcean** | No | $5-12 | Fixed pricing |

### Recommendation
- **Learning/Testing**: Render (free tier), Railway
- **Production (low traffic)**: DigitalOcean, Railway
- **Production (scaling)**: Google Cloud Run
- **Enterprise**: AWS Fargate, Azure ACI

---

## Performance Tuning

### 1. Container Optimization

```dockerfile
# Multi-stage build to reduce image size
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt requirements-api.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt -r requirements-api.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2. Resource Limits

Recommended settings:
- **Memory**: 512 MB minimum, 1 GB recommended
- **CPU**: 1 vCPU minimum, 2 recommended for high traffic
- **Workers**: `(2 * CPU_CORES) + 1` for Uvicorn

### 3. Environment Variables

```bash
# Production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=4
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=60
ENABLE_GZIP=true

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
```

### 4. Caching

Add Redis for caching scraped content:

```python
# In api.py
from redis import Redis
import json

redis_client = Redis(host='your-redis-host', port=6379, db=0)

@app.post("/scrape")
async def scrape_url(request: ScrapeRequest):
    # Check cache
    cache_key = f"scrape:{request.url}:{request.preset}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Scrape and cache
    result = pipeline.scrape(request.url, ...)
    redis_client.setex(cache_key, 3600, json.dumps(result))  # 1 hour TTL
    return result
```

### 5. Monitoring

Add health monitoring:

```python
import psutil
from datetime import datetime

@app.get("/metrics")
async def metrics():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "uptime": (datetime.now() - start_time).total_seconds()
    }
```

### 6. Load Testing

Test your deployment:

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Test endpoint
hey -n 1000 -c 10 -m POST -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}' \
  https://your-api.com/scrape/simple
```

---

## Security Considerations

### 1. API Authentication

Add API key authentication:

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.post("/scrape", dependencies=[Depends(verify_api_key)])
async def scrape_url(request: ScrapeRequest):
    # Protected endpoint
    ...
```

### 2. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/scrape")
@limiter.limit("10/minute")
async def scrape_url(request: Request, scrape_req: ScrapeRequest):
    ...
```

### 3. HTTPS Only

Always use HTTPS in production. Most cloud providers offer free SSL certificates.

### 4. URL Validation

The API already validates URLs, but consider adding a whitelist/blacklist:

```python
BLOCKED_DOMAINS = ["localhost", "127.0.0.1", "internal.company.com"]

def validate_url(url: str):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    if any(blocked in domain for blocked in BLOCKED_DOMAINS):
        raise HTTPException(400, "Domain not allowed")
```

---

## Next Steps

1. **Choose a platform** based on your needs and budget
2. **Deploy using the guide** for your chosen platform
3. **Test with the client examples** from `api_client_examples.py`
4. **Add monitoring** and error tracking (Sentry, Datadog)
5. **Implement authentication** if needed
6. **Set up CI/CD** for automatic deployments

## Support

For issues or questions:
- Check the main README.md
- Review ARCHITECTURE.md for system design
- Test locally with `docker-compose up` first
- Check cloud provider logs for deployment issues
