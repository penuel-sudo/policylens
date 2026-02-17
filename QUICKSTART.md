# Quick Start Guide

## Installation & Setup

### Step 1: Install Dependencies

Open a terminal in the project directory and run:

```bash
pip install -r requirements.txt
```

This will install all required packages:
- requests (HTTP requests)
- beautifulsoup4 (HTML parsing)
- lxml (Fast parser)
- trafilatura (Content extraction)
- readability-lxml (Alternative extraction)
- html2text (HTML to text)
- langdetect (Language detection)
- nltk (Sentence tokenization)
- tiktoken (Token counting)
- fake-useragent (User agent rotation)
- And more...

### Step 2: Download NLTK Data

After installing dependencies, download the NLTK punkt tokenizer:

```bash
python -c "import nltk; nltk.download('punkt')"
```

### Step 3: Test the Installation

Try a simple scrape:

```bash
python main.py https://en.wikipedia.org/wiki/Web_scraping
```

You should see JSON output with the scraped content.

## Basic Usage

### 1. Command Line

Scrape a URL from the command line:

```bash
# Basic scraping
python main.py https://example.com/article

# Save to file
python main.py https://example.com/article -o output.json

# Use different presets
python main.py https://example.com/article --preset articles
python main.py https://example.com/article --preset llm

# Custom chunk size
python main.py https://example.com/article --chunk-size 500 --chunk-method paragraph
```

### 2. Python Script

Create a file `test_scraper.py`:

```python
from main import WebScraper

# Simple usage
with WebScraper() as scraper:
    result = scraper.scrape('https://en.wikipedia.org/wiki/Python_(programming_language)')
    
    # Print title
    print(f"Title: {result['metadata']['title']}")
    
    # Print word count
    print(f"Words: {result['statistics']['clean']['word_count']}")
    
    # Print first chunk
    if result['content']['chunks']:
        first_chunk = result['content']['chunks'][0]
        print(f"\nFirst chunk:\n{first_chunk['text'][:300]}...")
```

Run it:

```bash
python test_scraper.py
```

### 3. Run Examples

The project includes comprehensive examples:

```bash
python examples.py
```

This will run through 8 different example scenarios showing various features.

## Common Use Cases

### Extract Just Text (No Chunking)

```python
from main import WebScraper

with WebScraper() as scraper:
    text = scraper.scrape_url_simple('https://example.com/article')
    print(text)
```

### Get Chunks for LLM/RAG

```python
from main import WebScraper
from scraper.config import ScraperConfig

config = ScraperConfig.create_for_llm(max_tokens=500)

with WebScraper(config) as scraper:
    chunks = scraper.scrape_url_chunks('https://example.com/article')
    
    for chunk in chunks:
        print(f"Chunk {chunk['chunk_index']}: {chunk['word_count']} words")
        # Process chunk for embedding, etc.
```

### Batch Scraping

```python
from main import WebScraper
from scraper.config import ScraperConfig

urls = [
    'https://example.com/page1',
    'https://example.com/page2',
    'https://example.com/page3',
]

config = ScraperConfig.create_fast()
config.fetcher.rate_limit_delay = 1.0  # Be respectful

with WebScraper(config) as scraper:
    for url in urls:
        try:
            result = scraper.scrape(url)
            print(f"✓ Scraped: {result['metadata']['title']}")
        except Exception as e:
            print(f"✗ Failed {url}: {e}")
```

## Configuration Presets

Choose the right preset for your use case:

| Preset | Use Case | Command |
|--------|----------|---------|
| `default` | General purpose | `--preset default` |
| `fast` | Speed over quality, bulk scraping | `--preset fast` |
| `thorough` | Quality over speed, important content | `--preset thorough` |
| `articles` | Blog posts, news articles | `--preset articles` |
| `llm` | Preparing content for LLM/RAG | `--preset llm` |

Example:
```bash
python main.py https://example.com/blog-post --preset articles -o article.json
```

## Troubleshooting

### Issue: Module not found errors

**Solution:** Make sure you installed dependencies:
```bash
pip install -r requirements.txt
```

### Issue: NLTK punkt tokenizer error

**Solution:** Download the tokenizer:
```bash
python -c "import nltk; nltk.download('punkt')"
```

### Issue: SSL certificate verification fails

**Solution:** Disable SSL verification in your script:
```python
config.fetcher.verify_ssl = False
```

### Issue: Content too short errors

**Solution:** Lower the minimum requirements:
```python
config.cleaner.min_content_length = 10
config.cleaner.min_word_count = 5
```

### Issue: Rate limiting (429 errors)

**Solution:** Add rate limiting delay:
```python
config.fetcher.rate_limit_delay = 2.0  # 2 seconds between requests
```

Or from command line:
```python
# Edit the config in main.py or create custom script
```

### Issue: Blocked by robots.txt

**Solution:** Disable robots.txt checking (use responsibly):
```python
config.fetcher.respect_robots_txt = False
```

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Run examples.py** to see all features in action
3. **Explore the configuration options** in `scraper/config.py`
4. **Customize for your needs** by creating your own configuration presets

## Tips

- **Start simple**: Use default settings first, then customize
- **Check logs**: Set `log_level='DEBUG'` to see what's happening
- **Test with known URLs**: Start with Wikipedia or simple sites
- **Respect robots.txt**: Keep it enabled unless you have a good reason
- **Add delays**: Use `rate_limit_delay` to be respectful to servers
- **Handle errors**: Always wrap scraping in try/except blocks

## Project Structure

```
PolicyLens/
├── scraper/          # Core scraping modules
│   ├── fetcher.py    # Downloads web pages
│   ├── parser.py     # Extracts main content
│   ├── cleaner.py    # Cleans text
│   └── chunker.py    # Splits into chunks
├── utils/            # Utilities
│   ├── exceptions.py # Error handling
│   └── validators.py # Input validation
├── main.py           # Main pipeline
├── examples.py       # Usage examples
└── README.md         # Full documentation
```

## Getting Help

- Check the **README.md** for comprehensive documentation
- Run **examples.py** to see working code
- Look at the **docstrings** in the source code
- Check the **error messages** - they're descriptive!

## License

Free to use for educational and commercial purposes.

Happy Scraping! 🚀
