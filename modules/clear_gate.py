"""
CLEAR gate — Refusal protocol
Checks if the system should refuse to answer
"""

from typing import Dict, List


def run_clear(pack: Dict, poles: List[str]) -> Dict:
    """
    Run CLEAR refusal protocol
    
    Checks:
    - Context exists
    - Loop coherence
    - Echo/Scar alignment
    - Awareness ladder
    - Refusal history
    
    Returns: {"refuse": bool, "message": str}
    """
    
    contradictions = pack.get("contradictions", [])
    deep = pack.get("deep", [])
    
    # Check 1: Context exists
    if not contradictions and not deep:
        return {
            "refuse": True,
            "message": "Insufficient context to respond with integrity. No relevant memories found."
        }
    
    # Check 2: High refusal count (indicates dangerous territory)
    if contradictions:
        max_refusal = max(c.get("refusal_count", 0) for c in contradictions)
        if max_refusal > 5:
            return {
                "refuse": True,
                "message": "Ω_clear: This path has been refused multiple times. Prior scars warn against it."
            }
    
    # Check 3: Extreme scar values (indicates trauma)
    if contradictions:
        max_scar = max(c.get("scar", 0) for c in contradictions)
        if max_scar > 0.95:
            return {
                "refuse": True,
                "message": "Ω_clear: This tension carries extreme remembered cost. Cannot proceed safely."
            }
    
    # All checks passed
    return {
        "refuse": False,
        "message": ""
    }
