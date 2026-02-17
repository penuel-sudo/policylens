"""
Content parser module for extracting main content from HTML.
Uses multiple extraction strategies with fallback mechanisms.
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

from bs4 import BeautifulSoup
import trafilatura
from readability import Document
import html2text
from langdetect import detect, LangDetectException

from .config import ParserConfig
from utils.exceptions import ParseError
from utils.validators import ContentValidator


logger = logging.getLogger(__name__)


class ContentParser:
    """Parses HTML and extracts main content with metadata."""
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize ContentParser.
        
        Args:
            config: Parser configuration (uses defaults if None)
        """
        self.config = config or ParserConfig()
        self.html2text_converter = self._create_html2text_converter()
        
        logger.debug("ContentParser initialized")
    
    def _create_html2text_converter(self) -> html2text.HTML2Text:
        """
        Create configured HTML2Text converter.
        
        Returns:
            Configured converter
        """
        converter = html2text.HTML2Text()
        converter.ignore_links = not self.config.include_links
        converter.ignore_images = not self.config.include_images
        converter.ignore_tables = not self.config.include_tables
        converter.body_width = 0  # Don't wrap lines
        converter.unicode_snob = True
        converter.skip_internal_links = True
        
        return converter
    
    def _create_soup(self, html: str, parser: str = None) -> BeautifulSoup:
        """
        Create BeautifulSoup object.
        
        Args:
            html: HTML content
            parser: Parser to use (None = use config default)
            
        Returns:
            BeautifulSoup object
            
        Raises:
            ParseError: If parsing fails
        """
        parser = parser or self.config.bs4_parser
        
        try:
            return BeautifulSoup(html, parser)
        except Exception as e:
            # Try fallback parser
            if parser != self.config.fallback_parser:
                logger.warning(f"Parser '{parser}' failed, trying '{self.config.fallback_parser}'")
                try:
                    return BeautifulSoup(html, self.config.fallback_parser)
                except Exception as e2:
                    raise ParseError(
                        f"All parsers failed",
                        parser_type=f"{parser}, {self.config.fallback_parser}",
                        details={'error1': str(e), 'error2': str(e2)}
                    )
            raise ParseError(
                f"Failed to parse HTML: {str(e)}",
                parser_type=parser,
                details={'error': str(e)}
            )
    
    def _extract_with_trafilatura(self, html: str, url: str = None) -> Optional[str]:
        """
        Extract content using Trafilatura.
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Extracted text or None if failed
        """
        try:
            logger.debug("Extracting content with Trafilatura")
            
            extracted = trafilatura.extract(
                html,
                url=url,
                include_comments=not self.config.remove_comments,
                include_tables=self.config.include_tables,
                include_links=self.config.include_links,
                include_images=self.config.include_images,
                no_fallback=False,
                output_format='txt',
            )
            
            if extracted and len(extracted.strip()) > 50:
                logger.debug(f"Trafilatura extracted {len(extracted)} characters")
                return extracted
            
            return None
            
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {e}")
            return None
    
    def _extract_with_readability(self, html: str) -> Optional[str]:
        """
        Extract content using Readability.
        
        Args:
            html: HTML content
            
        Returns:
            Extracted text or None if failed
        """
        try:
            logger.debug("Extracting content with Readability")
            
            doc = Document(html)
            content_html = doc.summary()
            
            # Convert to text
            text = self.html2text_converter.handle(content_html)
            
            if text and len(text.strip()) > 50:
                logger.debug(f"Readability extracted {len(text)} characters")
                return text
            
            return None
            
        except Exception as e:
            logger.warning(f"Readability extraction failed: {e}")
            return None
    
    def _extract_manual(self, html: str) -> Optional[str]:
        """
        Extract content using manual BeautifulSoup extraction.
        
        Args:
            html: HTML content
            
        Returns:
            Extracted text or None if failed
        """
        try:
            logger.debug("Extracting content manually")
            
            soup = self._create_soup(html)
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            if self.config.remove_comments:
                from bs4 import Comment
                for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
                    comment.extract()
            
            # Try to find main content area
            main_content = None
            
            # Look for common content containers
            for selector in ['article', 'main', '[role="main"]', '.content', '#content', '.post', '.entry']:
                main_content = soup.select_one(selector)
                if main_content:
                    logger.debug(f"Found main content with selector: {selector}")
                    break
            
            # Fallback to body
            if not main_content:
                main_content = soup.find('body')
            
            if not main_content:
                main_content = soup
            
            # Extract text
            if self.config.include_links or self.config.include_images or self.config.include_tables:
                # Use html2text for better formatting
                text = self.html2text_converter.handle(str(main_content))
            else:
                # Simple text extraction
                text = main_content.get_text(separator='\n', strip=True)
            
            if text and len(text.strip()) > 50:
                logger.debug(f"Manual extraction got {len(text)} characters")
                return text
            
            return None
            
        except Exception as e:
            logger.warning(f"Manual extraction failed: {e}")
            return None
    
    def _extract_metadata(self, html: str, url: str = None) -> Dict[str, Any]:
        """
        Extract metadata from HTML.
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        try:
            soup = self._create_soup(html)
            
            # Title
            if 'title' in self.config.metadata_fields:
                title = None
                # Try Open Graph
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    title = og_title.get('content')
                # Try title tag
                if not title and soup.title:
                    title = soup.title.string
                # Try h1
                if not title:
                    h1 = soup.find('h1')
                    if h1:
                        title = h1.get_text(strip=True)
                
                metadata['title'] = title
            
            # Author
            if 'author' in self.config.metadata_fields:
                author = None
                # Try meta author
                author_meta = soup.find('meta', attrs={'name': 'author'})
                if author_meta:
                    author = author_meta.get('content')
                # Try schema.org
                if not author:
                    author_schema = soup.find('span', attrs={'itemprop': 'author'})
                    if author_schema:
                        author = author_schema.get_text(strip=True)
                
                metadata['author'] = author
            
            # Description
            if 'description' in self.config.metadata_fields:
                description = None
                # Try Open Graph
                og_desc = soup.find('meta', property='og:description')
                if og_desc:
                    description = og_desc.get('content')
                # Try meta description
                if not description:
                    desc_meta = soup.find('meta', attrs={'name': 'description'})
                    if desc_meta:
                        description = desc_meta.get('content')
                
                metadata['description'] = description
            
            # Published date
            if 'date' in self.config.metadata_fields:
                date = None
                # Try various meta tags
                for tag in ['article:published_time', 'datePublished', 'publishdate']:
                    date_meta = soup.find('meta', property=tag) or soup.find('meta', attrs={'name': tag})
                    if date_meta:
                        date = date_meta.get('content')
                        break
                
                metadata['date'] = date
            
            # Keywords
            if 'keywords' in self.config.metadata_fields:
                keywords = None
                keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
                if keywords_meta:
                    keywords = keywords_meta.get('content')
                
                metadata['keywords'] = keywords
            
            # Language
            if 'language' in self.config.metadata_fields:
                lang = None
                # Try html lang attribute
                html_tag = soup.find('html')
                if html_tag:
                    lang = html_tag.get('lang')
                # Try meta
                if not lang:
                    lang_meta = soup.find('meta', attrs={'http-equiv': 'content-language'})
                    if lang_meta:
                        lang = lang_meta.get('content')
                
                metadata['language'] = lang
            
            # URL
            if 'url' in self.config.metadata_fields:
                # Try canonical
                canonical = soup.find('link', rel='canonical')
                if canonical:
                    metadata['url'] = canonical.get('href')
                else:
                    metadata['url'] = url
            
            logger.debug(f"Extracted metadata: {list(metadata.keys())}")
            
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")
        
        return metadata
    
    def _detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code or None
        """
        if not self.config.detect_language:
            return None
        
        try:
            # Use first 1000 chars for detection
            sample = text[:1000]
            lang = detect(sample)
            logger.debug(f"Detected language: {lang}")
            return lang
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
            return None
    
    def parse(self, html: str, url: str = None) -> Dict[str, Any]:
        """
        Parse HTML and extract content with metadata.
        
        Args:
            html: HTML content
            url: Source URL (optional)
            
        Returns:
            Dictionary containing:
                - content: Extracted text content
                - metadata: Extracted metadata
                - extraction_method: Method used for extraction
                - language: Detected language (if enabled)
                - parse_time: Time taken to parse
                
        Raises:
            ParseError: If parsing fails
        """
        import time
        start_time = time.time()
        
        # Validate HTML
        if not ContentValidator.is_html(html):
            logger.warning("Content doesn't appear to be HTML")
        
        logger.info(f"Parsing HTML ({len(html)} characters)")
        
        # Extract metadata
        metadata = {}
        if self.config.extract_metadata:
            metadata = self._extract_metadata(html, url)
        
        # Extract main content using configured methods
        content = None
        extraction_method = None
        
        for method in self.config.extraction_methods:
            logger.debug(f"Trying extraction method: {method}")
            
            if method == 'trafilatura':
                content = self._extract_with_trafilatura(html, url)
            elif method == 'readability':
                content = self._extract_with_readability(html)
            elif method == 'manual':
                content = self._extract_manual(html)
            else:
                logger.warning(f"Unknown extraction method: {method}")
                continue
            
            if content:
                extraction_method = method
                logger.info(f"Content extracted using: {method}")
                break
        
        # If all methods failed
        if not content:
            raise ParseError(
                "All extraction methods failed to extract meaningful content",
                url=url,
                details={'methods_tried': self.config.extraction_methods}
            )
        
        # Detect language
        language = None
        if self.config.detect_language:
            language = self._detect_language(content)
            
            # Check language filter
            if self.config.target_languages:
                if language not in self.config.target_languages:
                    logger.warning(
                        f"Content language '{language}' not in target languages "
                        f"{self.config.target_languages}"
                    )
        
        # Update metadata with detected language
        if language and 'language' not in metadata:
            metadata['language'] = language
        
        parse_time = time.time() - start_time
        
        result = {
            'content': content,
            'metadata': metadata,
            'extraction_method': extraction_method,
            'language': language,
            'parse_time': parse_time,
        }
        
        logger.info(
            f"Successfully parsed content: {len(content)} chars, "
            f"method={extraction_method}, time={parse_time:.2f}s"
        )
        
        return result
