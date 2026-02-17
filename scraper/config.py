"""
Configuration settings for the web scraping pipeline.
Centralizes all configurable parameters with sensible defaults.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class FetcherConfig:
    """Configuration for content fetching."""
    
    # Timeout settings (in seconds)
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    
    # Retry settings
    max_retries: int = 3
    retry_backoff_factor: float = 2.0  # Exponential backoff multiplier
    retry_on_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    
    # User agent settings
    use_random_user_agent: bool = True
    custom_user_agent: Optional[str] = None
    
    # Request headers
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    # SSL verification
    verify_ssl: bool = True
    
    # Robots.txt compliance
    respect_robots_txt: bool = True
    robots_txt_cache_duration: int = 3600  # 1 hour in seconds
    
    # Rate limiting
    rate_limit_delay: float = 0.0  # Delay between requests (seconds)
    
    # Caching
    enable_cache: bool = False
    cache_expire_after: int = 3600  # 1 hour
    
    # Content-Type filtering
    allowed_content_types: List[str] = field(default_factory=lambda: [
        'text/html',
        'application/xhtml+xml',
        'text/plain',
    ])
    
    # Follow redirects
    allow_redirects: bool = True
    max_redirects: int = 5


@dataclass
class ParserConfig:
    """Configuration for content parsing."""
    
    # Primary parser (beautifulsoup parser)
    bs4_parser: str = 'lxml'  # 'lxml', 'html.parser', 'html5lib'
    fallback_parser: str = 'html.parser'
    
    # Extraction methods (in priority order)
    extraction_methods: List[str] = field(default_factory=lambda: [
        'trafilatura',  # Best for articles
        'readability',  # Good for general content
        'manual',       # Custom extraction logic
    ])
    
    # Extract metadata
    extract_metadata: bool = True
    metadata_fields: List[str] = field(default_factory=lambda: [
        'title',
        'author',
        'date',
        'description',
        'language',
        'keywords',
        'url',
    ])
    
    # Content extraction settings
    include_links: bool = True
    include_images: bool = True  # Extract alt text
    include_tables: bool = True
    
    # Filtering
    remove_comments: bool = True
    remove_scripts: bool = True
    remove_styles: bool = True
    
    # Language detection
    detect_language: bool = True
    target_languages: Optional[List[str]] = None  # None = all languages


@dataclass
class CleanerConfig:
    """Configuration for content cleaning."""
    
    # Text normalization
    normalize_whitespace: bool = True
    normalize_unicode: bool = True
    remove_control_characters: bool = True
    
    # Content filtering
    remove_urls: bool = False
    remove_emails: bool = False
    remove_phone_numbers: bool = False
    remove_extra_newlines: bool = True  # More than 2 consecutive newlines
    
    # HTML cleanup
    decode_html_entities: bool = True
    remove_html_tags: bool = True  # If any remain after parsing
    
    # Case normalization
    convert_to_lowercase: bool = False
    
    # Character filtering
    allowed_characters: Optional[str] = None  # Regex pattern, None = all printable
    
    # Minimum content requirements
    min_content_length: int = 50
    min_word_count: int = 10
    
    # Text trimming
    trim_whitespace: bool = True


@dataclass
class ChunkerConfig:
    """Configuration for content chunking."""
    
    # Chunking method
    chunking_method: str = 'paragraph'  # 'character', 'word', 'sentence', 'paragraph', 'token'
    
    # Chunk size (interpretation depends on method)
    chunk_size: int = 1000  # characters/words/tokens depending on method
    
    # Overlap between chunks
    chunk_overlap: int = 100  # characters/words/tokens depending on method
    overlap_percentage: float = 0.1  # Alternative to absolute overlap (0.0-1.0)
    
    # Sentence/paragraph detection settings
    sentence_tokenizer: str = 'nltk'  # 'nltk', 'simple'
    preserve_sentences: bool = True  # Don't split mid-sentence when possible
    preserve_paragraphs: bool = False  # Keep paragraphs together when possible
    
    # Token-based chunking (for LLMs)
    token_encoding: str = 'cl100k_base'  # tiktoken encoding
    max_tokens_per_chunk: int = 500
    
    # Chunk metadata
    include_chunk_metadata: bool = True  # Index, position, etc.
    include_overlap_info: bool = True
    
    # Empty chunk handling
    skip_empty_chunks: bool = True
    min_chunk_length: int = 10  # Minimum characters in chunk


@dataclass
class ScraperConfig:
    """Main configuration for the web scraping pipeline."""
    
    # Sub-configurations
    fetcher: FetcherConfig = field(default_factory=FetcherConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    cleaner: CleanerConfig = field(default_factory=CleanerConfig)
    chunker: ChunkerConfig = field(default_factory=ChunkerConfig)
    
    # Logging
    log_level: str = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    enable_colored_logs: bool = True
    log_file: Optional[str] = None
    
    # Performance
    enable_performance_metrics: bool = True
    
    # Output format
    output_format: str = 'dict'  # 'dict', 'json'
    include_raw_html: bool = False
    include_statistics: bool = True
    
    @classmethod
    def create_default(cls) -> 'ScraperConfig':
        """Create configuration with default settings."""
        return cls()
    
    @classmethod
    def create_fast(cls) -> 'ScraperConfig':
        """Create configuration optimized for speed."""
        config = cls()
        config.fetcher.max_retries = 1
        config.fetcher.respect_robots_txt = False
        config.fetcher.enable_cache = True
        config.parser.extraction_methods = ['trafilatura']
        config.parser.extract_metadata = False
        config.cleaner.normalize_unicode = False
        config.enable_performance_metrics = False
        return config
    
    @classmethod
    def create_thorough(cls) -> 'ScraperConfig':
        """Create configuration optimized for thoroughness."""
        config = cls()
        config.fetcher.max_retries = 5
        config.fetcher.read_timeout = 60.0
        config.parser.extraction_methods = ['trafilatura', 'readability', 'manual']
        config.parser.extract_metadata = True
        config.cleaner.normalize_unicode = True
        config.enable_performance_metrics = True
        return config
    
    @classmethod
    def create_for_articles(cls) -> 'ScraperConfig':
        """Create configuration optimized for article extraction."""
        config = cls()
        config.parser.extraction_methods = ['trafilatura']  # Best for articles
        config.parser.extract_metadata = True
        config.parser.include_links = True
        config.cleaner.remove_urls = False
        config.chunker.chunking_method = 'paragraph'
        config.chunker.preserve_paragraphs = True
        return config
    
    @classmethod
    def create_for_llm(cls, max_tokens: int = 500) -> 'ScraperConfig':
        """
        Create configuration optimized for LLM consumption.
        
        Args:
            max_tokens: Maximum tokens per chunk
        """
        config = cls()
        config.parser.include_links = False
        config.parser.include_images = False
        config.cleaner.remove_urls = True
        config.cleaner.remove_extra_newlines = True
        config.chunker.chunking_method = 'token'
        config.chunker.max_tokens_per_chunk = max_tokens
        config.chunker.preserve_sentences = True
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'fetcher': self.fetcher.__dict__,
            'parser': self.parser.__dict__,
            'cleaner': self.cleaner.__dict__,
            'chunker': self.chunker.__dict__,
            'log_level': self.log_level,
            'enable_colored_logs': self.enable_colored_logs,
            'log_file': self.log_file,
            'enable_performance_metrics': self.enable_performance_metrics,
            'output_format': self.output_format,
            'include_raw_html': self.include_raw_html,
            'include_statistics': self.include_statistics,
        }
    
    def validate(self) -> bool:
        """
        Validate configuration settings.
        
        Returns:
            True if valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate timeouts
        if self.fetcher.connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")
        if self.fetcher.read_timeout <= 0:
            raise ValueError("read_timeout must be positive")
        
        # Validate retries
        if self.fetcher.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        
        # Validate chunk settings
        if self.chunker.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunker.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if self.chunker.chunk_overlap >= self.chunker.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        # Validate chunking method
        valid_methods = ['character', 'word', 'sentence', 'paragraph', 'token']
        if self.chunker.chunking_method not in valid_methods:
            raise ValueError(f"chunking_method must be one of {valid_methods}")
        
        # Validate parser
        valid_parsers = ['lxml', 'html.parser', 'html5lib']
        if self.parser.bs4_parser not in valid_parsers:
            raise ValueError(f"bs4_parser must be one of {valid_parsers}")
        
        # Validate extraction methods
        valid_extraction = ['trafilatura', 'readability', 'manual']
        for method in self.parser.extraction_methods:
            if method not in valid_extraction:
                raise ValueError(f"Unknown extraction method: {method}")
        
        return True
