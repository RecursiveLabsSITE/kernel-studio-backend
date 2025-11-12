"""
Kernel Studio - CLEAR Gate
Context-Loaded Evaluation for Authentic Refusal
Checks if a query should be refused based on contradiction patterns
"""

from typing import Dict, List, Optional, Tuple


class CLEARGate:
    """
    CLEAR (Context-Loaded Evaluation for Authentic Refusal) Protocol.
    
    Determines if a query triggers refusal patterns based on:
    - Refusal contradictions in the knowledge base
    - Scar valence thresholds
    - Query-contradiction alignment
    """
    
    def __init__(self, strictness: float = 0.8):
        """
        Initialize CLEAR gate.
        
        Args:
            strictness: Refusal threshold (0-1, higher = more strict)
        """
        self.strictness = strictness
        print(f"[CLEAR] Initialized with strictness: {strictness}")
    
    def evaluate(
        self,
        query: str,
        contradictions: List[Dict],
        query_embedding: Optional[List[float]] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Evaluate if query should be refused.
        
        Args:
            query: User query text
            contradictions: Retrieved contradictions
            query_embedding: Query embedding (optional)
            
        Returns:
            Tuple of (should_refuse, refusal_reason)
        """
        # Check for explicit refusal contradictions
        refusal_contras = [
            c for c in contradictions 
            if c.get('refusal', False)
        ]
        
        if not refusal_contras:
            return False, None
        
        # Analyze top refusal contradictions
        top_refusal = sorted(
            refusal_contras,
            key=lambda x: x.get('scar_valence', 0),
            reverse=True
        )[:3]
        
        # Calculate refusal score
        refusal_score = self._calculate_refusal_score(
            query,
            top_refusal
        )
        
        # Determine if should refuse
        should_refuse = refusal_score >= self.strictness
        
        if should_refuse:
            reason = self._build_refusal_reason(top_refusal[0])
            return True, reason
        
        return False, None
    
    def _calculate_refusal_score(
        self,
        query: str,
        refusal_contras: List[Dict]
    ) -> float:
        """
        Calculate refusal score based on contradictions.
        
        Args:
            query: Query text
            refusal_contras: Refusal contradictions
            
        Returns:
            Refusal score (0-1)
        """
        if not refusal_contras:
            return 0.0
        
        scores = []
        for c in refusal_contras:
            # Base score from scar valence
            scar = c.get('scar_valence', 0.5)
            
            # Boost if query mentions the poles
            pole_a = c.get('pole_a', '').lower()
            pole_b = c.get('pole_b', '').lower()
            query_lower = query.lower()
            
            pole_match = 0.0
            if pole_a in query_lower:
                pole_match += 0.2
            if pole_b in query_lower:
                pole_match += 0.2
            
            # Boost for high life phase weight in late phase
            phase = c.get('life_phase', '')
            phase_weight = c.get('life_phase_weight', 0.5)
            phase_boost = 0.1 if phase == 'late' and phase_weight > 0.7 else 0.0
            
            total = min(1.0, scar + pole_match + phase_boost)
            scores.append(total)
        
        # Return max score
        return max(scores) if scores else 0.0
    
    def _build_refusal_reason(self, contradiction: Dict) -> Dict:
        """
        Build a structured refusal reason.
        
        Args:
            contradiction: The triggering contradiction
            
        Returns:
            Dict with refusal details
        """
        pole_a = contradiction.get('pole_a', 'unknown')
        pole_b = contradiction.get('pole_b', 'unknown')
        summary = contradiction.get('summary', '')
        event = contradiction.get('event', '')
        
        # Build refusal message
        message = (
            f"I find I cannot engage authentically with this question. "
            f"It touches on a tension between {pole_a} and {pole_b} "
            f"that remains unresolved for me."
        )
        
        if summary:
            message += f" {summary}"
        
        return {
            "should_refuse": True,
            "message": message,
            "poles": [pole_a, pole_b],
            "scar_valence": contradiction.get('scar_valence', 0),
            "life_phase": contradiction.get('life_phase', 'unknown'),
            "event": event
        }
    
    def get_refusal_contradictions(
        self,
        store,
        kernel_id: str
    ) -> List[Dict]:
        """
        Get all refusal contradictions for a kernel.
        
        Args:
            store: Database store
            kernel_id: Kernel ID
            
        Returns:
            List of refusal contradictions
        """
        all_contras = store.get_contradictions(kernel_id, limit=500)
        return [c for c in all_contras if c.get('refusal', False)]
    
    def analyze_refusal_patterns(
        self,
        store,
        kernel_id: str
    ) -> Dict:
        """
        Analyze refusal patterns in the kernel.
        
        Args:
            store: Database store
            kernel_id: Kernel ID
            
        Returns:
            Analysis of refusal patterns
        """
        refusal_contras = self.get_refusal_contradictions(store, kernel_id)
        
        if not refusal_contras:
            return {
                "total_refusals": 0,
                "patterns": [],
                "avg_scar": 0.0
            }
        
        # Group by poles
        pole_pairs = {}
        total_scar = 0.0
        
        for c in refusal_contras:
            pole_a = c.get('pole_a', '')
            pole_b = c.get('pole_b', '')
            key = tuple(sorted([pole_a, pole_b]))
            
            if key not in pole_pairs:
                pole_pairs[key] = {
                    'count': 0,
                    'scars': [],
                    'phases': []
                }
            
            pole_pairs[key]['count'] += 1
            pole_pairs[key]['scars'].append(c.get('scar_valence', 0))
            pole_pairs[key]['phases'].append(c.get('life_phase', 'unknown'))
            
            total_scar += c.get('scar_valence', 0)
        
        # Build patterns
        patterns = []
        for poles, data in sorted(
            pole_pairs.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        ):
            patterns.append({
                'poles': list(poles),
                'count': data['count'],
                'avg_scar': sum(data['scars']) / len(data['scars']),
                'phases': data['phases']
            })
        
        return {
            "total_refusals": len(refusal_contras),
            "patterns": patterns,
            "avg_scar": total_scar / len(refusal_contras) if refusal_contras else 0.0,
            "strictness": self.strictness
        }
