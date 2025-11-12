"""
Kernel Studio - PDF Parser
Extracts text from PDFs using pypdf
"""

from pypdf import PdfReader
import io
from typing import List, Dict, Union
import re


class PDFParser:
    """PDF text extraction with cleaning."""
    
    def __init__(self):
        print("[Parser] PDF parser initialized")
    
    def parse(self, source: Union[str, bytes, io.BytesIO]) -> str:
        """
        Extract text from PDF.
        
        Args:
            source: File path, bytes, or BytesIO object
            
        Returns:
            Extracted text
        """
        try:
            # Handle different input types
            if isinstance(source, bytes):
                reader = PdfReader(io.BytesIO(source))
            elif isinstance(source, io.BytesIO):
                reader = PdfReader(source)
            else:
                # Assume file path
                reader = PdfReader(source)
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            full_text = "\n".join(text_parts)
            
            # Clean the text
            cleaned = self._clean_text(full_text)
            
            print(f"[Parser] Extracted {len(cleaned)} chars from {len(reader.pages)} pages")
            return cleaned
            
        except Exception as e:
            print(f"[Parser] ❌ Error parsing PDF: {e}")
            return ""
    
    def parse_with_metadata(self, source: Union[str, bytes, io.BytesIO]) -> Dict:
        """
        Parse PDF with metadata.
        
        Args:
            source: File path, bytes, or BytesIO object
            
        Returns:
            Dict with text, pages, and metadata
        """
        try:
            if isinstance(source, bytes):
                reader = PdfReader(io.BytesIO(source))
            elif isinstance(source, io.BytesIO):
                reader = PdfReader(source)
            else:
                reader = PdfReader(source)
            
            # Extract text
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            full_text = "\n".join(text_parts)
            cleaned = self._clean_text(full_text)
            
            # Get metadata
            metadata = {}
            if reader.metadata:
                metadata = {
                    k.replace('/', ''): v 
                    for k, v in reader.metadata.items()
                }
            
            return {
                "text": cleaned,
                "pages": len(reader.pages),
                "metadata": metadata,
                "word_count": len(cleaned.split())
            }
            
        except Exception as e:
            print(f"[Parser] ❌ Error: {e}")
            return {
                "text": "",
                "pages": 0,
                "metadata": {},
                "error": str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers at start of lines
        text = re.sub(r'^\d+\s+', '', text, flags=re.MULTILINE)
        
        # Fix hyphenated words at line breaks
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()


class Chunker:
    """Text chunking utilities."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Number of words per chunk
            overlap: Number of overlapping words between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks by word count.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            chunk_words = words[i:i + self.chunk_size]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)
            
            # Move forward, accounting for overlap
            i += self.chunk_size - self.overlap
            
            # Break if we're at the end
            if i >= len(words):
                break
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str, max_words: int = 500) -> List[str]:
        """
        Chunk by paragraphs, respecting max word count.
        
        Args:
            text: Text to chunk
            max_words: Maximum words per chunk
            
        Returns:
            List of chunks
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            para_length = len(para.split())
            
            # If adding this paragraph exceeds max, save current chunk
            if current_length + para_length > max_words and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
        
        # Add remaining chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
    
    def chunk_by_sentences(self, text: str, sentences_per_chunk: int = 5) -> List[str]:
        """
        Chunk by sentence count.
        
        Args:
            text: Text to chunk
            sentences_per_chunk: Number of sentences per chunk
            
        Returns:
            List of chunks
        """
        # Simple sentence splitting (can be enhanced with nltk)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk):
            chunk = " ".join(sentences[i:i + sentences_per_chunk])
            chunks.append(chunk)
        
        return chunks
