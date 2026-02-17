"""
Example usage scripts for the web scraping pipeline.
Demonstrates various use cases and configurations.
"""

from main import WebScraper, scrape_url
from scraper.config import ScraperConfig


def example_1_basic_scraping():
    """Example 1: Basic web scraping with default settings."""
    print("\n" + "="*60)
    print("Example 1: Basic Web Scraping")
    print("="*60)
    
    url = "https://en.wikipedia.org/wiki/Web_scraping"
    
    with WebScraper() as scraper:
        result = scraper.scrape(url)
        
        print(f"\nURL: {result['url']}")
        print(f"Title: {result['metadata'].get('title', 'N/A')}")
        print(f"Language: {result['metadata'].get('language', 'N/A')}")
        print(f"\nContent length: {len(result['content']['raw'])} characters")
        print(f"Word count: {result['statistics']['clean']['word_count']}")
        print(f"Number of chunks: {len(result['content'].get('chunks', []))}")
        
        # Print first 500 characters
        print(f"\nFirst 500 characters:")
        print(result['content']['raw'][:500])
        print("...")
        
        # Print timing statistics
        print(f"\nTiming:")
        for stage, time in result['statistics']['timing'].items():
            print(f"  {stage}: {time:.2f}s")


def example_2_simple_text_extraction():
    """Example 2: Extract just the cleaned text without chunking."""
    print("\n" + "="*60)
    print("Example 2: Simple Text Extraction")
    print("="*60)
    
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    
    with WebScraper() as scraper:
        # Use convenience method to get just the text
        text = scraper.scrape_url_simple(url)
        
        print(f"\nExtracted {len(text)} characters of text")
        print(f"\nFirst 300 characters:")
        print(text[:300])
        print("...")


def example_3_chunk_for_llm():
    """Example 3: Prepare content for LLM/RAG systems."""
    print("\n" + "="*60)
    print("Example 3: LLM-Ready Chunking")
    print("="*60)
    
    url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    
    # Use LLM-optimized configuration
    config = ScraperConfig.create_for_llm(max_tokens=300)
    
    with WebScraper(config) as scraper:
        chunks = scraper.scrape_url_chunks(url)
        
        print(f"\nExtracted {len(chunks)} chunks")
        print(f"\nFirst 3 chunks:")
        
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Index: {chunk['chunk_index']}/{chunk['total_chunks']}")
            print(f"Length: {chunk['chunk_length']} chars")
            print(f"Words: {chunk['word_count']}")
            print(f"Text preview: {chunk['text'][:200]}...")


def example_4_article_extraction():
    """Example 4: Extract article content with metadata."""
    print("\n" + "="*60)
    print("Example 4: Article Extraction")
    print("="*60)
    
    # Example blog post / article URL
    url = "https://en.wikipedia.org/wiki/Machine_learning"
    
    config = ScraperConfig.create_for_articles()
    
    with WebScraper(config) as scraper:
        result = scraper.scrape(url)
        
        print(f"\nArticle Metadata:")
        print(f"  Title: {result['metadata'].get('title', 'N/A')}")
        print(f"  Author: {result['metadata'].get('author', 'N/A')}")
        print(f"  Date: {result['metadata'].get('date', 'N/A')}")
        print(f"  Description: {result['metadata'].get('description', 'N/A')}")
        print(f"  Language: {result['metadata'].get('language', 'N/A')}")
        
        print(f"\nContent Stats:")
        print(f"  Words: {result['statistics']['clean']['word_count']}")
        print(f"  Chunks: {len(result['content']['chunks'])}")
        print(f"  Extraction method: {result['statistics']['parse']['extraction_method']}")
        
        # Show first chunk (usually the introduction)
        if result['content']['chunks']:
            first_chunk = result['content']['chunks'][0]
            print(f"\nIntroduction:")
            print(first_chunk['text'][:400])
            print("...")


def example_5_custom_configuration():
    """Example 5: Custom configuration for specific needs."""
    print("\n" + "="*60)
    print("Example 5: Custom Configuration")
    print("="*60)
    
    url = "https://en.wikipedia.org/wiki/Natural_language_processing"
    
    # Create custom configuration
    config = ScraperConfig()
    
    # Custom fetcher settings
    config.fetcher.max_retries = 5
    config.fetcher.read_timeout = 60.0
    config.fetcher.rate_limit_delay = 1.0  # Be nice to servers
    
    # Custom parser settings
    config.parser.extraction_methods = ['trafilatura']  # Only use trafilatura
    config.parser.extract_metadata = True
    
    # Custom cleaner settings
    config.cleaner.remove_urls = True
    config.cleaner.normalize_unicode = True
    config.cleaner.min_word_count = 100  # Require at least 100 words
    
    # Custom chunker settings
    config.chunker.chunking_method = 'paragraph'
    config.chunker.chunk_size = 1500
    config.chunker.chunk_overlap = 150
    config.chunker.preserve_paragraphs = True
    
    with WebScraper(config) as scraper:
        result = scraper.scrape(url)
        
        print(f"\nConfiguration used:")
        print(f"  Extraction method: {result['statistics']['parse']['extraction_method']}")
        print(f"  Chunking method: {result['statistics']['chunk']['chunking_method']}")
        print(f"  Chunk size: {result['statistics']['chunk']['chunk_size']}")
        print(f"  Overlap: {result['statistics']['chunk']['overlap']}")
        
        print(f"\nResults:")
        print(f"  Total words: {result['statistics']['clean']['word_count']}")
        print(f"  Total chunks: {result['statistics']['chunk']['chunk_count']}")
        print(f"  Avg chunk length: {result['statistics']['chunk']['average_chunk_length']:.0f}")
        
        print(f"\nChunk sizes:")
        for chunk in result['content']['chunks'][:5]:
            print(f"  Chunk {chunk['chunk_index']}: {chunk['chunk_length']} chars, {chunk['word_count']} words")


