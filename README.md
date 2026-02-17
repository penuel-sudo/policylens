# Web Scraping Pipeline

A production-ready Python web scraping pipeline that fetches, parses, cleans, and chunks web content. Built with robust error handling, multiple extraction strategies, and flexible configuration options.

## Features

✨ **Complete Pipeline**
- HTTP fetching with retry logic and rate limiting
- Multiple content extraction methods (Trafilatura, Readability, custom)
- Advanced text cleaning and normalization
- Flexible chunking strategies (character, word, sentence, paragraph, token-based)

🛡️ **Robust & Respectful**
- Respects `robots.txt`
- Configurable rate limiting
- User agent rotation
- Retry with exponential backoff
- SSL verification

🎯 **Intelligent Extraction**
- Automatic fallback between extraction methods
- Metadata extraction (title, author, date, etc.)
- Language detection
- Error page detection

🔧 **Highly Configurable**
- Multiple configuration presets (fast, thorough, articles, LLM)
- Granular control over each pipeline stage
- Support for different chunking methods
- Token-based chunking for LLMs (using tiktoken)

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Download NLTK data (required for sentence tokenization):**
```python
python -c "import nltk; nltk.download('punkt')"
```

## Quick Start

### Basic Usage

```python
from main import WebScraper

# Create scraper with default settings
scraper = WebScraper()

# Scrape a URL
result = scraper.scrape('https://example.com/article')

# Access the content
print(result['content']['raw'])  # Full cleaned text

# Access chunks (if enabled)
for chunk in result['content']['chunks']:
    print(f"Chunk {chunk['chunk_index']}: {chunk['text'][:100]}...")

# Access metadata
print(result['metadata']['title'])
print(result['metadata']['author'])

scraper.close()
```

### Using Context Manager (Recommended)

```python
from main import WebScraper

with WebScraper() as scraper:
    result = scraper.scrape('https://example.com/article')
    print(result['content']['raw'])
```

### Simple Functions

```python
from main import scrape_url

# Get full result
result = scrape_url('https://example.com/article')

# Or use the scraper's convenience methods
from main import WebScraper

with WebScraper() as scraper:
    # Get just the text
    text = scraper.scrape_url_simple('https://example.com')
    
    # Get just the chunks
    chunks = scraper.scrape_url_chunks('https://example.com')
```

## Configuration Presets

### Default Configuration
```python
from scraper.config import ScraperConfig
from main import WebScraper

config = ScraperConfig.create_default()
scraper = WebScraper(config)
```

### Fast Scraping (Speed Optimized)
```python
config = ScraperConfig.create_fast()
# - Fewer retries
# - Single extraction method
# - No robots.txt checking
# - Caching enabled
```

### Thorough Scraping (Quality Optimized)
```python
config = ScraperConfig.create_thorough()
# - More retries
# - Multiple extraction methods with fallbacks
# - Full metadata extraction
# - Unicode normalization
```

### Article Extraction
```python
config = ScraperConfig.create_for_articles()
# - Optimized for blog posts and articles
# - Keeps paragraph structure
# - Extracts full metadata
```

### LLM-Ready Content
```python
config = ScraperConfig.create_for_llm(max_tokens=500)
# - Token-based chunking
# - Removes URLs and extra formatting
# - Preserves sentence boundaries
# - Optimized for language models
```

## Advanced Configuration

### Custom Configuration

```python
from scraper.config import ScraperConfig, FetcherConfig, ParserConfig, CleanerConfig, ChunkerConfig

# Create custom configuration
config = ScraperConfig()

# Configure fetcher
config.fetcher.max_retries = 5
config.fetcher.read_timeout = 60.0
config.fetcher.respect_robots_txt = True
config.fetcher.rate_limit_delay = 1.0  # 1 second between requests

# Configure parser
config.parser.extraction_methods = ['trafilatura', 'readability']
config.parser.extract_metadata = True

# Configure cleaner
config.cleaner.remove_urls = True
config.cleaner.normalize_whitespace = True
config.cleaner.min_word_count = 50

# Configure chunker
config.chunker.chunking_method = 'paragraph'
config.chunker.chunk_size = 1000
config.chunker.chunk_overlap = 100
config.chunker.preserve_paragraphs = True

scraper = WebScraper(config)
```

### Chunking Methods

