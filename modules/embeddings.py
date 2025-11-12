"""
Kernel Studio - Embeddings Module
Uses sentence-transformers for BGE-M3 or other models
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import os


class Embedder:
    """Embedding service using sentence-transformers."""
    
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """
        Initialize embedder with specified model.
        
        Args:
            model_name: HuggingFace model name (default: BGE-M3)
        """
        self.model_name = model_name
        print(f"[Embedder] Loading model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"[Embedder] ✅ Model loaded. Dimension: {self.dimension}")
        except Exception as e:
            print(f"[Embedder] ❌ Failed to load model: {e}")
            raise
    
    def embed(self, text: str, normalize: bool = True) -> List[float]:
        """
        Embed a single text string.
        
        Args:
            text: Text to embed
            normalize: Whether to L2 normalize the embedding
            
        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )
        
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], normalize: bool = True, 
                   batch_size: int = 32) -> List[List[float]]:
        """
        Embed multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            normalize: Whether to L2 normalize embeddings
            batch_size: Batch size for encoding
            
        Returns:
            List of embeddings
        """
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [t if t and t.strip() else " " for t in texts]
        
        embeddings = self.model.encode(
            valid_texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100
        )
        
        return embeddings.tolist()
    
    def similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        v1 = np.array(emb1)
        v2 = np.array(emb2)
        
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# Global instance (lazy loaded)
_embedder_instance = None


def get_embedder(model_name: str = "BAAI/bge-m3") -> Embedder:
    """Get or create global embedder instance."""
    global _embedder_instance
    
    if _embedder_instance is None:
        _embedder_instance = Embedder(model_name)
    
    return _embedder_instance