def example_6_error_handling():
    """Example 6: Proper error handling."""
    print("\n" + "="*60)
    print("Example 6: Error Handling")
    print("="*60)
    
    from utils.exceptions import (
        FetchError,
        ParseError,
        ValidationError,
        RobotsDisallowedError,
    )
    
    urls = [
        "https://en.wikipedia.org/wiki/Web_scraping",  # Valid
        "https://thissitedoesnotexist12345.com",       # Invalid domain
        "not-a-url",                                   # Invalid format
    ]
    
    with WebScraper() as scraper:
        for url in urls:
            print(f"\nTrying: {url}")
            try:
                result = scraper.scrape(url, enable_chunking=False)
                print(f"  ✓ Success! Got {result['statistics']['clean']['word_count']} words")
                
            except ValidationError as e:
                print(f"  ✗ Invalid URL: {e.message}")
                
            except FetchError as e:
                print(f"  ✗ Fetch failed: {e.message}")
                if hasattr(e, 'status_code') and e.status_code:
                    print(f"    Status code: {e.status_code}")
                    
            except ParseError as e:
                print(f"  ✗ Parse failed: {e.message}")
                
            except RobotsDisallowedError as e:
                print(f"  ✗ Blocked by robots.txt")
                
            except Exception as e:
                print(f"  ✗ Unexpected error: {e}")


def example_7_batch_scraping():
    """Example 7: Scrape multiple URLs efficiently."""
    print("\n" + "="*60)
    print("Example 7: Batch Scraping")
    print("="*60)
    
    urls = [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/wiki/JavaScript",
        "https://en.wikipedia.org/wiki/Java_(programming_language)",
    ]
    
    # Fast configuration for batch scraping
    config = ScraperConfig.create_fast()
    config.fetcher.rate_limit_delay = 0.5  # Be respectful
    
    results = []
    
    with WebScraper(config) as scraper:
        print(f"\nScraping {len(urls)} URLs...")
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"\n[{i}/{len(urls)}] Scraping: {url}")
                result = scraper.scrape(url, enable_chunking=False)
                
                results.append({
                    'url': url,
                    'title': result['metadata'].get('title', 'N/A'),
                    'word_count': result['statistics']['clean']['word_count'],
                    'fetch_time': result['statistics']['timing']['total'],
                })
                
                print(f"  ✓ Success! {result['statistics']['clean']['word_count']} words in {result['statistics']['timing']['total']:.2f}s")
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                results.append({
                    'url': url,
                    'error': str(e)
                })
    
    # Summary
    print("\n" + "-"*60)
    print("Summary:")
    print("-"*60)
    
    successful = [r for r in results if 'word_count' in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"\nSuccessful: {len(successful)}/{len(urls)}")
    if successful:
        total_words = sum(r['word_count'] for r in successful)
        total_time = sum(r['fetch_time'] for r in successful)
        print(f"Total words extracted: {total_words:,}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average speed: {total_words/total_time:.0f} words/second")
    
    if failed:
        print(f"\nFailed: {len(failed)}")
        for r in failed:
            print(f"  - {r['url']}: {r['error']}")


def example_8_different_chunking_methods():
    """Example 8: Compare different chunking methods."""
    print("\n" + "="*60)
    print("Example 8: Different Chunking Methods")
    print("="*60)
    
    url = "https://en.wikipedia.org/wiki/Algorithm"
    
    chunking_methods = [
        ('character', 1000),
        ('word', 200),
        ('sentence', 1000),
        ('paragraph', 1500),
    ]
    
    for method, size in chunking_methods:
        print(f"\n--- Chunking Method: {method.upper()} (size={size}) ---")
        
        config = ScraperConfig()
        config.chunker.chunking_method = method
        config.chunker.chunk_size = size
        config.chunker.chunk_overlap = int(size * 0.1)
        
        with WebScraper(config) as scraper:
            result = scraper.scrape(url)
            
            chunks = result['content']['chunks']
            print(f"Total chunks: {len(chunks)}")
            print(f"Average chunk length: {result['statistics']['chunk']['average_chunk_length']:.0f} chars")
            
            # Show first chunk
            if chunks:
                first_chunk = chunks[0]
                print(f"\nFirst chunk preview ({first_chunk['chunk_length']} chars):")
                print(first_chunk['text'][:200] + "...")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("WEB SCRAPING PIPELINE - EXAMPLE USAGE")
    print("="*60)
    
    examples = [
        ("Basic Scraping", example_1_basic_scraping),
        ("Simple Text Extraction", example_2_simple_text_extraction),
        ("LLM Chunking", example_3_chunk_for_llm),
        ("Article Extraction", example_4_article_extraction),
        ("Custom Configuration", example_5_custom_configuration),
        ("Error Handling", example_6_error_handling),
        ("Batch Scraping", example_7_batch_scraping),
        ("Chunking Methods", example_8_different_chunking_methods),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "="*60)
    
    # Run each example
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-"*60)
        input("Press Enter to continue to next example...")
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == '__main__':
    main()