```python
# Character-based chunking
config.chunker.chunking_method = 'character'
config.chunker.chunk_size = 1000  # 1000 characters per chunk

# Word-based chunking
config.chunker.chunking_method = 'word'
config.chunker.chunk_size = 200  # 200 words per chunk

# Sentence-based chunking
config.chunker.chunking_method = 'sentence'
config.chunker.chunk_size = 1000  # Group sentences up to 1000 chars

# Paragraph-based chunking (best for preserving structure)
config.chunker.chunking_method = 'paragraph'
config.chunker.chunk_size = 1500
config.chunker.preserve_paragraphs = True

# Token-based chunking (for LLMs)
config.chunker.chunking_method = 'token'
config.chunker.max_tokens_per_chunk = 500
```

## Command-Line Usage

```bash
# Basic scraping
python main.py https://example.com/article

# With custom options
python main.py https://example.com/article \
    --chunk-method paragraph \
    --chunk-size 1000 \
    --output result.json \
    --format json \
    --log-level INFO

# Using presets
python main.py https://example.com/article --preset articles
python main.py https://example.com/article --preset llm

# Disable chunking
python main.py https://example.com/article --no-chunks

# Save to file
python main.py https://example.com/article -o output.json
```

### Command-Line Options

- `url` - URL to scrape (required)
- `--no-chunks` - Disable content chunking
- `--chunk-size SIZE` - Chunk size (default: 1000)
- `--chunk-method METHOD` - Chunking method: character, word, sentence, paragraph, token
- `--output FILE` - Output file path
- `--format FORMAT` - Output format: dict, json (default: json)
- `--log-level LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR
- `--preset PRESET` - Configuration preset: default, fast, thorough, articles, llm

## Result Structure

```python
{
    "url": "https://example.com/article",  # Final URL after redirects
    "original_url": "https://example.com/article",
    "metadata": {
        "title": "Article Title",
        "author": "Author Name",
        "date": "2024-01-15",
        "description": "Article description",
        "language": "en",
        "keywords": "keyword1, keyword2"
    },
    "content": {
        "raw": "Full cleaned text content...",
        "chunks": [
            {
                "text": "First chunk text...",
                "chunk_index": 0,
                "total_chunks": 5,
                "chunk_length": 1234,
                "word_count": 200,
                "is_first": true,
                "is_last": false
            },
            # ... more chunks
        ]
    },
    "statistics": {
        "fetch": {
            "status_code": 200,
            "content_type": "text/html",
            "time": 0.52
        },
        "parse": {
            "extraction_method": "trafilatura",
            "language": "en",
            "time": 0.15
        },
        "clean": {
            "original_length": 50000,
            "cleaned_length": 45000,
            "reduction_percent": 10.0,
            "word_count": 7500,
            "time": 0.08
        },
        "chunk": {
            "chunk_count": 5,
            "chunking_method": "paragraph",
            "average_chunk_length": 1200,
            "time": 0.03
        },
        "timing": {
            "fetch": 0.52,
            "parse": 0.15,
            "clean": 0.08,
            "chunk": 0.03,
            "total": 0.78
        }
    },
    "timestamp": "2024-01-15T10:30:00.000000"
}
```

## Error Handling

The pipeline includes comprehensive error handling:

```python
from main import WebScraper
from utils.exceptions import (
    FetchError,
    ParseError,
    CleaningError,
    ChunkingError,
    ValidationError,
    RateLimitError,
    RobotsDisallowedError
)

try:
    with WebScraper() as scraper:
        result = scraper.scrape('https://example.com')
except ValidationError as e:
    print(f"Invalid URL: {e}")
except RobotsDisallowedError as e:
    print(f"Blocked by robots.txt: {e}")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except FetchError as e:
    print(f"Failed to fetch: {e}")
except ParseError as e:
    print(f"Failed to parse: {e}")
except CleaningError as e:
    print(f"Failed to clean: {e}")
except ChunkingError as e:
    print(f"Failed to chunk: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Examples

### Example 1: Scrape Multiple URLs

```python
from main import WebScraper

urls = [
    'https://example.com/article1',
    'https://example.com/article2',
    'https://example.com/article3',
]

with WebScraper() as scraper:
    for url in urls:
        try:
            result = scraper.scrape(url)
            print(f"Scraped: {result['metadata']['title']}")
            print(f"Words: {result['statistics']['clean']['word_count']}")
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
```

### Example 2: Extract Only Main Text

```python
from main import WebScraper
from scraper.config import ScraperConfig

# Configure to skip chunking and metadata
config = ScraperConfig()
config.parser.extract_metadata = False
config.include_statistics = False

with WebScraper(config) as scraper:
    result = scraper.scrape('https://example.com', enable_chunking=False)
    text = result['content']['raw']
    print(text)
```

### Example 3: Prepare Content for RAG/LLM

```python
from main import WebScraper
from scraper.config import ScraperConfig

# LLM-optimized configuration
config = ScraperConfig.create_for_llm(max_tokens=500)

with WebScraper(config) as scraper:
    result = scraper.scrape('https://example.com/article')
    
    # Get chunks ready for embedding/processing
    for chunk in result['content']['chunks']:
        chunk_text = chunk['text']
        chunk_index = chunk['chunk_index']
        
        # Process with your LLM/embedding model
        print(f"Processing chunk {chunk_index}...")
        # embedding = embed_model.encode(chunk_text)
        # store_in_vector_db(embedding, chunk_text, metadata)
```

### Example 4: Custom Cleaning Pipeline

```python
from scraper.config import ScraperConfig

config = ScraperConfig()

# Aggressive cleaning
config.cleaner.remove_urls = True
config.cleaner.remove_emails = True
config.cleaner.remove_phone_numbers = True
config.cleaner.convert_to_lowercase = True
config.cleaner.normalize_unicode = True

# Strict content requirements
config.cleaner.min_content_length = 200
config.cleaner.min_word_count = 50

with WebScraper(config) as scraper:
    result = scraper.scrape('https://example.com')
    clean_text = result['content']['raw']
```

## Project Structure

```
PolicyLens/
├── scraper/
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Configuration classes
│   ├── fetcher.py          # HTTP fetching logic
│   ├── parser.py           # HTML parsing and extraction
│   ├── cleaner.py          # Text cleaning and normalization
│   └── chunker.py          # Text chunking strategies
├── utils/
│   ├── __init__.py         # Utility package initialization
│   ├── exceptions.py       # Custom exception classes
│   └── validators.py       # Validation utilities
├── main.py                 # Main pipeline and CLI
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Dependencies

Core dependencies:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast XML/HTML processing
- `trafilatura` - Main content extraction
- `readability-lxml` - Alternative extraction
- `html2text` - HTML to text conversion
- `langdetect` - Language detection
- `nltk` - Sentence tokenization
- `tiktoken` - Token counting for LLMs
- `fake-useragent` - User agent rotation

## Logging

Configure logging levels:

```python
from scraper.config import ScraperConfig

config = ScraperConfig()
config.log_level = 'DEBUG'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
config.log_file = 'scraper.log'  # Optional file output
config.enable_colored_logs = True  # Colored console output

scraper = WebScraper(config)
```

## Performance Tips

1. **Use caching for repeated scraping:**
```python
config.fetcher.enable_cache = True
config.fetcher.cache_expire_after = 3600
```

2. **Adjust timeouts for slow sites:**
```python
config.fetcher.connect_timeout = 15.0
config.fetcher.read_timeout = 60.0
```

3. **Use fast preset for bulk scraping:**
```python
config = ScraperConfig.create_fast()
```

4. **Disable features you don't need:**
```python
config.parser.extract_metadata = False
config.include_statistics = False
config.enable_performance_metrics = False
```

## Limitations

- Requires JavaScript-free content (use Selenium/Playwright for JS-heavy sites)
- Respects robots.txt by default (can be disabled if needed)
- May not work with heavily obfuscated HTML
- Rate limiting is basic (consider using advanced rate limiting libraries for production)

## License

This project is provided as-is for educational and commercial use.

## Contributing

Contributions welcome! Areas for improvement:
- JavaScript rendering support (Selenium/Playwright integration)
- Advanced rate limiting strategies
- More extraction methods
- Better error recovery
- Async/batch processing support

## Troubleshooting

**Issue: NLTK punkt tokenizer not found**
```python
import nltk
nltk.download('punkt')
```

**Issue: SSL certificate verification fails**
```python
config.fetcher.verify_ssl = False
```

**Issue: Content too short errors**
```python
config.cleaner.min_content_length = 10
config.cleaner.min_word_count = 5
```

**Issue: Rate limiting / 429 errors**
```python
config.fetcher.rate_limit_delay = 2.0  # 2 seconds between requests
```

## Support

For issues, questions, or contributions, please refer to the project documentation or create an issue in the repository.
