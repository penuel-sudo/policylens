"""
Main web scraping pipeline.
Orchestrates the complete scraping workflow from URL to cleaned, chunked content.
"""

import logging
import json
from typing import Optional, Dict, Any, Union
from datetime import datetime

from scraper.config import ScraperConfig
from scraper.fetcher import ContentFetcher
from scraper.parser import ContentParser
from scraper.cleaner import ContentCleaner
from scraper.chunker import ContentChunker
from utils.exceptions import ScraperError
from utils.validators import URLValidator


# Configure logging
def setup_logging(config: ScraperConfig):
    """Setup logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler (if configured)
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=log_format,
        handlers=handlers
    )
    
    # Try to use colored logs if enabled
    if config.enable_colored_logs:
        try:
            import coloredlogs
            coloredlogs.install(
                level=config.log_level.upper(),
                fmt=log_format
            )
        except ImportError:
            pass


class WebScraper:
    """
    Complete web scraping pipeline.
    
    Handles fetching, parsing, cleaning, and chunking of web content.
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        """
        Initialize WebScraper.
        
        Args:
            config: Scraper configuration (uses defaults if None)
        """
        self.config = config or ScraperConfig.create_default()
        
        # Validate configuration
        self.config.validate()
        
        # Setup logging
        setup_logging(self.config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.fetcher = ContentFetcher(self.config.fetcher)
        self.parser = ContentParser(self.config.parser)
        self.cleaner = ContentCleaner(self.config.cleaner)
        self.chunker = ContentChunker(self.config.chunker)
        
        self.logger.info("WebScraper initialized")
    
    def scrape(self, url: str, enable_chunking: bool = True) -> Dict[str, Any]:
        """
        Scrape content from URL.
        
        Args:
            url: URL to scrape
            enable_chunking: Whether to chunk the content
            
        Returns:
            Dictionary containing:
                - url: Final URL (after redirects)
                - metadata: Extracted metadata
                - content: Main content
                    - raw: Cleaned full text
                    - chunks: List of chunks (if chunking enabled)
                - statistics: Processing statistics
                - timestamp: When the scrape was performed
                
        Raises:
            ValidationError: If URL is invalid
            ScraperError: If scraping fails
        """
        start_time = datetime.now()
        
        self.logger.info(f"Starting scrape of: {url}")
        
        # Track timing for each stage
        timings = {}
        
        try:
            # Stage 1: Fetch
            self.logger.info("Stage 1/4: Fetching content...")
            fetch_result = self.fetcher.fetch(url)
            timings['fetch'] = fetch_result['fetch_time']
            
            # Stage 2: Parse
            self.logger.info("Stage 2/4: Parsing HTML...")
            parse_result = self.parser.parse(
                fetch_result['html'],
                url=fetch_result['url']
            )
            timings['parse'] = parse_result['parse_time']
            
            # Stage 3: Clean
            self.logger.info("Stage 3/4: Cleaning content...")
            clean_result = self.cleaner.clean(
                parse_result['content'],
                url=fetch_result['url']
            )
            timings['clean'] = clean_result['clean_time']
            
            # Stage 4: Chunk (optional)
            chunk_result = None
            if enable_chunking:
                self.logger.info("Stage 4/4: Chunking content...")
                chunk_result = self.chunker.chunk(
                    clean_result['content'],
                    url=fetch_result['url']
                )
                timings['chunk'] = chunk_result['chunk_time']
            else:
                self.logger.info("Stage 4/4: Skipped (chunking disabled)")
                timings['chunk'] = 0
            
            # Build result
            result = {
                'url': fetch_result['url'],
                'original_url': url,
                'metadata': parse_result['metadata'],
                'content': {
                    'raw': clean_result['content'],
                },
                'timestamp': start_time.isoformat(),
            }
            
            # Add chunks if enabled
            if chunk_result:
                result['content']['chunks'] = chunk_result['chunks']
            
            # Add statistics if enabled
            if self.config.include_statistics:
                total_time = sum(timings.values())
                result['statistics'] = {
                    'fetch': {
                        'status_code': fetch_result['status_code'],
                        'content_type': fetch_result['content_type'],
                        'encoding': fetch_result['encoding'],
                        'time': timings['fetch'],
                    },
                    'parse': {
                        'extraction_method': parse_result['extraction_method'],
                        'language': parse_result.get('language'),
                        'time': timings['parse'],
                    },
                    'clean': {
                        'original_length': clean_result['original_length'],
                        'cleaned_length': clean_result['cleaned_length'],
                        'reduction_percent': clean_result['reduction_percent'],
                        'word_count': clean_result['word_count'],
                        'time': timings['clean'],
                    },
                    'timing': {
                        **timings,
                        'total': total_time,
                    },
                }
                
                if chunk_result:
                    result['statistics']['chunk'] = {
                        'chunk_count': chunk_result['chunk_count'],
                        'chunking_method': chunk_result['chunking_method'],
                        'chunk_size': chunk_result['chunk_size'],
                        'overlap': chunk_result['overlap'],
                        'average_chunk_length': chunk_result['average_chunk_length'],
                        'time': timings['chunk'],
                    }
            
            # Add raw HTML if configured
            if self.config.include_raw_html:
                result['raw_html'] = fetch_result['html']
            
            self.logger.info(
                f"Successfully scraped {url} in {sum(timings.values()):.2f}s"
            )
            
            # Return in requested format
            if self.config.output_format == 'json':
                return json.dumps(result, indent=2, ensure_ascii=False)
            else:
                return result
                
        except ScraperError as e:
            self.logger.error(f"Scraping failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            raise ScraperError(
                f"Unexpected error during scraping: {str(e)}",
                url=url,
                details={'error': str(e), 'type': type(e).__name__}
            )
    
    def scrape_url_simple(self, url: str) -> str:
        """
        Simple scraping that returns just the cleaned text.
        
        Args:
            url: URL to scrape
            
        Returns:
            Cleaned text content
        """
        result = self.scrape(url, enable_chunking=False)
        return result['content']['raw']
    
    def scrape_url_chunks(self, url: str) -> list:
        """
        Scraping that returns just the chunks.
        
        Args:
            url: URL to scrape
            
        Returns:
            List of chunk dictionaries
        """
        result = self.scrape(url, enable_chunking=True)
        return result['content'].get('chunks', [])
    
    def close(self):
        """Close resources and cleanup."""
        if self.fetcher:
            self.fetcher.close()
        self.logger.info("WebScraper closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def scrape_url(
    url: str,
    config: Optional[ScraperConfig] = None,
    enable_chunking: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to scrape a single URL.
    
    Args:
        url: URL to scrape
        config: Scraper configuration (uses defaults if None)
        enable_chunking: Whether to chunk the content
        
    Returns:
        Scraping result dictionary
    """
    with WebScraper(config) as scraper:
        return scraper.scrape(url, enable_chunking=enable_chunking)


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Web Scraping Pipeline - Extract and clean content from URLs'
    )
    parser.add_argument('url', help='URL to scrape')
    parser.add_argument(
        '--no-chunks',
        action='store_true',
        help='Disable content chunking'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Chunk size (default: 1000)'
    )
    parser.add_argument(
        '--chunk-method',
        choices=['character', 'word', 'sentence', 'paragraph', 'token'],
        default='paragraph',
        help='Chunking method (default: paragraph)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file (default: print to stdout)'
    )
    parser.add_argument(
        '--format',
        choices=['dict', 'json'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--preset',
        choices=['default', 'fast', 'thorough', 'articles', 'llm'],
        default='default',
        help='Configuration preset (default: default)'
    )
    
    args = parser.parse_args()
    
    # Create configuration based on preset
    if args.preset == 'fast':
        config = ScraperConfig.create_fast()
    elif args.preset == 'thorough':
        config = ScraperConfig.create_thorough()
    elif args.preset == 'articles':
        config = ScraperConfig.create_for_articles()
    elif args.preset == 'llm':
        config = ScraperConfig.create_for_llm()
    else:
        config = ScraperConfig.create_default()
    
    # Apply custom settings
    config.log_level = args.log_level
    config.output_format = args.format
    config.chunker.chunk_size = args.chunk_size
    config.chunker.chunking_method = args.chunk_method
    
    try:
        # Scrape URL
        result = scrape_url(
            args.url,
            config=config,
            enable_chunking=not args.no_chunks
        )
        
        # Format output
        if args.format == 'json':
            if isinstance(result, str):
                output = result
            else:
                output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            output = str(result)
        
        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Output written to: {args.output}")
        else:
            print(output)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=__import__('sys').stderr)
        return 1


if __name__ == '__main__':
    exit(main())
