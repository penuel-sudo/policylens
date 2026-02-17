# API Reference Documentation

Complete API reference for the Web Scraping API.

## Base URL

```
Local: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

Currently, the API is open (no authentication required). For production use, see [API_DEPLOYMENT.md](API_DEPLOYMENT.md#security-considerations) for authentication setup.

---

## Endpoints

### 1. Health Check

Check API health and version.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**cURL**:
```bash
curl http://localhost:8000/health
```

---

### 2. Get Presets

List available configuration presets.

**Endpoint**: `GET /presets`

**Response**:
```json
{
  "presets": ["default", "fast", "thorough", "articles", "llm"],
  "default_chunk_methods": ["character", "word", "sentence", "paragraph", "token"],
  "description": "Available presets: default (balanced), fast (quick extraction), thorough (deep cleaning), articles (news/blogs), llm (RAG-optimized)"
}
```

**cURL**:
```bash
curl http://localhost:8000/presets
```

---

### 3. Scrape Single URL (Full)

Scrape a single URL with complete control over all options.

**Endpoint**: `POST /scrape`

**Request Body**:
```json
{
  "url": "string (required)",
  "enable_chunking": "boolean (default: true)",
  "preset": "string (default: 'default')",
  "chunk_size": "integer (optional)",
  "chunk_overlap": "integer (optional)",
  "chunk_method": "string (optional)",
  "include_metadata": "boolean (default: true)",
  "include_statistics": "boolean (default: true)"
}
```

**Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | ✅ Yes | - | URL to scrape |
| `enable_chunking` | boolean | No | `true` | Whether to chunk the content |
| `preset` | string | No | `"default"` | Configuration preset: `default`, `fast`, `thorough`, `articles`, `llm` |
| `chunk_size` | integer | No | Preset default | Custom chunk size in characters/tokens |
| `chunk_overlap` | integer | No | Preset default | Overlap between chunks |
| `chunk_method` | string | No | Preset default | Method: `character`, `word`, `sentence`, `paragraph`, `token` |
| `include_metadata` | boolean | No | `true` | Include metadata in response |
| `include_statistics` | boolean | No | `true` | Include statistics in response |

**Response**:
```json
{
  "success": true,
  "url": "https://example.com/article",
  "data": {
    "metadata": {
      "title": "Article Title",
      "author": "John Doe",
      "published_date": "2024-01-15",
      "description": "Article description",
      "language": "en",
      "url": "https://example.com/article",
      "domain": "example.com",
      "scraped_at": "2024-01-15T10:30:00Z"
    },
    "content": {
      "cleaned_text": "Full cleaned text content...",
      "chunks": [
        {
          "chunk_index": 0,
          "text": "First chunk of content...",
          "chunk_length": 512,
          "metadata": {
            "source_url": "https://example.com/article",
            "chunk_method": "paragraph",
            "position": "start"
          }
        }
      ]
    },
    "statistics": {
      "raw": {
        "total_length": 15234,
        "word_count": 2345,
        "sentence_count": 123
      },
      "clean": {
        "total_length": 12456,
        "word_count": 2100,
        "sentence_count": 115
      },
      "chunks": {
        "total_chunks": 8,
        "avg_chunk_size": 1557,
        "method": "paragraph"
      }
    }
  },
  "processing_time": 2.34
}
```

**Error Response**:
```json
{
  "success": false,
  "url": "https://example.com/article",
  "error": "Failed to fetch URL: Connection timeout",
  "error_type": "FetchError"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://en.wikipedia.org/wiki/Web_scraping",
    "enable_chunking": true,
    "preset": "articles",
    "chunk_method": "paragraph"
  }'
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:8000/scrape",
    json={
        "url": "https://example.com/article",
        "preset": "llm",
        "chunk_method": "token",
        "chunk_size": 1000
    }
)

result = response.json()
print(f"Got {len(result['data']['content']['chunks'])} chunks")
```

---

### 4. Scrape Simple (Text Only)

Quick endpoint that returns only the cleaned text.

**Endpoint**: `POST /scrape/simple`

**Request Body**:
```json
{
  "url": "string (required)"
}
```

**Response**:
```json
{
  "success": true,
  "url": "https://example.com/article",
  "text": "Full cleaned text content without chunking...",
  "processing_time": 1.23
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/scrape/simple \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:8000/scrape/simple",
    json={"url": "https://example.com/article"}
)

