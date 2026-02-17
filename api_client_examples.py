"""
API Client Examples
Demonstrates how to use the Web Scraping API from different contexts.
"""

import requests
import json
from typing import List, Dict, Any, Optional


API_BASE_URL = "http://localhost:8000"  # Change to your deployed URL


class ScraperAPIClient:
    """Python client for the Web Scraping API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def scrape(
        self,
        url: str,
        enable_chunking: bool = True,
        preset: str = "default",
        chunk_size: Optional[int] = None,
        chunk_method: Optional[str] = None,
        include_metadata: bool = True,
        include_statistics: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape a single URL.
        
        Args:
            url: URL to scrape
            enable_chunking: Whether to chunk the content
            preset: Configuration preset (default, fast, thorough, articles, llm)
            chunk_size: Custom chunk size
            chunk_method: Chunking method (character, word, sentence, paragraph, token)
            include_metadata: Include metadata in response
            include_statistics: Include statistics in response
            
        Returns:
            Scraping result
        """
        payload = {
            "url": url,
            "enable_chunking": enable_chunking,
            "preset": preset,
            "include_metadata": include_metadata,
            "include_statistics": include_statistics
        }
        
        if chunk_size:
            payload["chunk_size"] = chunk_size
        if chunk_method:
            payload["chunk_method"] = chunk_method
        
        response = self.session.post(f"{self.base_url}/scrape", json=payload)
        response.raise_for_status()
        return response.json()
    
    def scrape_simple(self, url: str) -> str:
        """
        Simple scraping that returns only the text.
        
        Args:
            url: URL to scrape
            
        Returns:
            Cleaned text content
        """
        payload = {"url": url}
        response = self.session.post(f"{self.base_url}/scrape/simple", json=payload)
        response.raise_for_status()
        return response.json()["text"]
    
    def scrape_chunks(
        self,
        url: str,
        preset: str = "llm",
        chunk_size: Optional[int] = None,
        chunk_method: str = "paragraph"
    ) -> List[Dict[str, Any]]:
        """
        Scrape and return only chunks.
        
        Args:
            url: URL to scrape
            preset: Configuration preset
            chunk_size: Custom chunk size
            chunk_method: Chunking method
            
        Returns:
            List of chunks
        """
        payload = {
            "url": url,
            "preset": preset,
            "chunk_method": chunk_method
        }
        
        if chunk_size:
            payload["chunk_size"] = chunk_size
        
        response = self.session.post(f"{self.base_url}/scrape/chunks", json=payload)
        response.raise_for_status()
        return response.json()["chunks"]
    
    def scrape_batch(
        self,
        urls: List[str],
        enable_chunking: bool = True,
        preset: str = "fast"
    ) -> Dict[str, Any]:
        """
        Scrape multiple URLs.
        
        Args:
            urls: List of URLs to scrape (max 10)
            enable_chunking: Whether to chunk the content
            preset: Configuration preset
            
        Returns:
            Batch results
        """
        payload = {
            "urls": urls,
            "enable_chunking": enable_chunking,
            "preset": preset
        }
        
        response = self.session.post(f"{self.base_url}/scrape/batch", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_presets(self) -> Dict[str, Any]:
        """Get available configuration presets."""
        response = self.session.get(f"{self.base_url}/presets")
        response.raise_for_status()
        return response.json()


# Example Usage Functions

def example_1_basic_scraping():
    """Example 1: Basic scraping."""
    print("\n" + "="*60)
    print("Example 1: Basic Scraping via API")
    print("="*60)
    
    client = ScraperAPIClient()
    
    # Check health
    health = client.health_check()
    print(f"API Status: {health['status']}")
    
    # Scrape a URL
    result = client.scrape("https://en.wikipedia.org/wiki/Web_scraping")
    
    print(f"\nTitle: {result['data']['metadata']['title']}")
    print(f"Word count: {result['data']['statistics']['clean']['word_count']}")
    print(f"Chunks: {len(result['data']['content'].get('chunks', []))}")


def example_2_simple_text():
    """Example 2: Get just the text."""
    print("\n" + "="*60)
    print("Example 2: Simple Text Extraction")
    print("="*60)
    
    client = ScraperAPIClient()
    
    text = client.scrape_simple("https://en.wikipedia.org/wiki/Python_(programming_language)")
    
    print(f"Extracted {len(text)} characters")
    print(f"\nFirst 300 chars:\n{text[:300]}...")


def example_3_llm_chunks():
    """Example 3: Get chunks for LLM."""
    print("\n" + "="*60)
    print("Example 3: LLM-Ready Chunks")
    print("="*60)
    
    client = ScraperAPIClient()
    
    chunks = client.scrape_chunks(
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        preset="llm",
        chunk_method="token"
    )
    
    print(f"Got {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Length: {chunk['chunk_length']} chars")
        print(f"Preview: {chunk['text'][:150]}...")


def example_4_batch_scraping():
    """Example 4: Batch scraping."""
    print("\n" + "="*60)
    print("Example 4: Batch Scraping")
    print("="*60)
    
    client = ScraperAPIClient()
    
    urls = [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/wiki/JavaScript"
    ]
    
    results = client.scrape_batch(urls, preset="fast")
    
    print(f"Total: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    
    for result in results['results']:
        if result['success']:
            title = result['data']['metadata'].get('title', 'N/A')
            print(f"\n✓ {result['url']}")
            print(f"  Title: {title}")


def example_5_from_another_project():
    """Example 5: Using in another Python project."""
    print("\n" + "="*60)
    print("Example 5: Integration in Another Project")
    print("="*60)
    
    # This is how you'd use it in your RAG pipeline, for example
    
    client = ScraperAPIClient(base_url="http://your-api-url.com")
    
    # Get chunks ready for embedding
    url = "https://example.com/documentation"
    
    try:
        chunks = client.scrape_chunks(url, preset="llm", chunk_method="token")
        
        # Now you can process chunks for your vector database
        for chunk in chunks:
            chunk_text = chunk['text']
            chunk_index = chunk['chunk_index']
            
            # Example: Generate embeddings and store
            # embedding = your_embedding_model.encode(chunk_text)
            # vector_db.store(embedding, chunk_text, metadata={'url': url, 'index': chunk_index})
            
            print(f"Processed chunk {chunk_index}")
        
        print(f"\n✓ Processed {len(chunks)} chunks for embeddings")
        
    except requests.HTTPError as e:
        print(f"✗ API error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


# Plain HTTP examples (for reference)

def example_curl_commands():
    """Example cURL commands for API testing."""
    print("\n" + "="*60)
    print("cURL Examples")
    print("="*60)
    
    examples = """
# Health check
curl http://localhost:8000/health

# Basic scraping
curl -X POST http://localhost:8000/scrape \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://en.wikipedia.org/wiki/Web_scraping",
    "enable_chunking": true,
    "preset": "articles"
  }'

# Simple text extraction
curl -X POST http://localhost:8000/scrape/simple \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://example.com/article"
  }'

# Get chunks only
curl -X POST http://localhost:8000/scrape/chunks \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://example.com/article",
    "preset": "llm",
    "chunk_method": "token"
  }'

# Batch scraping
curl -X POST http://localhost:8000/scrape/batch \\
  -H "Content-Type: application/json" \\
  -d '{
    "urls": [
      "https://example.com/page1",
      "https://example.com/page2"
    ],
    "preset": "fast"
  }'

# Get available presets
curl http://localhost:8000/presets
"""
    print(examples)


def example_javascript_fetch():
    """Example JavaScript/TypeScript client."""
    print("\n" + "="*60)
    print("JavaScript/TypeScript Example")
    print("="*60)
    
    js_code = """
// JavaScript/TypeScript example

const API_BASE_URL = 'http://localhost:8000';

async function scrapeUrl(url, options = {}) {
  const response = await fetch(`${API_BASE_URL}/scrape`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      url,
      enable_chunking: options.enableChunking ?? true,
      preset: options.preset ?? 'default',
      include_metadata: options.includeMetadata ?? true,
      include_statistics: options.includeStatistics ?? true,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  
  return await response.json();
}

// Usage
async function main() {
  try {
    const result = await scrapeUrl('https://example.com/article', {
      preset: 'articles',
      enableChunking: true
    });
    
    console.log('Title:', result.data.metadata.title);
    console.log('Chunks:', result.data.content.chunks.length);
    
    // Use the chunks
    for (const chunk of result.data.content.chunks) {
      console.log(`Chunk ${chunk.chunk_index}:`, chunk.text.substring(0, 100));
    }
  } catch (error) {
    console.error('Scraping failed:', error);
  }
}

main();
"""
    print(js_code)


if __name__ == '__main__':
    print("="*60)
    print("WEB SCRAPING API - CLIENT EXAMPLES")
    print("="*60)
    
    # Check if API is running
    try:
        client = ScraperAPIClient()
        health = client.health_check()
        print(f"\n✓ API is running: {health['status']}")
        print(f"  URL: {API_BASE_URL}")
        print(f"  Version: {health['version']}")
    except Exception as e:
        print(f"\n✗ API is not running at {API_BASE_URL}")
        print(f"  Error: {e}")
        print("\nStart the API with:")
        print("  python api.py")
        print("  or")
        print("  docker-compose up")
        exit(1)
    
    # Run examples
    examples = [
        ("Basic Scraping", example_1_basic_scraping),
        ("Simple Text", example_2_simple_text),
        ("LLM Chunks", example_3_llm_chunks),
        ("Batch Scraping", example_4_batch_scraping),
        ("Integration Example", example_5_from_another_project),
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
        
        input("\nPress Enter to continue...")
    
    # Show other examples
    example_curl_commands()
    input("\nPress Enter to continue...")
    
    example_javascript_fetch()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
