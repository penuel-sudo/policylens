"""
Validation utilities for URLs and content.
Ensures data integrity throughout the scraping pipeline.
"""

import re
from typing import Optional, List
from urllib.parse import urlparse, urlunparse
from .exceptions import ValidationError


class URLValidator:
    """Validates and normalizes URLs."""
    
    # Supported URL schemes
    SUPPORTED_SCHEMES = ['http', 'https']
    
    # Common file extensions to exclude
    EXCLUDED_EXTENSIONS = [
        '.pdf', '.zip', '.exe', '.dmg', '.pkg', '.deb', '.rpm',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.gz', '.tar', '.rar', '.7z',
    ]
    
    @staticmethod
    def is_valid(url: str, raise_error: bool = False) -> bool:
        """
        Check if URL is valid.
        
        Args:
            url: URL to validate
            raise_error: If True, raises ValidationError instead of returning False
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If raise_error is True and validation fails
        """
        if not url or not isinstance(url, str):
            if raise_error:
                raise ValidationError("URL must be a non-empty string", field="url", value=url)
            return False
        
        # Basic format check
        url = url.strip()
        if not url:
            if raise_error:
                raise ValidationError("URL cannot be empty or whitespace", field="url", value=url)
            return False
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in URLValidator.SUPPORTED_SCHEMES:
                if raise_error:
                    raise ValidationError(
                        f"URL scheme must be one of {URLValidator.SUPPORTED_SCHEMES}",
                        field="url",
                        value=url,
                        details={"scheme": parsed.scheme}
                    )
                return False
            
            # Check netloc (domain)
            if not parsed.netloc:
                if raise_error:
                    raise ValidationError(
                        "URL must contain a valid domain",
                        field="url",
                        value=url
                    )
                return False
            
            # Check for suspicious patterns
            if '..' in parsed.path or '..' in parsed.netloc:
                if raise_error:
                    raise ValidationError(
                        "URL contains suspicious patterns (..)",
                        field="url",
                        value=url
                    )
                return False
            
            return True
            
        except Exception as e:
            if raise_error:
                raise ValidationError(
                    f"Invalid URL format: {str(e)}",
                    field="url",
                    value=url,
                    details={"error": str(e)}
                )
            return False
    
    @staticmethod
    def normalize(url: str) -> str:
        """
        Normalize URL to standard format.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
            
        Raises:
            ValidationError: If URL is invalid
        """
        URLValidator.is_valid(url, raise_error=True)
        
        url = url.strip()
        parsed = urlparse(url)
        
        # Normalize scheme to lowercase
        scheme = parsed.scheme.lower()
        
        # Normalize netloc to lowercase
        netloc = parsed.netloc.lower()
        
        # Remove default ports
        if netloc.endswith(':80') and scheme == 'http':
            netloc = netloc[:-3]
        elif netloc.endswith(':443') and scheme == 'https':
            netloc = netloc[:-4]
        
        # Remove trailing slash from path (unless it's just /)
        path = parsed.path
        if path and path != '/' and path.endswith('/'):
            path = path.rstrip('/')
        
        # Rebuild URL
        normalized = urlunparse((
            scheme,
            netloc,
            path or '/',
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        
        return normalized
    
    @staticmethod
    def is_scrapable(url: str) -> bool:
        """
        Check if URL likely points to scrapable HTML content.
        
        Args:
            url: URL to check
            
        Returns:
            True if likely scrapable, False otherwise
        """
        if not URLValidator.is_valid(url):
            return False
        
        url_lower = url.lower()
        
        # Check for excluded file extensions
        for ext in URLValidator.EXCLUDED_EXTENSIONS:
            if url_lower.endswith(ext):
                return False
        
        return True
    
    @staticmethod
    def get_domain(url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain (netloc)
            
        Raises:
            ValidationError: If URL is invalid
        """
        URLValidator.is_valid(url, raise_error=True)
        parsed = urlparse(url)
        return parsed.netloc.lower()


class ContentValidator:
    """Validates scraped content."""
    
    # Minimum content length (characters)
    MIN_CONTENT_LENGTH = 50
    
    # Maximum content length (characters) - 10MB as text
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    # Common non-content indicators
    ERROR_INDICATORS = [
        'page not found',
        '404 error',
        'access denied',
        'forbidden',
        'server error',
        '500 error',
        'temporarily unavailable',
        'under maintenance',
    ]
    
    @staticmethod
    def is_valid_content(
        content: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        check_errors: bool = True,
        raise_error: bool = False
    ) -> bool:
        """
        Check if content is valid.
        
        Args:
            content: Content to validate
            min_length: Minimum content length (default: MIN_CONTENT_LENGTH)
            max_length: Maximum content length (default: MAX_CONTENT_LENGTH)
            check_errors: Check for error page indicators
            raise_error: If True, raises ValidationError instead of returning False
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If raise_error is True and validation fails
        """
        if not isinstance(content, str):
            if raise_error:
                raise ValidationError(
                    "Content must be a string",
                    field="content",
                    value=type(content).__name__
                )
            return False
        
        # Check length
        content_length = len(content)
        min_len = min_length if min_length is not None else ContentValidator.MIN_CONTENT_LENGTH
        max_len = max_length if max_length is not None else ContentValidator.MAX_CONTENT_LENGTH
        
        if content_length < min_len:
            if raise_error:
                raise ValidationError(
                    f"Content too short (minimum: {min_len} characters)",
                    field="content",
                    details={"length": content_length, "minimum": min_len}
                )
            return False
        
        if content_length > max_len:
            if raise_error:
                raise ValidationError(
                    f"Content too long (maximum: {max_len} characters)",
                    field="content",
                    details={"length": content_length, "maximum": max_len}
                )
            return False
        
        # Check for error indicators
        if check_errors:
            content_lower = content.lower()[:1000]  # Check first 1000 chars
            for indicator in ContentValidator.ERROR_INDICATORS:
                if indicator in content_lower:
                    if raise_error:
                        raise ValidationError(
                            f"Content appears to be an error page (found: '{indicator}')",
                            field="content",
                            details={"indicator": indicator}
                        )
                    return False
        
        return True
    
    @staticmethod
    def is_html(content: str) -> bool:
        """
        Check if content looks like HTML.
        
        Args:
            content: Content to check
            
        Returns:
            True if likely HTML, False otherwise
        """
        if not isinstance(content, str) or not content:
            return False
        
        content_lower = content.lower().strip()
        
        # Check for HTML markers
        html_indicators = [
            content_lower.startswith('<!doctype html'),
            content_lower.startswith('<html'),
            '<html' in content_lower[:200],
            '</html>' in content_lower[-200:],
            bool(re.search(r'<(div|p|span|body|head)', content_lower[:500]))
        ]
        
        return any(html_indicators)
    
    @staticmethod
    def estimate_word_count(content: str) -> int:
        """
        Estimate word count in content.
        
        Args:
            content: Content to count words in
            
        Returns:
            Estimated word count
        """
        if not isinstance(content, str):
            return 0
        
        # Simple word count (split on whitespace)
        words = content.split()
        return len(words)
    
    @staticmethod
    def has_meaningful_content(content: str, min_words: int = 20) -> bool:
        """
        Check if content has meaningful text (not just whitespace/symbols).
        
        Args:
            content: Content to check
            min_words: Minimum number of words required
            
        Returns:
            True if content has meaningful text, False otherwise
        """
        if not isinstance(content, str) or not content.strip():
            return False
        
        word_count = ContentValidator.estimate_word_count(content)
        if word_count < min_words:
            return False
        
        # Check that content isn't just repeated characters or symbols
        unique_chars = len(set(content.replace(' ', '').replace('\n', '')))
        if unique_chars < 10:  # Too few unique characters
            return False
        
        return True