text = response.json()["text"]
print(f"Extracted {len(text)} characters")
```

---

### 5. Scrape Chunks (Chunks Only)

Returns only the chunks, optimized for LLM/RAG pipelines.

**Endpoint**: `POST /scrape/chunks`

**Request Body**:
```json
{
  "url": "string (required)",
  "preset": "string (default: 'llm')",
  "chunk_size": "integer (optional)",
  "chunk_method": "string (default: 'paragraph')"
}
```

**Response**:
```json
{
  "success": true,
  "url": "https://example.com/article",
  "chunks": [
    {
      "chunk_index": 0,
      "text": "First chunk...",
      "chunk_length": 512,
      "metadata": {
        "source_url": "https://example.com/article",
        "chunk_method": "paragraph",
        "position": "start"
      }
    },
    {
      "chunk_index": 1,
      "text": "Second chunk...",
      "chunk_length": 498,
      "metadata": {
        "source_url": "https://example.com/article",
        "chunk_method": "paragraph",
        "position": "middle"
      }
    }
  ],
  "total_chunks": 2,
  "processing_time": 1.56
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/scrape/chunks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "preset": "llm",
    "chunk_method": "token",
    "chunk_size": 1000
  }'
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:8000/scrape/chunks",
    json={
        "url": "https://example.com/article",
        "preset": "llm",
        "chunk_method": "token"
    }
)

chunks = response.json()["chunks"]

# Use in your RAG pipeline
for chunk in chunks:
    embedding = your_embedding_model.encode(chunk["text"])
    vector_db.add(embedding, chunk["text"], chunk["metadata"])
```

---

### 6. Batch Scraping

Scrape multiple URLs in a single request.

**Endpoint**: `POST /scrape/batch`

**Request Body**:
```json
{
  "urls": ["string", "string"],
  "enable_chunking": "boolean (default: true)",
  "preset": "string (default: 'fast')",
  "chunk_method": "string (optional)"
}
```

**Limits**:
- Maximum 10 URLs per request
- Each URL is processed independently
- Failed URLs don't stop batch processing

**Response**:
```json
{
  "total": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "success": true,
      "url": "https://example.com/article1",
      "data": {
        "metadata": {...},
        "content": {...},
        "statistics": {...}
      }
    },
    {
      "success": true,
      "url": "https://example.com/article2",
      "data": {
        "metadata": {...},
        "content": {...},
        "statistics": {...}
      }
    }
  ],
  "processing_time": 4.56
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/scrape/batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/article1",
      "https://example.com/article2"
    ],
    "preset": "fast",
    "enable_chunking": false
  }'
```

**Python Example**:
```python
import requests

urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

response = requests.post(
    "http://localhost:8000/scrape/batch",
    json={
        "urls": urls,
        "preset": "fast"
    }
)

results = response.json()
print(f"Processed {results['successful']}/{results['total']} URLs")

for result in results["results"]:
    if result["success"]:
        print(f"✓ {result['url']}: {result['data']['metadata']['title']}")
    else:
        print(f"✗ {result['url']}: {result['error']}")
