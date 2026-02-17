"""
Content chunker module for splitting text into manageable pieces.
Supports multiple chunking strategies with overlap.
"""

import re
import logging
from typing import List, Dict, Any, Optional

from .config import ChunkerConfig
from utils.exceptions import ChunkingError


logger = logging.getLogger(__name__)


class ContentChunker:
    """Chunks text content using various strategies."""
    
    def __init__(self, config: Optional[ChunkerConfig] = None):
        """
        Initialize ContentChunker.
        
        Args:
            config: Chunker configuration (uses defaults if None)
        """
        self.config = config or ChunkerConfig()
        
        # Initialize sentence tokenizer if needed
        self.sentence_tokenizer = None
        if self.config.chunking_method in ['sentence', 'paragraph']:
            self._initialize_sentence_tokenizer()
        
        # Initialize token encoder if needed
        self.token_encoder = None
        if self.config.chunking_method == 'token':
            self._initialize_token_encoder()
        
        logger.debug(f"ContentChunker initialized with method: {self.config.chunking_method}")
    
    def _initialize_sentence_tokenizer(self):
        """Initialize NLTK sentence tokenizer."""
        try:
            if self.config.sentence_tokenizer == 'nltk':
                import nltk
                try:
                    # Try to use punkt tokenizer
                    nltk.data.find('tokenizers/punkt')
                except LookupError:
                    # Download if not found
                    logger.info("Downloading NLTK punkt tokenizer...")
                    nltk.download('punkt', quiet=True)
                
                from nltk.tokenize import sent_tokenize
                self.sentence_tokenizer = sent_tokenize
                logger.debug("Initialized NLTK sentence tokenizer")
            else:
                # Use simple tokenizer
                self.sentence_tokenizer = self._simple_sentence_split
                logger.debug("Using simple sentence tokenizer")
        except Exception as e:
            logger.warning(f"Failed to initialize NLTK tokenizer: {e}, using simple tokenizer")
            self.sentence_tokenizer = self._simple_sentence_split
    
    def _simple_sentence_split(self, text: str) -> List[str]:
        """
        Simple sentence splitter based on regex.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Split on . ! ? followed by space and capital letter
        pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _initialize_token_encoder(self):
        """Initialize tiktoken encoder for LLM tokens."""
        try:
            import tiktoken
            self.token_encoder = tiktoken.get_encoding(self.config.token_encoding)
            logger.debug(f"Initialized tiktoken encoder: {self.config.token_encoding}")
        except Exception as e:
            logger.warning(f"Failed to initialize tiktoken: {e}, falling back to word-based chunking")
            self.config.chunking_method = 'word'
    
    def _chunk_by_characters(self, text: str) -> List[str]:
        """
        Chunk text by character count.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Get chunk
            chunk = text[start:end]
            
            # If preserve_sentences is enabled and we're not at the end,
            # try to break at sentence boundary
            if self.config.preserve_sentences and end < text_length:
                # Look for sentence endings in the last 20% of chunk
                search_start = max(start, end - int(chunk_size * 0.2))
                sentence_end_match = None
                
                for pattern in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                    idx = text.rfind(pattern, search_start, end)
                    if idx != -1:
                        if sentence_end_match is None or idx > sentence_end_match:
                            sentence_end_match = idx + len(pattern)
                
                if sentence_end_match:
                    end = sentence_end_match
                    chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk)
            
            # Move start position (with overlap)
            start = end - overlap
            
            # Prevent infinite loop
            if start <= chunks[-1:] and len(chunks) > 0:
                start = end
        
        return chunks
    
    def _chunk_by_words(self, text: str) -> List[str]:
        """
        Chunk text by word count.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        words = text.split()
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        start = 0
        
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            
            chunk = ' '.join(chunk_words)
            
            if chunk.strip():
                chunks.append(chunk)
            
            # Move start position (with overlap)
            start = end - overlap
            
            # Prevent infinite loop
            if start >= end:
                break
        
        return chunks
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """
        Chunk text by sentences.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        if not self.sentence_tokenizer:
            self._initialize_sentence_tokenizer()
        
        sentences = self.sentence_tokenizer(text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence) if self.config.chunking_method == 'sentence' else len(sentence.split())
            
            # If adding this sentence would exceed chunk size
            if current_size + sentence_size > self.config.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                if self.config.chunk_overlap > 0:
                    # Keep last sentences for overlap
                    overlap_size = 0
                    overlap_sentences = []
                    for s in reversed(current_chunk):
                        s_size = len(s) if self.config.chunking_method == 'sentence' else len(s.split())
                        if overlap_size + s_size <= self.config.chunk_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_size += s_size
                        else:
                            break
                    current_chunk = overlap_sentences
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        Chunk text by paragraphs.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        # Split by double newlines
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if self.config.preserve_paragraphs:
            # Keep paragraphs intact, group them into chunks
            chunks = []
            current_chunk = []
            current_size = 0
            
            for para in paragraphs:
                para_size = len(para)
                
                # If this paragraph alone exceeds chunk size, split it
                if para_size > self.config.chunk_size:
                    if current_chunk:
                        chunks.append('\n\n'.join(current_chunk))
                        current_chunk = []
                        current_size = 0
                    
                    # Split large paragraph by sentences
                    para_chunks = self._chunk_by_sentences(para)
                    chunks.extend(para_chunks)
                    continue
                
                # If adding this paragraph would exceed chunk size
                if current_size + para_size > self.config.chunk_size and current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    
                    # Start new chunk with overlap
                    if self.config.chunk_overlap > 0:
                        overlap_paras = []
                        overlap_size = 0
                        for p in reversed(current_chunk):
                            if overlap_size + len(p) <= self.config.chunk_overlap:
                                overlap_paras.insert(0, p)
                                overlap_size += len(p)
                            else:
                                break
                        current_chunk = overlap_paras
                        current_size = overlap_size
                    else:
                        current_chunk = []
                        current_size = 0
                
                current_chunk.append(para)
                current_size += para_size
            
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            
            return chunks
        else:
            # Treat paragraphs as sentences
            return self._chunk_by_sentences('\n'.join(paragraphs))
    
    def _chunk_by_tokens(self, text: str) -> List[str]:
        """
        Chunk text by token count (for LLMs).
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        if not self.token_encoder:
            logger.warning("Token encoder not available, falling back to word chunking")
            return self._chunk_by_words(text)
        
        # Encode entire text
        tokens = self.token_encoder.encode(text)
        
        chunks = []
        max_tokens = self.config.max_tokens_per_chunk
        overlap_tokens = int(max_tokens * 0.1)  # 10% overlap
        
        start = 0
        
        while start < len(tokens):
            end = start + max_tokens
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.token_encoder.decode(chunk_tokens)
            
            # If preserve_sentences, try to break at sentence boundary
            if self.config.preserve_sentences and end < len(tokens):
                # Check last ~10% of chunk for sentence ending
                search_start = int(len(chunk_text) * 0.9)
                for pattern in ['. ', '! ', '? ']:
                    idx = chunk_text.rfind(pattern, search_start)
                    if idx != -1:
                        chunk_text = chunk_text[:idx + len(pattern)]
                        break
            
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
            
            # Move start with overlap
            start = end - overlap_tokens
        
        return chunks
    
    def _create_chunk_metadata(self, chunks: List[str], original_text: str) -> List[Dict[str, Any]]:
        """
        Create metadata for each chunk.
        
        Args:
            chunks: List of text chunks
            original_text: Original text before chunking
            
        Returns:
            List of chunk dictionaries with metadata
        """
        result = []
        
        for idx, chunk in enumerate(chunks):
            chunk_data = {
                'text': chunk,
                'chunk_index': idx,
                'total_chunks': len(chunks),
            }
            
            if self.config.include_chunk_metadata:
                chunk_data.update({
                    'chunk_length': len(chunk),
                    'word_count': len(chunk.split()),
                    'is_first': idx == 0,
                    'is_last': idx == len(chunks) - 1,
                })
            
            if self.config.include_overlap_info and idx > 0:
                # Calculate approximate overlap with previous chunk
                prev_chunk = chunks[idx - 1]
                # Find common substring at boundaries
                overlap_length = 0
                for i in range(1, min(len(chunk), len(prev_chunk)) + 1):
                    if prev_chunk.endswith(chunk[:i]):
                        overlap_length = i
                
                chunk_data['overlap_length'] = overlap_length
            
            result.append(chunk_data)
        
        return result
    
    def chunk(self, text: str, url: str = None) -> Dict[str, Any]:
        """
        Chunk text content.
        
        Args:
            text: Text to chunk
            url: Source URL (for error reporting)
            
        Returns:
            Dictionary containing:
                - chunks: List of chunk dictionaries
                - chunk_count: Number of chunks
                - chunking_method: Method used
                - chunk_size: Configured chunk size
                - overlap: Configured overlap
                - chunk_time: Time taken to chunk
                
        Raises:
            ChunkingError: If chunking fails
        """
        import time
        start_time = time.time()
        
        if not isinstance(text, str):
            raise ChunkingError(
                f"Content must be a string, got {type(text).__name__}",
                url=url
            )
        
        if not text.strip():
            raise ChunkingError("Cannot chunk empty text", url=url)
        
        logger.info(f"Chunking content with method: {self.config.chunking_method}")
        
        try:
            # Chunk based on configured method
            if self.config.chunking_method == 'character':
                chunks = self._chunk_by_characters(text)
            elif self.config.chunking_method == 'word':
                chunks = self._chunk_by_words(text)
            elif self.config.chunking_method == 'sentence':
                chunks = self._chunk_by_sentences(text)
            elif self.config.chunking_method == 'paragraph':
                chunks = self._chunk_by_paragraphs(text)
            elif self.config.chunking_method == 'token':
                chunks = self._chunk_by_tokens(text)
            else:
                raise ChunkingError(
                    f"Unknown chunking method: {self.config.chunking_method}",
                    url=url,
                    chunking_method=self.config.chunking_method
                )
            
        except ChunkingError:
            raise
        except Exception as e:
            raise ChunkingError(
                f"Chunking failed: {str(e)}",
                url=url,
                chunking_method=self.config.chunking_method,
                details={'error': str(e)}
            )
        
        # Filter empty chunks
        if self.config.skip_empty_chunks:
            chunks = [c for c in chunks if c.strip()]
        
        # Filter chunks that are too small
        if self.config.min_chunk_length > 0:
            chunks = [c for c in chunks if len(c.strip()) >= self.config.min_chunk_length]
        
        if not chunks:
            raise ChunkingError(
                "Chunking produced no valid chunks",
                url=url,
                chunking_method=self.config.chunking_method
            )
        
        # Create chunk metadata
        chunks_with_metadata = self._create_chunk_metadata(chunks, text)
        
        chunk_time = time.time() - start_time
        
        result = {
            'chunks': chunks_with_metadata,
            'chunk_count': len(chunks_with_metadata),
            'chunking_method': self.config.chunking_method,
            'chunk_size': self.config.chunk_size,
            'overlap': self.config.chunk_overlap,
            'average_chunk_length': sum(len(c) for c in chunks) / len(chunks),
            'chunk_time': chunk_time,
        }
        
        logger.info(
            f"Successfully chunked content: {len(chunks)} chunks, "
            f"avg_length={result['average_chunk_length']:.0f}, "
            f"method={self.config.chunking_method}, "
            f"time={chunk_time:.2f}s"
        )
        
        return result
