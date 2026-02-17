"""
Custom Exception classes for the web scraping pipeline.
Provides detailed error handling for different stages of scraping process.
"""


class ScraperError(Exception):
    """Base exception class for all scraper-related errors."""
    
    def __init__(self, message: str, url: str = None, details: dict = None):
        """
        Initialize ScraperError.
        
        Args:
            message: Error message
            url: URL where the error occurred (optional)
            details: Additional error details (optional)
        """
        self.message = message
        self.url = url
        self.details = details or {}
        
        full_message = f"{message}"
        if url:
            full_message += f" | URL: {url}"
        if details:
            full_message += f" | Details: {details}"
            
        super().__init__(full_message)


class FetchError(ScraperError):
    """Exception raised when fetching content from a URL fails."""
    
    def __init__(self, message: str, url: str = None, status_code: int = None, details: dict = None):
        """
        Initialize FetchError.
        
        Args:
            message: Error message
            url: URL that failed to fetch
            status_code: HTTP status code (if applicable)
            details: Additional error details
        """
        self.status_code = status_code
        if status_code:
            message = f"{message} (Status Code: {status_code})"
        super().__init__(message, url, details)


class ParseError(ScraperError):
    """Exception raised when parsing HTML content fails."""
    
    def __init__(self, message: str, url: str = None, parser_type: str = None, details: dict = None):
        """
        Initialize ParseError.
        
        Args:
            message: Error message
            url: URL of content that failed to parse
            parser_type: Type of parser that failed
            details: Additional error details
        """
        self.parser_type = parser_type
        if parser_type:
            message = f"{message} (Parser: {parser_type})"
        super().__init__(message, url, details)


class ValidationError(ScraperError):
    """Exception raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None, value: any = None, details: dict = None):
        """
        Initialize ValidationError.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            details: Additional error details
        """
        self.field = field
        self.value = value
        
        if field:
            message = f"{message} (Field: {field})"
        if value is not None:
            message = f"{message} | Value: {value}"
            
        super().__init__(message, None, details)


class CleaningError(ScraperError):
    """Exception raised when content cleaning fails."""
    
    def __init__(self, message: str, url: str = None, cleaning_step: str = None, details: dict = None):
        """
        Initialize CleaningError.
        
        Args:
            message: Error message
            url: URL of content that failed to clean
            cleaning_step: Specific cleaning step that failed
            details: Additional error details
        """
        self.cleaning_step = cleaning_step
        if cleaning_step:
            message = f"{message} (Step: {cleaning_step})"
        super().__init__(message, url, details)


class ChunkingError(ScraperError):
    """Exception raised when content chunking fails."""
    
    def __init__(self, message: str, url: str = None, chunking_method: str = None, details: dict = None):
        """
        Initialize ChunkingError.
        
        Args:
            message: Error message
            url: URL of content that failed to chunk
            chunking_method: Chunking method that failed
            details: Additional error details
        """
        self.chunking_method = chunking_method
        if chunking_method:
            message = f"{message} (Method: {chunking_method})"
        super().__init__(message, url, details)


class RateLimitError(FetchError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", url: str = None, 
                 retry_after: int = None, details: dict = None):
        """
        Initialize RateLimitError.
        
        Args:
            message: Error message
            url: URL that triggered rate limit
            retry_after: Seconds to wait before retry
            details: Additional error details
        """
        self.retry_after = retry_after
        if retry_after:
            message = f"{message} (Retry after {retry_after}s)"
        super().__init__(message, url, status_code=429, details=details)


class TimeoutError(FetchError):
    """Exception raised when request times out."""
    
    def __init__(self, message: str = "Request timeout", url: str = None, 
                 timeout_duration: float = None, details: dict = None):
        """
        Initialize TimeoutError.
        
        Args:
            message: Error message
            url: URL that timed out
            timeout_duration: Timeout duration in seconds
            details: Additional error details
        """
        self.timeout_duration = timeout_duration
        if timeout_duration:
            message = f"{message} (Timeout: {timeout_duration}s)"
        super().__init__(message, url, status_code=408, details=details)


class RobotsDisallowedError(FetchError):
    """Exception raised when URL is disallowed by robots.txt."""
    
    def __init__(self, message: str = "URL disallowed by robots.txt", 
                 url: str = None, details: dict = None):
        """
        Initialize RobotsDisallowedError.
        
        Args:
            message: Error message
            url: Disallowed URL
            details: Additional error details
        """
        super().__init__(message, url, status_code=None, details=details)
