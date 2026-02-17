"""
Web Scraper Package
A production-ready web scraping pipeline for extracting, cleaning, and chunking web content.
"""

from .fetcher import ContentFetcher
from .parser import ContentParser
from .cleaner import ContentCleaner
from .chunker import ContentChunker
from .config import ScraperConfig

__version__ = "1.0.0"
__all__ = [
    "ContentFetcher",
    "ContentParser",
    "ContentCleaner",
    "ContentChunker",
    "ScraperConfig",
]
