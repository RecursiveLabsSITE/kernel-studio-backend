"""
Retrieval module — Vector search and pole detection
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors
from typing import List, Dict
from .embeddings import embed_query, embed_pair
from .store import Store


# Pole keywords (simplified lexicon)
POLE_KEYWORDS = {
    "justice": ["justice", "fairness", "law", "punishment", "retribution"],
    "mercy": ["mercy", "forgiveness", "clemency", "pardon", "compassion"],
    "control": ["control", "power", "command", "authority", "rule"],
    "freedom": ["freedom", "liberty", "autonomy", "independence"],
    "duty": ["duty", "obligation", "responsibility", "honor"],
    "desire": ["desire", "want", "pleasure", "passion", "impulse"],
    "reason": ["reason", "logic", "rationality", "thought", "mind"],
    "emotion": ["emotion", "feeling", "heart", "passion"],
    "action": ["action", "deed", "work", "practice"],
    "contemplation": ["contemplation", "meditation", "reflection", "thought"],
}


class Retrieval:
    """Handles vector search and pole detection"""
    
    def __init__(self, store: Store):
        self.store = store
    
    def detect_poles(self, message: str) -> List[str]:
        """Detect which poles are mentioned in the message"""
        message_lower = message.lower()
        detected = []
        
        for pole, keywords in POLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    if pole not in detected:
                        detected.append(pole)
                    break
        
        return detected
    
    def search_contradictions(
        self,
        kernel_id: str,
        poles: List[str],
        top_k: int = 10
    ) -> List[Dict]:
        """Search for relevant contradictions"""
        
        # Get all contradictions
        contradictions = self.store.get_contradictions(kernel_id)
        
        if not contradictions or len(poles) < 2:
            return []
        
        # Create query embedding from first two poles
        query_embedding = embed_pair(poles[0], poles[1])
        
        # Extract embeddings
        embeddings = np.array([c["embedding"] for c in contradictions])
        
        # Build k-NN index
        k = min(top_k, len(contradictions))
        nbrs = NearestNeighbors(n_neighbors=k, metric='cosine')
        nbrs.fit(embeddings)
        
        # Search
        distances, indices = nbrs.kneighbors([query_embedding])
        
        # Return top matches
        results = []
        for idx in indices[0]:
            results.append(contradictions[idx])
        
        return results
    
    def search_deep(
        self,
        kernel_id: str,
        message: str,
        top_k: int = 12
    ) -> List[Dict]:
        """Search deep memories semantically"""
        
        # Get all deep memories
        deep = self.store.get_deep(kernel_id)
        
        if not deep:
            return []
        
        # Create query embedding
        query_embedding = embed_query(message)
        
        # Extract embeddings
        embeddings = np.array([d["embedding"] for d in deep])
        
        # Build k-NN index
        k = min(top_k, len(deep))
        nbrs = NearestNeighbors(n_neighbors=k, metric='cosine')
        nbrs.fit(embeddings)
        
        # Search
        distances, indices = nbrs.kneighbors([query_embedding])
        
        # Return top matches
        results = []
        for idx in indices[0]:
            results.append(deep[idx])
        
        return results
    
    def retrieve(
        self,
        kernel_id: str,
        message: str,
        doc_lens: List[str] = None,
        masks: List[str] = None
    ) -> Dict:
        """
        Main retrieval function
        Returns a pack with contradictions and deep memories
        """
        
        # Detect poles
        poles = self.detect_poles(message)
        
        # Search contradictions (if we have poles)
        contradictions = []
        if len(poles) >= 2:
            contradictions = self.search_contradictions(kernel_id, poles, top_k=10)
        
        # Search deep memories
        deep = self.search_deep(kernel_id, message, top_k=12)
        
        # Filter by doc_lens if provided
        if doc_lens:
            deep = [d for d in deep if d.get("source") in doc_lens]
        
        # Filter by masks if provided
        if masks:
            deep = [d for d in deep if any(m in d.get("masks", []) for m in masks)]
        
        return {
            "contradictions": contradictions,
            "deep": deep,
            "poles": poles,
            "message": message
        }