```

---

## Configuration Presets

### Default
Balanced settings for general web content.

```python
{
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "chunk_method": "paragraph",
    "timeout": 30,
    "retries": 3
}
```

### Fast
Quick extraction with minimal processing.

```python
{
    "chunk_size": 2000,
    "chunk_overlap": 100,
    "chunk_method": "character",
    "timeout": 10,
    "retries": 1
}
```

### Thorough
Deep cleaning and processing.

```python
{
    "chunk_size": 800,
    "chunk_overlap": 150,
    "chunk_method": "sentence",
    "timeout": 60,
    "retries": 5
}
```

### Articles
Optimized for news articles and blog posts.

```python
{
    "chunk_size": 1500,
    "chunk_overlap": 200,
    "chunk_method": "paragraph",
    "timeout": 30,
    "retries": 3
}
```

### LLM
Optimized for RAG and LLM pipelines (token-based chunking).

```python
{
    "chunk_size": 1024,  # tokens
    "chunk_overlap": 128,
    "chunk_method": "token",
    "timeout": 45,
    "retries": 3
}
```

---

## Chunking Methods

### Character
Split by character count.

**Use when**: Fixed-size chunks needed
**Pros**: Predictable size
**Cons**: May split words/sentences

```json
{"chunk_method": "character", "chunk_size": 1000}
```

### Word
Split by word count.

**Use when**: Word-based analysis
**Pros**: Doesn't split words
**Cons**: Variable character size

```json
{"chunk_method": "word", "chunk_size": 200}
```

### Sentence
Split by sentences.

**Use when**: Semantic coherence important
**Pros**: Maintains sentence integrity
**Cons**: Variable chunk sizes

```json
{"chunk_method": "sentence", "chunk_size": 5}
```

### Paragraph
Split by paragraphs.

**Use when**: Topic-based chunking
**Pros**: Maintains topical coherence
**Cons**: Highly variable sizes

```json
{"chunk_method": "paragraph"}
```

### Token
Split by tokens (for LLMs).

**Use when**: LLM/RAG pipelines, embeddings
**Pros**: Respects token limits (GPT, Claude, etc.)
**Cons**: Slower processing

```json
{"chunk_method": "token", "chunk_size": 1024}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "url": "https://example.com/bad-url",
  "error": "Error description",
  "error_type": "ErrorTypeName"
}
```

### Error Types

| Error Type | HTTP Code | Description |
|------------|-----------|-------------|
| `ValidationError` | 400 | Invalid request parameters |
| `FetchError` | 500 | Failed to fetch URL |
| `ParseError` | 500 | Failed to parse HTML |
| `ChunkingError` | 500 | Failed to chunk content |
| `TimeoutError` | 504 | Request timed out |

### Example Error Handling

**Python**:
```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/scrape",
        json={"url": "https://example.com/article"},
        timeout=60
    )
    response.raise_for_status()
    
    result = response.json()
    
    if result["success"]:
        print("Success!")
    else:
        print(f"Error: {result['error']}")
        
except requests.Timeout:
    print("Request timed out")
