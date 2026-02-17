# Web Scraping Pipeline - Architecture & Flow

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WEB SCRAPING PIPELINE                        │
└─────────────────────────────────────────────────────────────────────┘

INPUT: URL
  │
  ├──────────────────────────────────────────────────────────────────┐
  │                                                                    │
  ▼                                                                    │
┌──────────────────────────────┐                                      │
│   STAGE 1: FETCH             │                                      │
│   (ContentFetcher)           │                                      │
├──────────────────────────────┤                                      │
│ • Validate URL               │                                      │
│ • Check robots.txt           │                                      │
│ • Apply rate limiting        │                                      │
│ • Send HTTP request          │                                      │
│ • Retry on failure           │                                      │
│ • Handle redirects           │                                      │
└──────────────────────────────┘                                      │
  │                                                                    │
  │ Output: HTML + metadata                                           │
  │                                                                    │
  ▼                                                                    │
┌──────────────────────────────┐                                      │
│   STAGE 2: PARSE             │                                      │
│   (ContentParser)            │                                      │
├──────────────────────────────┤                                      │
│ • Parse HTML (BeautifulSoup) │                                      │
│ • Extract with Trafilatura   │◄─── Primary extraction              │
│   └─ Failed? ──▼             │                                      │
│ • Extract with Readability   │◄─── Fallback extraction             │
│   └─ Failed? ──▼             │                                      │
│ • Manual extraction          │◄─── Final fallback                  │
│ • Extract metadata           │                                      │
│ • Detect language            │                                      │
└──────────────────────────────┘                                      │
  │                                                                    │
  │ Output: Text content + metadata                                   │
  │                                                                    │
  ▼                                                                    │
┌──────────────────────────────┐                                      │
│   STAGE 3: CLEAN             │                                      │
│   (ContentCleaner)           │                                      │
├──────────────────────────────┤                                      │
│ • Decode HTML entities       │                                      │
│ • Remove HTML tags           │                                      │
│ • Normalize Unicode          │                                      │
│ • Remove control chars       │                                      │
│ • Normalize whitespace       │                                      │
│ • Remove URLs/emails         │ (optional)                           │
│ • Remove extra newlines      │                                      │
│ • Filter characters          │                                      │
│ • Convert case               │ (optional)                           │
│ • Trim whitespace            │                                      │
│ • Validate content           │                                      │
└──────────────────────────────┘                                      │
  │                                                                    │
  │ Output: Cleaned text                                              │
  │                                                                    │
  ▼                                                                    │
┌──────────────────────────────┐                                      │
│   STAGE 4: CHUNK             │                                      │
│   (ContentChunker)           │                                      │
├──────────────────────────────┤                                      │
│ Choose chunking method:      │                                      │
│                              │                                      │
│ ┌────────────────────────┐   │                                      │
│ │ Character-based        │   │ ◄─ Fixed character count            │
│ └────────────────────────┘   │                                      │
│ ┌────────────────────────┐   │                                      │
│ │ Word-based             │   │ ◄─ Fixed word count                 │
│ └────────────────────────┘   │                                      │
│ ┌────────────────────────┐   │                                      │
│ │ Sentence-based         │   │ ◄─ Sentence boundaries              │
│ └────────────────────────┘   │                                      │
│ ┌────────────────────────┐   │                                      │
│ │ Paragraph-based        │   │ ◄─ Preserve paragraphs              │
│ └────────────────────────┘   │                                      │
│ ┌────────────────────────┐   │                                      │
│ │ Token-based (LLM)      │   │ ◄─ Tiktoken encoding                │
│ └────────────────────────┘   │                                      │
│                              │                                      │
│ • Apply overlap              │                                      │
│ • Add chunk metadata         │                                      │
│ • Validate chunks            │                                      │
└──────────────────────────────┘                                      │
  │                                                                    │
  │ Output: List of chunks with metadata                              │
  │                                                                    │
  ▼                                                                    │
┌──────────────────────────────────────────────────────────────────┐  │
│                        RESULT OUTPUT                              │  │
├──────────────────────────────────────────────────────────────────┤  │
│ {                                                                 │  │
│   "url": "...",                                                   │  │
│   "metadata": {...},                                              │  │
│   "content": {                                                    │  │
│     "raw": "Full cleaned text",                                   │  │
│     "chunks": [...]                                               │  │
│   },                                                              │  │
│   "statistics": {...}                                             │  │
│ }                                                                 │  │
└──────────────────────────────────────────────────────────────────┘  │
                                                                       │
═══════════════════════════════════════════════════════════════════════╝
                        Error Handling at Every Stage
```

## Component Interaction

```
┌─────────────┐
│   main.py   │ ──► Main orchestrator, CLI interface
└──────┬──────┘
       │
       ├──► ┌──────────────┐
       │    │ ScraperConfig│ ──► Configuration for all components
       │    └──────────────┘
       │
       ├──► ┌─────────────────┐
       │    │ ContentFetcher  │ ──► HTTP requests, robots.txt
       │    └─────────────────┘
       │
       ├──► ┌─────────────────┐
       │    │ ContentParser   │ ──► HTML parsing, extraction
       │    └─────────────────┘
       │
       ├──► ┌─────────────────┐
       │    │ ContentCleaner  │ ──► Text normalization
       │    └─────────────────┘
       │
       └──► ┌─────────────────┐
            │ ContentChunker  │ ──► Text splitting
            └─────────────────┘

┌──────────────┐
│ Utilities    │
├──────────────┤
│ exceptions.py│ ──► Error handling
│ validators.py│ ──► Input validation
└──────────────┘
```

## Data Flow

```
URL String
    ↓
[Validation] ──► ValidationError?
    ↓
HTTP Request
    ↓
