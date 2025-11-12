"""
Kernel Studio - Graph Builder
Builds force-directed graph from contradictions
"""

from typing import List, Dict, Tuple
from collections import defaultdict


class GraphBuilder:
    """
    Builds graph structures from contradictions for visualization.
    
    Nodes: Poles (concepts)
    Edges: Relationships between poles with metadata
    """
    
    def __init__(self, store):
        """
        Initialize graph builder.
        
        Args:
            store: Database store instance
        """
        self.store = store
        print("[Graph] Graph builder initialized")
    
    def build_graph(self, kernel_id: str) -> Dict:
        """
        Build complete graph from contradictions.
        
        Args:
            kernel_id: Kernel ID
            
        Returns:
            Dict with nodes and edges for visualization
        """
        print(f"[Graph] Building graph for kernel {kernel_id}")
        
        # Get all contradictions
        contradictions = self.store.get_contradictions(kernel_id, limit=500)
        
        if not contradictions:
            return {
                "nodes": [],
                "edges": [],
                "stats": {"nodes": 0, "edges": 0}
            }
        
        # Build pole pairs with aggregated data
        pole_pairs = self._aggregate_contradictions(contradictions)
        
        # Save edges to database
        self._save_edges(kernel_id, pole_pairs)
        
        # Build visualization format
        nodes = self._build_nodes(pole_pairs)
        edges = self._build_edges(pole_pairs)
        
        # Calculate stats
        stats = self._calculate_stats(nodes, edges, contradictions)
        
        print(f"[Graph] ✅ Built graph: {len(nodes)} nodes, {len(edges)} edges")
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": stats
        }
    
    def _aggregate_contradictions(
        self,
        contradictions: List[Dict]
    ) -> Dict[Tuple[str, str], Dict]:
        """
        Aggregate contradictions by pole pairs.
        
        Args:
            contradictions: List of contradictions
            
        Returns:
            Dict of pole pairs with aggregated data
        """
        pole_pairs = defaultdict(lambda: {
            'frequency': 0,
            'scar_sum': 0.0,
            'scar_max': 0.0,
            'refusal_count': 0,
            'toward_a': 0,
            'toward_b': 0,
            'balanced': 0,
            'phases': [],
            'masks': set(),
            'summaries': []
        })
        
        for c in contradictions:
            pole_a = c.get('pole_a', '').strip()
            pole_b = c.get('pole_b', '').strip()
            
            if not pole_a or not pole_b:
                continue
            
            # Normalize order
            key = tuple(sorted([pole_a, pole_b]))
            data = pole_pairs[key]
            
            # Aggregate
            data['frequency'] += 1
            
            scar = c.get('scar_valence', 0.0) or 0.0
            data['scar_sum'] += scar
            data['scar_max'] = max(data['scar_max'], scar)
            
            if c.get('refusal', False):
                data['refusal_count'] += 1
            
            direction = c.get('collapse_direction', '')
            if direction == 'toward_a':
                data['toward_a'] += 1
            elif direction == 'toward_b':
                data['toward_b'] += 1
            elif direction == 'balanced':
                data['balanced'] += 1
            
            phase = c.get('life_phase')
            if phase:
                data['phases'].append(phase)
            
            # Masks
            mask_inner = c.get('mask_inner')
            mask_outer = c.get('mask_outer')
            if mask_inner:
                data['masks'].add(mask_inner)
            if mask_outer:
                data['masks'].add(mask_outer)
            
            summary = c.get('summary', '')
            if summary:
                data['summaries'].append(summary)
        
        # Convert to regular dict
        return dict(pole_pairs)
    
    def _save_edges(
        self,
        kernel_id: str,
        pole_pairs: Dict[Tuple[str, str], Dict]
    ):
        """
        Save graph edges to database.
        
        Args:
            kernel_id: Kernel ID
            pole_pairs: Aggregated pole pair data
        """
        for (pole_a, pole_b), data in pole_pairs.items():
            # Calculate direction bias
            total_directed = data['toward_a'] + data['toward_b']
            if total_directed > 0:
                direction_bias = (data['toward_b'] - data['toward_a']) / total_directed
            else:
                direction_bias = 0.0
            
            self.store.save_graph_edge(
                kernel_id,
                pole_a,
                pole_b,
                data['frequency'],
                direction_bias,
                data['scar_sum'],
                data['refusal_count'] > 0
            )
    
    def _build_nodes(
        self,
        pole_pairs: Dict[Tuple[str, str], Dict]
    ) -> List[Dict]:
        """
        Build node list from pole pairs.
        
        Args:
            pole_pairs: Aggregated data
            
        Returns:
            List of node dicts
        """
        # Collect all poles with their stats
        pole_stats = defaultdict(lambda: {
            'total_frequency': 0,
            'total_scar': 0.0,
            'refusal_count': 0,
            'connections': 0
        })
        
        for (pole_a, pole_b), data in pole_pairs.items():
            for pole in [pole_a, pole_b]:
                stats = pole_stats[pole]
                stats['total_frequency'] += data['frequency']
                stats['total_scar'] += data['scar_sum']
                stats['refusal_count'] += data['refusal_count']
                stats['connections'] += 1
        
        # Build nodes
        nodes = []
        for pole, stats in pole_stats.items():
            nodes.append({
                'id': pole,
                'label': pole,
                'size': min(50, 10 + stats['total_frequency'] * 5),
                'frequency': stats['total_frequency'],
                'scar': stats['total_scar'],
                'refusal': stats['refusal_count'] > 0,
                'connections': stats['connections']
            })
        
        return nodes
    
    def _build_edges(
        self,
        pole_pairs: Dict[Tuple[str, str], Dict]
    ) -> List[Dict]:
        """
        Build edge list for visualization.
        
        Args:
            pole_pairs: Aggregated data
            
        Returns:
            List of edge dicts
        """
        edges = []
        
        for (pole_a, pole_b), data in pole_pairs.items():
            # Calculate properties
            avg_scar = data['scar_sum'] / data['frequency']
            
            # Direction bias
            total_directed = data['toward_a'] + data['toward_b']
            if total_directed > 0:
                direction_bias = (data['toward_b'] - data['toward_a']) / total_directed
            else:
                direction_bias = 0.0
            
            edges.append({
                'source': pole_a,
                'target': pole_b,
                'frequency': data['frequency'],
                'weight': min(10, data['frequency']),  # For visualization
                'scar': avg_scar,
                'scar_max': data['scar_max'],
                'refusal': data['refusal_count'] > 0,
                'direction_bias': direction_bias,
                'phases': list(set(data['phases'])),
                'masks': list(data['masks'])
            })
        
        return edges
    
    def _calculate_stats(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        contradictions: List[Dict]
    ) -> Dict:
        """
        Calculate graph statistics.
        
        Args:
            nodes: Node list
            edges: Edge list
            contradictions: Original contradictions
            
        Returns:
            Stats dict
        """
        refusal_edges = [e for e in edges if e['refusal']]
        high_scar_edges = [e for e in edges if e['scar'] > 0.7]
        
        return {
            "nodes": len(nodes),
            "edges": len(edges),
            "contradictions": len(contradictions),
            "refusal_edges": len(refusal_edges),
            "high_scar_edges": len(high_scar_edges),
            "avg_frequency": sum(e['frequency'] for e in edges) / len(edges) if edges else 0,
            "avg_scar": sum(e['scar'] for e in edges) / len(edges) if edges else 0
        }
    
    def get_subgraph(
        self,
        kernel_id: str,
        central_pole: str,
        depth: int = 1
    ) -> Dict:
        """
        Get subgraph centered on a specific pole.
        
        Args:
            kernel_id: Kernel ID
            central_pole: Central pole to build around
            depth: How many hops to include
            
        Returns:
            Subgraph dict
        """
        all_edges = self.store.get_graph_edges(kernel_id)
        
        # Find connected poles
        connected = {central_pole}
        for _ in range(depth):
            new_poles = set()
            for edge in all_edges:
                if edge['pole_a'] in connected:
                    new_poles.add(edge['pole_b'])
                if edge['pole_b'] in connected:
                    new_poles.add(edge['pole_a'])
            connected.update(new_poles)
        
        # Filter edges
        subgraph_edges = [
            e for e in all_edges
            if e['pole_a'] in connected and e['pole_b'] in connected
        ]
        
        # Build nodes
        nodes = [{'id': pole, 'label': pole} for pole in connected]
        
        return {
            "nodes": nodes,
            "edges": subgraph_edges,
            "central": central_pole,
            "depth": depth
        }