except requests.HTTPError as e:
    print(f"HTTP error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

**JavaScript**:
```javascript
async function scrapeUrl(url) {
  try {
    const response = await fetch('http://localhost:8000/scrape', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url})
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      return result.data;
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    console.error('Scraping failed:', error);
    throw error;
  }
}
```

---

## Rate Limits

**Current**: No rate limits (open API)

**Recommended for Production**:
- 100 requests/minute per IP
- 1000 requests/hour per API key
- Max 10 URLs per batch request

See [API_DEPLOYMENT.md](API_DEPLOYMENT.md#security-considerations) for implementation.

---

## Response Times

Typical response times:

| Endpoint | Average | Notes |
|----------|---------|-------|
| `/health` | <10ms | Instant |
| `/presets` | <10ms | Instant |
| `/scrape/simple` | 1-3s | Depends on URL |
| `/scrape` | 1-4s | With chunking |
| `/scrape/chunks` | 1-4s | Similar to `/scrape` |
| `/scrape/batch` | 3-15s | 10 URLs max |

**Factors affecting speed**:
- Target website response time
- Content size
- Preset choice (fast < default < thorough)
- Chunking method (character < word < paragraph < token)

---

## Best Practices

### 1. Choose the Right Endpoint

```python
# ✅ For simple text extraction
text = requests.post(url, json={"url": "..."}).json()["text"]

# ✅ For LLM/RAG pipelines
chunks = requests.post(url, json={
    "url": "...",
    "preset": "llm",
    "chunk_method": "token"
}).json()["chunks"]

# ✅ For full control
result = requests.post(url, json={
    "url": "...",
    "enable_chunking": True,
    "chunk_size": 1000,
    "include_statistics": True
}).json()
```

### 2. Handle Errors Gracefully

```python
def scrape_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/scrape/simple",
                json={"url": url},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    return result["text"]
            
            time.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    
    raise Exception(f"Failed after {max_retries} attempts")
```

### 3. Use Batch Endpoint Efficiently

```python
# ✅ Good: Batch similar URLs
urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
]
results = requests.post(url, json={"urls": urls, "preset": "fast"})

# ❌ Bad: Multiple single requests
for url in urls:
    result = requests.post(url, json={"url": url})
```

### 4. Choose Appropriate Presets

```python
# ✅ Fast preset for bulk scraping
bulk_scrape(urls, preset="fast")

# ✅ LLM preset for embeddings
rag_pipeline(url, preset="llm", chunk_method="token")

# ✅ Articles preset for news
news_scraper(url, preset="articles")
```

### 5. Cache Results

```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def scrape_cached(url):
    response = requests.post(
        "http://localhost:8000/scrape/simple",
        json={"url": url}
    )
    return response.json()["text"]
```

---

## Integration Examples

### RAG Pipeline

```python
from openai import OpenAI
import requests

def add_to_knowledge_base(url):
    """Scrape URL and add to vector database."""
    
    # Get chunks
    response = requests.post(
        "http://localhost:8000/scrape/chunks",
        json={
            "url": url,
            "preset": "llm",
            "chunk_method": "token",
            "chunk_size": 1024
        }
    )
    
    chunks = response.json()["chunks"]
    
    # Generate embeddings
    client = OpenAI()
    
    for chunk in chunks:
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk["text"]
        )
        
        # Store in vector DB
        vector_db.add(
            vector=embedding.data[0].embedding,
            text=chunk["text"],
            metadata={
                "url": url,
                "chunk_index": chunk["chunk_index"],
                **chunk["metadata"]
            }
        )
```

### Content Analysis

```python
import requests
from collections import Counter
import re

def analyze_content(url):
    """Analyze content from URL."""
    
    response = requests.post(
        "http://localhost:8000/scrape",
        json={"url": url, "preset": "thorough"}
    )
    
    result = response.json()
    
    if not result["success"]:
        raise Exception(result["error"])
    
    text = result["data"]["content"]["cleaned_text"]
    stats = result["data"]["statistics"]
    
    # Word frequency
    words = re.findall(r'\b\w+\b', text.lower())
    common_words = Counter(words).most_common(10)
    
    return {
        "title": result["data"]["metadata"]["title"],
        "word_count": stats["clean"]["word_count"],
        "sentence_count": stats["clean"]["sentence_count"],
        "common_words": common_words,
        "language": result["data"]["metadata"]["language"]
    }
```

### Batch News Scraper

```python
import requests
from concurrent.futures import ThreadPoolExecutor

def scrape_news_sites(urls):
    """Scrape multiple news sites in parallel."""
    
    def scrape_one(url):
        try:
            response = requests.post(
                "http://localhost:8000/scrape",
                json={"url": url, "preset": "articles"},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "url": url, "error": str(e)}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(scrape_one, urls))
    
    articles = []
    for result in results:
        if result["success"]:
            articles.append({
                "title": result["data"]["metadata"]["title"],
                "author": result["data"]["metadata"].get("author"),
                "date": result["data"]["metadata"].get("published_date"),
                "text": result["data"]["content"]["cleaned_text"],
                "url": result["url"]
            })
    
    return articles
```

---

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Simple Test
```bash
curl -X POST http://localhost:8000/scrape/simple \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Full Test
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://en.wikipedia.org/wiki/Web_scraping",
    "preset": "articles",
    "enable_chunking": true
  }' | jq '.'
```

---

## Support

- **Documentation**: [README.md](README.md), [QUICKSTART.md](QUICKSTART.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Deployment**: [API_DEPLOYMENT.md](API_DEPLOYMENT.md)
- **Examples**: [api_client_examples.py](api_client_examples.py)

## Next Steps

1. Deploy to cloud (see [API_DEPLOYMENT.md](API_DEPLOYMENT.md))
2. Add authentication for production use
3. Set up monitoring and logging
4. Implement rate limiting
5. Add caching layer (Redis)
