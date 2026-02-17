"""
FastAPI REST API for the Web Scraping Pipeline.
Provides HTTP endpoints for scraping URLs from anywhere.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any, Literal, TypedDict, NotRequired
import uvicorn
import logging
from datetime import datetime, timezone
import os

from main import WebScraper
from scraper.config import ScraperConfig
from utils.exceptions import ScraperError, ValidationError, FetchError, ParseError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Web Scraping API",
    description="Production-ready web scraping pipeline as a service. Fetch, parse, clean, and chunk web content.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class ScrapeRequest(BaseModel):
    """Request model for scraping a URL."""
    url: HttpUrl
    enable_chunking: bool = Field(default=True, description="Whether to chunk the content")
    preset: Optional[Literal["default", "fast", "thorough", "articles", "llm"]] = Field(
        default="default",
        description="Configuration preset to use"
    )
    chunk_size: Optional[int] = Field(default=None, ge=100, le=10000, description="Chunk size (overrides preset)")
    chunk_method: Optional[Literal["character", "word", "sentence", "paragraph", "token"]] = Field(
        default=None,
        description="Chunking method (overrides preset)"
    )
    max_tokens: Optional[int] = Field(default=500, ge=50, le=2000, description="Max tokens per chunk for 'token' method")
    include_metadata: bool = Field(default=True, description="Include metadata in response")
    include_statistics: bool = Field(default=True, description="Include processing statistics")
    
class BatchScrapeRequest(BaseModel):
    """Request model for scraping multiple URLs."""
    urls: List[HttpUrl] = Field(..., min_length=1, max_length=10, description="List of URLs to scrape (max 10)")
    enable_chunking: bool = Field(default=True, description="Whether to chunk the content")
    preset: Optional[Literal["default", "fast", "thorough", "articles", "llm"]] = Field(
        default="fast",
        description="Configuration preset to use"
    )
    
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    url: Optional[str] = None


class BatchResultItem(TypedDict):
    """Single URL result in a batch response."""
    url: str
    success: bool
    data: NotRequired[Dict[str, Any]]
    error: NotRequired[str]


# Helper Functions
def get_config(preset: str, chunk_size: Optional[int] = None, 
               chunk_method: Optional[str] = None, max_tokens: Optional[int] = None) -> ScraperConfig:
    """Create configuration based on preset and overrides."""
    
    # Create config from preset
    if preset == "fast":
        config = ScraperConfig.create_fast()
    elif preset == "thorough":
        config = ScraperConfig.create_thorough()
    elif preset == "articles":
        config = ScraperConfig.create_for_articles()
    elif preset == "llm":
        config = ScraperConfig.create_for_llm(max_tokens=max_tokens or 500)
    else:
        config = ScraperConfig.create_default()
    
    # Apply overrides
    if chunk_size is not None:
        config.chunker.chunk_size = chunk_size
    
    if chunk_method is not None:
        config.chunker.chunking_method = chunk_method
    
    return config


def scrape_single_url(url: str, request: ScrapeRequest) -> Dict[str, Any]:
    """Scrape a single URL."""
    try:
        # Get configuration
        config = get_config(
            request.preset or "default",
            request.chunk_size,
            request.chunk_method,
            request.max_tokens
        )
        
        # Configure output options
        config.parser.extract_metadata = request.include_metadata
        config.include_statistics = request.include_statistics
        
        # Scrape
        with WebScraper(config) as scraper:
            result = scraper.scrape(str(url), enable_chunking=request.enable_chunking)
        
        return {
            "success": True,
            "data": result
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {e.message}")
    except FetchError as e:
        raise HTTPException(status_code=422, detail=f"Failed to fetch URL: {e.message}")
    except ParseError as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse content: {e.message}")
    except ScraperError as e:
        raise HTTPException(status_code=500, detail=f"Scraping error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Web Scraping API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }


@app.post("/scrape", response_model=Dict[str, Any])
async def scrape_url(request: ScrapeRequest) -> Dict[str, Any]:
    """
    Scrape a single URL.
    
    Returns the scraped content with metadata, cleaned text, and optional chunks.
    """
    logger.info(f"Scraping URL: {request.url}")
    result = scrape_single_url(str(request.url), request)
    logger.info(f"Successfully scraped: {request.url}")
    return result


@app.post("/scrape/batch", response_model=Dict[str, Any])
async def scrape_batch(request: BatchScrapeRequest) -> Dict[str, Any]:
    """
    Scrape multiple URLs.
    
    Returns results for each URL, including successes and failures.
    Max 10 URLs per request.
    """
    logger.info(f"Batch scraping {len(request.urls)} URLs")
    
    results: List[BatchResultItem] = []
    
    for url in request.urls:
        try:
            # Create a scrape request for this URL
            single_request = ScrapeRequest(
                url=url,
                enable_chunking=request.enable_chunking,
                preset=request.preset
            )
            
            result = scrape_single_url(str(url), single_request)
            results.append({
                "url": str(url),
                "success": True,
                "data": result["data"]
            })
            
        except HTTPException as e:
            results.append({
                "url": str(url),
                "success": False,
                "error": str(e.detail)
            })
        except Exception as e:
            results.append({
                "url": str(url),
                "success": False,
                "error": str(e)
            })
    
    successful = sum(1 for r in results if r["success"])
    
    logger.info(f"Batch complete: {successful}/{len(request.urls)} successful")
    
    return {
        "total": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results
    }


@app.post("/scrape/simple", response_model=Dict[str, Any])
async def scrape_simple(request: ScrapeRequest) -> Dict[str, Any]:
    """
    Simplified scraping endpoint that returns only the cleaned text.
    
    Useful for quick text extraction without metadata or chunks.
    """
    logger.info(f"Simple scraping: {request.url}")
    
    try:
        config = get_config(request.preset or "default")
        config.parser.extract_metadata = False
        config.include_statistics = False
        
        with WebScraper(config) as scraper:
            result = scraper.scrape(str(request.url), enable_chunking=False)
        
        return {
            "url": str(request.url),
            "text": result["content"]["raw"]
        }
        
    except Exception as e:
        logger.error(f"Error in simple scrape: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/chunks", response_model=Dict[str, Any])
async def scrape_chunks_only(request: ScrapeRequest) -> Dict[str, Any]:
    """
    Scraping endpoint that returns only the chunks.
    
    Useful for LLM/RAG applications that only need chunked content.
    """
    logger.info(f"Chunk-only scraping: {request.url}")
    
    try:
        config = get_config(
            request.preset or "llm",
            request.chunk_size,
            request.chunk_method,
            request.max_tokens
        )
        
        with WebScraper(config) as scraper:
            result = scraper.scrape(str(request.url), enable_chunking=True)
        
        return {
            "url": str(request.url),
            "chunks": result["content"].get("chunks", []),
            "chunk_count": len(result["content"].get("chunks", []))
        }
        
    except Exception as e:
        logger.error(f"Error in chunk scrape: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/presets", response_model=Dict[str, Any])
async def get_presets() -> Dict[str, Any]:
    """
    Get information about available configuration presets.
    """
    return {
        "presets": {
            "default": {
                "description": "Balanced settings for general purpose scraping",
                "use_case": "General web scraping"
            },
            "fast": {
                "description": "Speed optimized with caching and fewer retries",
                "use_case": "Bulk scraping, quick extraction"
            },
            "thorough": {
                "description": "Quality optimized with multiple retries and extraction methods",
                "use_case": "Important content, detailed extraction"
            },
            "articles": {
                "description": "Optimized for blog posts and news articles",
                "use_case": "Articles, blog posts, news"
            },
            "llm": {
                "description": "Token-based chunking for LLM/RAG systems",
                "use_case": "Vector databases, embeddings, LLM training"
            }
        }
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(status_code=exc.status_code, content={
        "error": str(exc.detail),
        "status_code": int(exc.status_code)
    })


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={
        "error": "Internal server error",
        "detail": str(exc)
    })


# Run server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Web Scraping API on {host}:{port}")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=os.getenv("ENV", "production") == "development",
        log_level="info"
    )
