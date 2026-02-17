"""
Content fetcher module for downloading web pages.
Handles HTTP requests with retry logic, user agent rotation, and robots.txt compliance.
"""

import time
import logging
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout, ConnectionError
from fake_useragent import UserAgent
from retry import retry

from .config import FetcherConfig
from utils.exceptions import (
    FetchError,
    TimeoutError as ScraperTimeoutError,
    RateLimitError,
    RobotsDisallowedError,
)
from utils.validators import URLValidator


logger = logging.getLogger(__name__)


class ContentFetcher:
    """Fetches content from URLs with robust error handling."""
    
    def __init__(self, config: Optional[FetcherConfig] = None):
        """
        Initialize ContentFetcher.
        
        Args:
            config: Fetcher configuration (uses defaults if None)
        """
        self.config = config or FetcherConfig()
        self.session = self._create_session()
        self.user_agent_generator = UserAgent() if self.config.use_random_user_agent else None
        self.robots_cache: Dict[str, Tuple[RobotFileParser, float]] = {}
        self.last_request_time: Dict[str, float] = {}
        
        logger.debug("ContentFetcher initialized")
    
    def _create_session(self) -> requests.Session:
        """
        Create and configure requests session.
        
        Returns:
            Configured session
        """
        session = requests.Session()
        
        # Configure retry adapter
        adapter = HTTPAdapter(
            max_retries=0  # We handle retries manually for more control
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Set default headers
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Add custom headers
        if self.config.custom_headers:
            session.headers.update(self.config.custom_headers)
        
        return session
    
    def _get_user_agent(self) -> str:
        """
        Get user agent string.
        
        Returns:
            User agent string
        """
        if self.config.custom_user_agent:
            return self.config.custom_user_agent
        
        if self.user_agent_generator:
            try:
                return self.user_agent_generator.random
            except Exception as e:
                logger.warning(f"Failed to get random user agent: {e}, using default")
        
        # Default user agent
        return ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    def _check_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False otherwise
            
        Raises:
            RobotsDisallowedError: If URL is disallowed
        """
        if not self.config.respect_robots_txt:
            return True
        
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = urljoin(domain, '/robots.txt')
        
        # Check cache
        current_time = time.time()
        if domain in self.robots_cache:
            robot_parser, cache_time = self.robots_cache[domain]
            if current_time - cache_time < self.config.robots_txt_cache_duration:
                if not robot_parser.can_fetch(self._get_user_agent(), url):
                    raise RobotsDisallowedError(url=url)
                return True
        
        # Fetch and parse robots.txt
        try:
            logger.debug(f"Fetching robots.txt from {robots_url}")
            robot_parser = RobotFileParser()
            robot_parser.set_url(robots_url)
            robot_parser.read()
            
            # Cache the parser
            self.robots_cache[domain] = (robot_parser, current_time)
            
            if not robot_parser.can_fetch(self._get_user_agent(), url):
                raise RobotsDisallowedError(url=url)
            
            return True
            
        except RobotsDisallowedError:
            raise
        except Exception as e:
            # If we can't fetch robots.txt, allow by default
            logger.warning(f"Failed to fetch robots.txt: {e}, allowing access")
            return True
    
    def _apply_rate_limit(self, domain: str):
        """
        Apply rate limiting delay.
        
        Args:
            domain: Domain to apply rate limit to
        """
        if self.config.rate_limit_delay <= 0:
            return
        
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.config.rate_limit_delay:
                sleep_time = self.config.rate_limit_delay - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def _should_retry(self, response: Optional[requests.Response], 
                     exception: Optional[Exception]) -> bool:
        """
        Determine if request should be retried.
        
        Args:
            response: Response object (if any)
            exception: Exception raised (if any)
            
        Returns:
            True if should retry, False otherwise
        """
        # Retry on specific exceptions
        if exception:
            if isinstance(exception, (ConnectionError, Timeout)):
                return True
        
        # Retry on specific status codes
        if response:
            if response.status_code in self.config.retry_on_status_codes:
                return True
        
        return False
    
    def _make_request(self, url: str, attempt: int = 1) -> requests.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: URL to fetch
            attempt: Current attempt number
            
        Returns:
            Response object
            
        Raises:
            FetchError: If request fails
        """
        user_agent = self._get_user_agent()
        headers = {'User-Agent': user_agent}
        
        timeout = (self.config.connect_timeout, self.config.read_timeout)
        
        try:
            logger.debug(f"Fetching {url} (attempt {attempt}/{self.config.max_retries + 1})")
            
            response = self.session.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=self.config.verify_ssl,
                allow_redirects=self.config.allow_redirects,
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_seconds = int(retry_after) if retry_after else 60
                raise RateLimitError(
                    url=url,
                    retry_after=retry_seconds,
                    details={'attempt': attempt}
                )
            
            # Raise for bad status codes
            response.raise_for_status()
            
            return response
            
        except Timeout as e:
            if attempt <= self.config.max_retries:
                sleep_time = self.config.retry_backoff_factor ** (attempt - 1)
                logger.warning(f"Timeout on attempt {attempt}, retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                return self._make_request(url, attempt + 1)
            raise ScraperTimeoutError(
                url=url,
                timeout_duration=sum(timeout),
                details={'error': str(e)}
            )
        
        except ConnectionError as e:
            if attempt <= self.config.max_retries:
                sleep_time = self.config.retry_backoff_factor ** (attempt - 1)
                logger.warning(f"Connection error on attempt {attempt}, retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                return self._make_request(url, attempt + 1)
            raise FetchError(
                f"Connection failed: {str(e)}",
                url=url,
                details={'error': str(e)}
            )
        
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            
            # Retry on configured status codes
            if status_code in self.config.retry_on_status_codes and attempt <= self.config.max_retries:
                sleep_time = self.config.retry_backoff_factor ** (attempt - 1)
                logger.warning(f"HTTP {status_code} on attempt {attempt}, retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                return self._make_request(url, attempt + 1)
            
            raise FetchError(
                f"HTTP error: {str(e)}",
                url=url,
                status_code=status_code,
                details={'error': str(e)}
            )
        
        except RequestException as e:
            raise FetchError(
                f"Request failed: {str(e)}",
                url=url,
                details={'error': str(e), 'type': type(e).__name__}
            )
    
    def fetch(self, url: str) -> Dict[str, any]:
        """
        Fetch content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary containing:
                - url: Final URL (after redirects)
                - html: HTML content
                - status_code: HTTP status code
                - headers: Response headers
                - encoding: Content encoding
                - fetch_time: Time taken to fetch (seconds)
                
        Raises:
            ValidationError: If URL is invalid
            RobotsDisallowedError: If blocked by robots.txt
            FetchError: If fetch fails
        """
        start_time = time.time()
        
        # Validate URL
        url = URLValidator.normalize(url)
        logger.info(f"Fetching URL: {url}")
        
        # Check if URL is scrapable
        if not URLValidator.is_scrapable(url):
            raise FetchError(
                "URL does not appear to point to scrapable content",
                url=url,
                details={'reason': 'File extension not supported'}
            )
        
        # Check robots.txt
        self._check_robots_txt(url)
        
        # Apply rate limiting
        domain = URLValidator.get_domain(url)
        self._apply_rate_limit(domain)
        
        # Make request
        response = self._make_request(url)
        
        # Check content type
        content_type = response.headers.get('Content-Type', '').lower()
        if self.config.allowed_content_types:
            if not any(ct in content_type for ct in self.config.allowed_content_types):
                raise FetchError(
                    f"Content-Type not allowed: {content_type}",
                    url=url,
                    status_code=response.status_code,
                    details={'content_type': content_type}
                )
        
        fetch_time = time.time() - start_time
        
        result = {
            'url': response.url,  # Final URL after redirects
            'original_url': url,
            'html': response.text,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'encoding': response.encoding or 'utf-8',
            'content_type': content_type,
            'fetch_time': fetch_time,
        }
        
        logger.info(f"Successfully fetched {url} ({len(response.text)} chars in {fetch_time:.2f}s)")
        
        return result
    
    def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.debug("ContentFetcher session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
