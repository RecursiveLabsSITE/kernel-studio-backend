"""
Graph module — Build network visualization from contradictions
"""

from typing import Dict, List


def build_graph(contradictions: List[Dict]) -> Dict:
    """
    Build graph data structure from contradictions
    
    Returns: {"nodes": [...], "edges": [...]}
    """
    
    # Collect unique poles
    poles = set()
    for c in contradictions:
        poles.add(c["pole_a"])
        poles.add(c["pole_b"])
    
    # Build nodes
    nodes = []
    for pole in poles:
        # Count how many contradictions involve this pole
        count = sum(1 for c in contradictions if pole in [c["pole_a"], c["pole_b"]])
        
        nodes.append({
            "id": pole,
            "label": pole.capitalize(),
            "frequency": count
        })
    
    # Build edges
    edges = []
    for c in contradictions:
        edges.append({
            "source": c["pole_a"],
            "target": c["pole_b"],
            "scar": c.get("scar", 0.5),
            "phase": c.get("phase", "middle"),
            "refusal_count": c.get("refusal_count", 0),
            "context": c.get("context", "")[:100]
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }
