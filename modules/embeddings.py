"""
Embeddings module — sentence-transformers wrapper
Converts text to 768-dimensional vectors
"""

from sentence_transformers import SentenceTransformer
import os

# Global model instance (loaded once)
_model = None

def get_model():
    """Get or create the embedding model"""
    global _model
    if _model is None:
        model_name = os.getenv("EMBED_MODEL", "intfloat/e5-base-v2")
        device = os.getenv("DEVICE", "cpu")
        _model = SentenceTransformer(model_name, device=device)
    return _model

def embed_passage(text: str) -> list:
    """
    Embed a passage of text
    Returns a 768-dim vector as a list
    """
    model = get_model()
    # E5 models use "passage:" prefix for documents
    prefixed = f"passage: {text}"
    vector = model.encode(prefixed, convert_to_numpy=True)
    return vector.tolist()

def embed_query(text: str) -> list:
    """
    Embed a query
    Returns a 768-dim vector as a list
    """
    model = get_model()
    # E5 models use "query:" prefix for queries
    prefixed = f"query: {text}"
    vector = model.encode(prefixed, convert_to_numpy=True)
    return vector.tolist()

def embed_pair(pole_a: str, pole_b: str) -> list:
    """
    Embed a contradiction pair (e.g., "justice [VS] mercy")
    """
    text = f"{pole_a} [VS] {pole_b}"
    return embed_passage(text)
