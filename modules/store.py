"""
Storage module — File-based JSON storage
Handles all data persistence for kernels
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path


class Store:
    """File-based storage for kernel data"""
    
    def __init__(self, data_root: str = "./storage"):
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
    
    def _kernel_path(self, kernel_id: str) -> Path:
        """Get path to kernel directory"""
        path = self.data_root / kernel_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def save_meta(self, kernel_id: str, meta: dict):
        """Save kernel metadata"""
        path = self._kernel_path(kernel_id) / "meta.json"
        with open(path, 'w') as f:
            json.dump(meta, f, indent=2)
    
    def get_meta(self, kernel_id: str) -> Optional[dict]:
        """Get kernel metadata"""
        path = self._kernel_path(kernel_id) / "meta.json"
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return json.load(f)
    
    def list_kernels(self) -> List[dict]:
        """List all kernels"""
        kernels = []
        for kernel_dir in self.data_root.iterdir():
            if kernel_dir.is_dir():
                meta_path = kernel_dir / "meta.json"
                if meta_path.exists():
                    with open(meta_path, 'r') as f:
                        kernels.append(json.load(f))
        return kernels
    
    def delete_kernel(self, kernel_id: str) -> bool:
        """Delete a kernel and all its data"""
        import shutil
        path = self.data_root / kernel_id
        if path.exists():
            shutil.rmtree(path)
            return True
        return False
    
    def add_deep(self, kernel_id: str, chunks: List[dict]):
        """Add deep memory chunks"""
        path = self._kernel_path(kernel_id) / "deep.json"
        
        # Load existing
        existing = []
        if path.exists():
            with open(path, 'r') as f:
                existing = json.load(f)
        
        # Append new chunks
        existing.extend(chunks)
        
        # Save
        with open(path, 'w') as f:
            json.dump(existing, f, indent=2)
    
    def get_deep(self, kernel_id: str) -> List[dict]:
        """Get all deep memories"""
        path = self._kernel_path(kernel_id) / "deep.json"
        if not path.exists():
            return []
        with open(path, 'r') as f:
            return json.load(f)
    
    def add_contradictions(self, kernel_id: str, contradictions: List[dict]):
        """Add contradictions"""
        path = self._kernel_path(kernel_id) / "contradictions.json"
        
        # Load existing
        existing = []
        if path.exists():
            with open(path, 'r') as f:
                existing = json.load(f)
        
        # Append new
        existing.extend(contradictions)
        
        # Save
        with open(path, 'w') as f:
            json.dump(existing, f, indent=2)
    
    def get_contradictions(self, kernel_id: str) -> List[dict]:
        """Get all contradictions"""
        path = self._kernel_path(kernel_id) / "contradictions.json"
        if not path.exists():
            return []
        with open(path, 'r') as f:
            return json.load(f)
