"""
Content cleaner module for processing and cleaning extracted text.
Normalizes, filters, and prepares content for consumption.
"""

import re
import html
import logging
import unicodedata
from typing import Optional, Dict, Any

from .config import CleanerConfig
from utils.exceptions import CleaningError
from utils.validators import ContentValidator


logger = logging.getLogger(__name__)


class ContentCleaner:
    """Cleans and normalizes text content."""
    
    # Regex patterns (compiled for performance)
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    PHONE_PATTERN = re.compile(
        r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    )
    MULTIPLE_SPACES = re.compile(r' {2,}')
    MULTIPLE_NEWLINES = re.compile(r'\n{3,}')
    CONTROL_CHARS = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')
    HTML_TAG = re.compile(r'<[^>]+>')
    
    def __init__(self, config: Optional[CleanerConfig] = None):
        """
        Initialize ContentCleaner.
        
        Args:
            config: Cleaner configuration (uses defaults if None)
        """
        self.config = config or CleanerConfig()
        
        # Compile custom character filter if provided
        self.allowed_chars_pattern = None
        if self.config.allowed_characters:
            try:
                self.allowed_chars_pattern = re.compile(self.config.allowed_characters)
            except re.error as e:
                logger.warning(f"Invalid allowed_characters pattern: {e}")
        
        logger.debug("ContentCleaner initialized")
    
    def _decode_html_entities(self, text: str) -> str:
        """
        Decode HTML entities.
        
        Args:
            text: Text with HTML entities
            
        Returns:
            Decoded text
        """
        if not self.config.decode_html_entities:
            return text
        
        try:
            # Decode named and numeric entities
            text = html.unescape(text)
            logger.debug("Decoded HTML entities")
        except Exception as e:
            logger.warning(f"Failed to decode HTML entities: {e}")
        
        return text
    
    def _remove_html_tags(self, text: str) -> str:
        """
        Remove any remaining HTML tags.
        
        Args:
            text: Text potentially containing HTML tags
            
        Returns:
            Text without HTML tags
        """
        if not self.config.remove_html_tags:
            return text
        
        try:
            text = self.HTML_TAG.sub('', text)
            logger.debug("Removed HTML tags")
        except Exception as e:
            logger.warning(f"Failed to remove HTML tags: {e}")
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters.
        
        Args:
            text: Text with potentially inconsistent Unicode
            
        Returns:
            Normalized text
        """
        if not self.config.normalize_unicode:
            return text
        
        try:
            # Normalize to NFKC form (compatibility composition)
            # This converts things like ® to (R), ½ to 1/2, etc.
            text = unicodedata.normalize('NFKC', text)
            logger.debug("Normalized Unicode")
        except Exception as e:
            logger.warning(f"Failed to normalize Unicode: {e}")
        
        return text
    
    def _remove_control_characters(self, text: str) -> str:
        """
        Remove control characters.
        
        Args:
            text: Text with control characters
            
        Returns:
            Text without control characters
        """
        if not self.config.remove_control_characters:
            return text
        
        try:
            # Keep tabs, newlines, and carriage returns
            text = self.CONTROL_CHARS.sub('', text)
            logger.debug("Removed control characters")
        except Exception as e:
            logger.warning(f"Failed to remove control characters: {e}")
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace.
        
        Args:
            text: Text with irregular whitespace
            
        Returns:
            Text with normalized whitespace
        """
        if not self.config.normalize_whitespace:
            return text
        
        try:
            # Replace multiple spaces with single space
            text = self.MULTIPLE_SPACES.sub(' ', text)
            
            # Replace tabs with spaces
            text = text.replace('\t', ' ')
            
            # Normalize line breaks (CRLF to LF)
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            
            logger.debug("Normalized whitespace")
        except Exception as e:
            logger.warning(f"Failed to normalize whitespace: {e}")
        
        return text
    
    def _remove_extra_newlines(self, text: str) -> str:
        """
        Remove excessive newlines.
        
        Args:
            text: Text with multiple newlines
            
        Returns:
            Text with max 2 consecutive newlines
        """
        if not self.config.remove_extra_newlines:
            return text
        
        try:
            # Replace 3+ newlines with 2 newlines
            text = self.MULTIPLE_NEWLINES.sub('\n\n', text)
            logger.debug("Removed extra newlines")
        except Exception as e:
            logger.warning(f"Failed to remove extra newlines: {e}")
        
        return text
    
    def _remove_urls(self, text: str) -> str:
        """
        Remove URLs from text.
        
        Args:
            text: Text containing URLs
            
        Returns:
            Text without URLs
        """
        if not self.config.remove_urls:
            return text
        
        try:
            text = self.URL_PATTERN.sub('', text)
            logger.debug("Removed URLs")
        except Exception as e:
            logger.warning(f"Failed to remove URLs: {e}")
        
        return text
    
    def _remove_emails(self, text: str) -> str:
        """
        Remove email addresses from text.
        
        Args:
            text: Text containing emails
            
        Returns:
            Text without emails
        """
        if not self.config.remove_emails:
            return text
        
        try:
            text = self.EMAIL_PATTERN.sub('', text)
            logger.debug("Removed emails")
        except Exception as e:
            logger.warning(f"Failed to remove emails: {e}")
        
        return text
    
    def _remove_phone_numbers(self, text: str) -> str:
        """
        Remove phone numbers from text.
        
        Args:
            text: Text containing phone numbers
            
        Returns:
            Text without phone numbers
        """
        if not self.config.remove_phone_numbers:
            return text
        
        try:
            text = self.PHONE_PATTERN.sub('', text)
            logger.debug("Removed phone numbers")
        except Exception as e:
            logger.warning(f"Failed to remove phone numbers: {e}")
        
        return text
    
    def _filter_characters(self, text: str) -> str:
        """
        Filter characters based on allowed pattern.
        
        Args:
            text: Text to filter
            
        Returns:
            Filtered text
        """
        if not self.allowed_chars_pattern:
            return text
        
        try:
            # Keep only allowed characters
            text = ''.join(c for c in text if self.allowed_chars_pattern.match(c))
            logger.debug("Filtered characters")
        except Exception as e:
            logger.warning(f"Failed to filter characters: {e}")
        
        return text
    
    def _convert_case(self, text: str) -> str:
        """
        Convert text case if configured.
        
        Args:
            text: Text to convert
            
        Returns:
            Converted text
        """
        if not self.config.convert_to_lowercase:
            return text
        
        try:
            text = text.lower()
            logger.debug("Converted to lowercase")
        except Exception as e:
            logger.warning(f"Failed to convert case: {e}")
        
        return text
    
    def _trim_whitespace(self, text: str) -> str:
        """
        Trim leading and trailing whitespace.
        
        Args:
            text: Text to trim
            
        Returns:
            Trimmed text
        """
        if not self.config.trim_whitespace:
            return text
        
        try:
            # Trim each line and overall text
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(lines)
            text = text.strip()
            logger.debug("Trimmed whitespace")
        except Exception as e:
            logger.warning(f"Failed to trim whitespace: {e}")
        
        return text
    
    def clean(self, text: str, url: str = None) -> Dict[str, Any]:
        """
        Clean and normalize text content.
        
        Args:
            text: Text to clean
            url: Source URL (for error reporting)
            
        Returns:
            Dictionary containing:
                - content: Cleaned text
                - original_length: Original text length
                - cleaned_length: Cleaned text length
                - word_count: Estimated word count
                - clean_time: Time taken to clean
                
        Raises:
            CleaningError: If cleaning fails or content is invalid
        """
        import time
        start_time = time.time()
        
        if not isinstance(text, str):
            raise CleaningError(
                f"Content must be a string, got {type(text).__name__}",
                url=url
            )
        
        original_length = len(text)
        logger.info(f"Cleaning content ({original_length} characters)")
        
        # Apply cleaning steps in order
        try:
            # Step 1: Decode HTML entities
            text = self._decode_html_entities(text)
            
            # Step 2: Remove HTML tags
            text = self._remove_html_tags(text)
            
            # Step 3: Normalize Unicode
            text = self._normalize_unicode(text)
            
            # Step 4: Remove control characters
            text = self._remove_control_characters(text)
            
            # Step 5: Normalize whitespace
            text = self._normalize_whitespace(text)
            
            # Step 6: Remove URLs
            text = self._remove_urls(text)
            
            # Step 7: Remove emails
            text = self._remove_emails(text)
            
            # Step 8: Remove phone numbers
            text = self._remove_phone_numbers(text)
            
            # Step 9: Remove extra newlines
            text = self._remove_extra_newlines(text)
            
            # Step 10: Filter characters
            text = self._filter_characters(text)
            
            # Step 11: Convert case
            text = self._convert_case(text)
            
            # Step 12: Trim whitespace
            text = self._trim_whitespace(text)
            
        except CleaningError:
            raise
        except Exception as e:
            raise CleaningError(
                f"Cleaning failed: {str(e)}",
                url=url,
                details={'error': str(e)}
            )
        
        cleaned_length = len(text)
        
        # Validate cleaned content
        try:
            ContentValidator.is_valid_content(
                text,
                min_length=self.config.min_content_length,
                raise_error=True
            )
        except Exception as e:
            raise CleaningError(
                f"Cleaned content validation failed: {str(e)}",
                url=url,
                details={
                    'original_length': original_length,
                    'cleaned_length': cleaned_length
                }
            )
        
        # Check word count
        word_count = ContentValidator.estimate_word_count(text)
        if word_count < self.config.min_word_count:
            raise CleaningError(
                f"Content has too few words ({word_count} < {self.config.min_word_count})",
                url=url,
                details={'word_count': word_count}
            )
        
        # Check for meaningful content
        if not ContentValidator.has_meaningful_content(text):
            raise CleaningError(
                "Content does not appear to be meaningful text",
                url=url
            )
        
        clean_time = time.time() - start_time
        
        result = {
            'content': text,
            'original_length': original_length,
            'cleaned_length': cleaned_length,
            'reduction_percent': ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0,
            'word_count': word_count,
            'clean_time': clean_time,
        }
        
        logger.info(
            f"Successfully cleaned content: {cleaned_length} chars "
            f"({result['reduction_percent']:.1f}% reduction), "
            f"{word_count} words, time={clean_time:.2f}s"
        )
        
        return result
