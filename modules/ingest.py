"""
Ingest module — PDF parsing, chunking, contradiction detection
"""

import re
from typing import List, Dict
import pypdf
from .embeddings import embed_passage, embed_pair
from .store import Store


# Mask lexicon (simplified)
MASK_KEYWORDS = {
    "control": ["power", "empire", "command", "duty", "rule", "govern", "order", "discipline"],
    "knowledge": ["wisdom", "truth", "philosophy", "reason", "logos", "nature", "universe"],
    "utility": ["useful", "practical", "function", "work", "action", "deed"],
    "authenticity": ["true", "genuine", "self", "character", "virtue", "soul"],
    "desire": ["want", "pleasure", "pain", "passion", "emotion", "impulse"]
}


def parse_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    import io
    pdf_file = io.BytesIO(pdf_bytes)
    reader = pypdf.PdfReader(pdf_file)
    
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    return text


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks"""
    # Simple word-based chunking
    words = text.split()
    chunks = []
    
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
        i += chunk_size - overlap
    
    return chunks


def detect_contradictions(text: str) -> List[Dict]:
    """
    Detect contradictions in text using heuristics
    Looks for patterns like "X vs Y", "X or Y", "between X and Y"
    """
    contradictions = []
    
    # Patterns
    patterns = [
        r"(\w+)\s+vs\.?\s+(\w+)",
        r"(\w+)\s+or\s+(\w+)",
        r"between\s+(\w+)\s+and\s+(\w+)",
        r"(\w+)\s+but\s+(\w+)",
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            pole_a = match.group(1).lower()
            pole_b = match.group(2).lower()
            
            # Skip if too short or same
            if len(pole_a) < 3 or len(pole_b) < 3 or pole_a == pole_b:
                continue
            
            # Extract context (100 chars before/after)
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            contradictions.append({
                "pole_a": pole_a,
                "pole_b": pole_b,
                "context": context.strip(),
                "pattern": pattern
            })
    
    return contradictions


def tag_masks(text: str) -> List[str]:
    """Tag which masks are present in text"""
    text_lower = text.lower()
    masks = []
    
    for mask, keywords in MASK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if mask not in masks:
                    masks.append(mask)
                break
    
    return masks


def ingest_pdf_bytes(
    kernel_id: str,
    pdf_bytes: bytes,
    filename: str,
    store: Store
) -> Dict:
    """
    Ingest a PDF file:
    1. Extract text
    2. Chunk it
    3. Detect contradictions
    4. Tag masks
    5. Embed everything
    6. Store
    """
    
    # 1. Extract text
    text = parse_pdf_bytes(pdf_bytes)
    
    # 2. Chunk
    chunks = chunk_text(text)
    
    # 3. Create deep memories
    deep_memories = []
    for i, chunk in enumerate(chunks):
        mem_id = f"{filename}_{i}"
        masks = tag_masks(chunk)
        embedding = embed_passage(chunk)
        
        deep_memories.append({
            "id": mem_id,
            "text": chunk,
            "source": filename,
            "masks": masks,
            "embedding": embedding
        })
    
    # 4. Detect contradictions
    contradiction_candidates = detect_contradictions(text)
    
    # 5. Create contradiction objects with embeddings
    contradictions = []
    for i, cand in enumerate(contradiction_candidates):
        contra_id = f"{filename}_contra_{i}"
        pair_embedding = embed_pair(cand["pole_a"], cand["pole_b"])
        
        contradictions.append({
            "id": contra_id,
            "pole_a": cand["pole_a"],
            "pole_b": cand["pole_b"],
            "context": cand["context"],
            "source": filename,
            "embedding": pair_embedding,
            "scar": 0.5,  # Default scar value
            "phase": "middle",  # Default phase
            "refusal_count": 0
        })
    
    # 6. Store
    store.add_deep(kernel_id, deep_memories)
    store.add_contradictions(kernel_id, contradictions)
    
    return {
        "deep_added": len(deep_memories),
        "contradictions_added": len(contradictions)
    }
