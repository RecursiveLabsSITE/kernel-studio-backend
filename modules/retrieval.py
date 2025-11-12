"""
Kernel Studio - Hybrid Retrieval
Combines vector search with contradiction scoring
"""

from typing import List, Dict, Any, Optional
import numpy as np


class HybridRetriever:
    """
    Hybrid retrieval combining:
    - Vector similarity (contradictions + deep memories)
    - Scar valence weighting
    - Life phase relevance
    - Mask theory signals
    """
    
    def __init__(self, store, weights: Optional[Dict[str, float]] = None):
        """
        Initialize retriever.
        
        Args:
            store: Database store instance
            weights: Retrieval weights for different components
        """
        self.store = store
        
        # Default weights
        self.weights = weights or {
            "pair": 0.32,        # Contradiction pair relevance
            "single": 0.12,      # Single memory relevance
            "cluster": 0.16,     # Cluster membership
            "scar_phase": 0.14,  # Scar valence × life phase
            "bias": 0.10,        # Collapse direction bias
            "refusal": 0.10,     # CLEAR refusal signals
            "mask": 0.06         # Mask theory alignment
        }
        
        print(f"[Retriever] Initialized with weights: {self.weights}")
    
    def retrieve(
        self,
        kernel_id: str,
        query: str,
        query_embedding: List[float],
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query.
        
        Args:
            kernel_id: Kernel ID
            query: Query text
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            
        Returns:
            Dict with retrieved contradictions, memories, and context
        """
        # 1. Vector search contradictions
        contradictions = self.store.search_contradictions(
            kernel_id,
            query_embedding,
            limit=top_k * 2  # Get more for re-ranking
        )
        
        # 2. Vector search deep memories
        memories = self.store.search_deep_memories(
            kernel_id,
            query_embedding,
            limit=top_k
        )
        
        # 3. Re-rank contradictions with hybrid scoring
        scored_contradictions = self._score_contradictions(
            contradictions,
            query_embedding
        )
        
        # 4. Select top-k
        top_contradictions = sorted(
            scored_contradictions,
            key=lambda x: x['hybrid_score'],
            reverse=True
        )[:top_k]
        
        # 5. Build context string
        context = self._build_context(
            top_contradictions,
            memories[:top_k // 2]
        )
        
        return {
            "contradictions": top_contradictions,
            "memories": memories[:top_k // 2],
            "context": context,
            "weights_used": self.weights
        }
    
    def _score_contradictions(
        self,
        contradictions: List[Dict],
        query_embedding: List[float]
    ) -> List[Dict]:
        """
        Score contradictions with hybrid approach.
        
        Args:
            contradictions: List of contradictions with distances
            query_embedding: Query embedding
            
        Returns:
            Contradictions with hybrid scores
        """
        scored = []
        
        for c in contradictions:
            # Vector similarity (already computed as distance)
            # Lower distance = higher similarity
            vector_score = 1.0 / (1.0 + c.get('distance', 1.0))
            
            # Scar valence (higher = more important)
            scar_score = c.get('scar_valence', 0.5)
            
            # Life phase weight
            phase_weight = c.get('life_phase_weight', 0.5)
            
            # Refusal signal (higher weight if present)
            refusal_boost = 1.2 if c.get('refusal', False) else 1.0
            
            # Collapse direction (balanced is slightly preferred)
            direction = c.get('collapse_direction', '')
            balance_score = 1.1 if direction == 'balanced' else 1.0
            
            # Hybrid score
            hybrid_score = (
                self.weights['pair'] * vector_score +
                self.weights['scar_phase'] * scar_score * phase_weight +
                self.weights['refusal'] * refusal_boost +
                self.weights['bias'] * balance_score
            )
            
            c['hybrid_score'] = hybrid_score
            c['vector_score'] = vector_score
            c['scar_score'] = scar_score
            
            scored.append(c)
        
        return scored
    
    def _build_context(
        self,
        contradictions: List[Dict],
        memories: List[Dict]
    ) -> str:
        """
        Build context string from retrieved items.
        
        Args:
            contradictions: Top contradictions
            memories: Top memories
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Add contradictions
        if contradictions:
            parts.append("## Key Tensions & Contradictions:\n")
            for i, c in enumerate(contradictions, 1):
                pole_a = c.get('pole_a', '')
                pole_b = c.get('pole_b', '')
                direction = c.get('collapse_direction', 'unknown')
                scar = c.get('scar_valence', 0)
                summary = c.get('summary', '')
                
                parts.append(
                    f"{i}. **{pole_a} ↔ {pole_b}** "
                    f"(collapse: {direction}, scar: {scar:.2f})"
                )
                
                if summary:
                    parts.append(f"   → {summary}")
                
                # Add mask signals if present
                mask_inner = c.get('mask_inner')
                mask_outer = c.get('mask_outer')
                if mask_inner and mask_outer:
                    parts.append(f"   Masks: {mask_inner} (inner) ↔ {mask_outer} (outer)")
                
                parts.append("")
        
        # Add memories
        if memories:
            parts.append("\n## Relevant Memories:\n")
            for i, m in enumerate(memories, 1):
                text = m.get('text', '')[:200]  # Truncate long memories
                source = m.get('source_label', 'unknown')
                parts.append(f"{i}. {text}... (from {source})")
                parts.append("")
        
        return "\n".join(parts)
    
    def retrieve_by_poles(
        self,
        kernel_id: str,
        pole_a: str,
        pole_b: str
    ) -> List[Dict]:
        """
        Retrieve contradictions by specific poles.
        
        Args:
            kernel_id: Kernel ID
            pole_a: First pole
            pole_b: Second pole
            
        Returns:
            Matching contradictions
        """
        # This would need a SQL query in the store
        # For now, get all and filter
        all_contras = self.store.get_contradictions(kernel_id, limit=1000)
        
        matches = []
        for c in all_contras:
            if (
                (c['pole_a'].lower() == pole_a.lower() and 
                 c['pole_b'].lower() == pole_b.lower()) or
                (c['pole_a'].lower() == pole_b.lower() and 
                 c['pole_b'].lower() == pole_a.lower())
            ):
                matches.append(c)
        
        return matches
    
    def get_mask_context(
        self,
        kernel_id: str,
        mask_type: str
    ) -> List[Dict]:
        """
        Get contradictions filtered by mask type.
        
        Args:
            kernel_id: Kernel ID
            mask_type: Mask type (Desire, Control, Utility, Knowledge, Authenticity)
            
        Returns:
            Contradictions involving this mask
        """
        all_contras = self.store.get_contradictions(kernel_id, limit=500)
        
        filtered = []
        for c in all_contras:
            if (c.get('mask_inner') == mask_type or 
                c.get('mask_outer') == mask_type):
                filtered.append(c)
        
        return filtered