[Retry Logic] ──► FetchError?
    ↓
HTML Content
    ↓
[Multi-method Extraction] ──► ParseError?
    ↓
Raw Text
    ↓
[Cleaning Pipeline] ──► CleaningError?
    ↓
Clean Text
    ↓
[Chunking Strategy] ──► ChunkingError?
    ↓
Chunks + Metadata
    ↓
Result Dictionary
```

## Configuration Flow

```
ScraperConfig
    │
    ├── FetcherConfig
    │   ├── Timeouts
    │   ├── Retries
    │   ├── User agents
    │   ├── Rate limiting
    │   └── Robots.txt
    │
    ├── ParserConfig
    │   ├── Extraction methods
    │   ├── Metadata fields
    │   ├── Language detection
    │   └── Content filters
    │
    ├── CleanerConfig
    │   ├── Normalization
    │   ├── Character filters
    │   ├── Content removal
    │   └── Validation
    │
    └── ChunkerConfig
        ├── Chunking method
        ├── Chunk size
        ├── Overlap
        └── Metadata options

Presets Available:
├── create_default()
├── create_fast()
├── create_thorough()
├── create_for_articles()
└── create_for_llm()
```

## Error Handling Hierarchy

```
ScraperError (Base)
    │
    ├── FetchError
    │   ├── TimeoutError
    │   ├── RateLimitError
    │   └── RobotsDisallowedError
    │
    ├── ParseError
    │
    ├── CleaningError
    │
    ├── ChunkingError
    │
    └── ValidationError

All errors include:
├── message
├── url (if applicable)
├── details (dict)
└── specific context
```

## Extraction Strategy Fallback

```
┌─────────────────┐
│  Start Parsing  │
└────────┬────────┘
         │
         ▼
    ┌────────────┐
    │Trafilatura │ ──► Best for articles
    └─────┬──────┘
          │
    Success? ──Yes──► Return content
          │
         No
          │
          ▼
    ┌────────────┐
    │Readability │ ──► Good for general content
    └─────┬──────┘
          │
    Success? ──Yes──► Return content
          │
         No
          │
          ▼
    ┌────────────┐
    │   Manual   │ ──► BeautifulSoup extraction
    └─────┬──────┘
          │
    Success? ──Yes──► Return content
          │
         No
          │
          ▼
    ┌────────────┐
    │ ParseError │
    └────────────┘
```

## Chunking Methods Comparison

```
┌──────────────┬──────────┬─────────────┬──────────────────┐
│   Method     │ Use Case │ Preserves   │ Best For         │
├──────────────┼──────────┼─────────────┼──────────────────┤
│ Character    │ Simple   │ Nothing     │ Quick splitting  │
│ Word         │ Simple   │ Words       │ Basic analysis   │
│ Sentence     │ Semantic │ Sentences   │ NLP tasks        │
│ Paragraph    │ Semantic │ Paragraphs  │ Articles, docs   │
│ Token        │ LLM      │ Sentences   │ RAG, embeddings  │
└──────────────┴──────────┴─────────────┴──────────────────┘

Overlap Strategy:
┌────────────┐
│  Chunk 1   │
└──────┬─────┘
       │ ┌──────┐ ◄── Overlap region
       └─┤      │
         │Chunk2│
         └──────┤
                │ ┌──────┐
                └─┤      │
                  │Chunk3│
                  └──────┘
```

## Module Dependencies

```
main.py
  ├── scraper/
  │   ├── config.py     (no internal deps)
  │   ├── fetcher.py    requires: config, utils
  │   ├── parser.py     requires: config, utils
  │   ├── cleaner.py    requires: config, utils
  │   └── chunker.py    requires: config, utils
  │
  └── utils/
      ├── exceptions.py (no deps)
      └── validators.py requires: exceptions

External Dependencies:
  ├── requests          (HTTP)
  ├── beautifulsoup4    (HTML parsing)
  ├── lxml              (Fast parsing)
  ├── trafilatura       (Content extraction)
  ├── readability-lxml  (Alternative extraction)
  ├── html2text         (HTML to text)
  ├── langdetect        (Language detection)
  ├── nltk              (Sentence tokenization)
  ├── tiktoken          (Token counting)
  └── fake-useragent    (User agent rotation)
```

## Performance Characteristics

```
┌─────────────────┬──────────┬─────────┬──────────┐
│     Stage       │ Avg Time │ Memory  │ I/O      │
├─────────────────┼──────────┼─────────┼──────────┤
│ Fetch           │ 0.5-2s   │ Low     │ Network  │
│ Parse           │ 0.1-0.5s │ Medium  │ CPU      │
│ Clean           │ 0.05-0.2s│ Low     │ CPU      │
│ Chunk           │ 0.02-0.1s│ Low     │ CPU      │
├─────────────────┼──────────┼─────────┼──────────┤
│ Total (typical) │ 0.7-2.8s │ <100MB  │ Mixed    │
└─────────────────┴──────────┴─────────┴──────────┘

Bottleneck: Network latency (fetch stage)
Optimization: Caching, async requests, rate limiting
```

## Usage Patterns

```
Pattern 1: Simple scraping
───────────────────────────
from main import WebScraper
with WebScraper() as s:
    result = s.scrape(url)

Pattern 2: Batch processing
────────────────────────────
with WebScraper() as s:
    for url in urls:
        result = s.scrape(url)

Pattern 3: Custom config
────────────────────────
config = ScraperConfig.create_for_llm()
with WebScraper(config) as s:
    chunks = s.scrape_url_chunks(url)

Pattern 4: CLI
──────────────
python main.py <url> --preset llm -o output.json
```

---

This architecture provides a robust, maintainable, and extensible
web scraping solution suitable for production use.
