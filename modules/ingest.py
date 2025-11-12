"""
Kernel Studio - Ingest Pipeline
Coordinates PDF parsing, embedding, and knowledge extraction
"""

import asyncio
from typing import List, Dict, Optional
from .parser import PDFParser, Chunker
from .embeddings import get_embedder


class IngestPipeline:
    """
    Complete ingest pipeline:
    1. Parse PDFs
    2. Chunk text
    3. Generate embeddings
    4. Store deep memories
    """
    
    def __init__(self, store, embedder_model: str = "BAAI/bge-m3"):
        """
        Initialize pipeline.
        
        Args:
            store: Database store instance
            embedder_model: Embedding model name
        """
        self.store = store
        self.parser = PDFParser()
        self.chunker = Chunker(chunk_size=500, overlap=50)
        self.embedder = get_embedder(embedder_model)
        
        print("[Ingest] Pipeline initialized")
    
    async def run(
        self,
        kernel_id: str,
        batch_id: str,
        source_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Run the full ingest pipeline.
        
        Args:
            kernel_id: Kernel ID
            batch_id: Batch ID
            source_ids: Optional list of specific source IDs to process
            
        Returns:
            Pipeline results
        """
        try:
            print(f"[Ingest] Starting pipeline for kernel {kernel_id}")
            
            # Get sources
            if source_ids:
                sources = [
                    s for s in self.store.get_sources(kernel_id)
                    if s['id'] in source_ids
                ]
            else:
                sources = self.store.get_sources(kernel_id)
            
            if not sources:
                raise ValueError("No sources found to ingest")
            
            # Step 1: Parse
            self.store.update_batch(
                batch_id,
                "parsing",
                {"step": "parse", "progress": 10, "total_sources": len(sources)}
            )
            
            all_chunks = []
            for i, source in enumerate(sources):
                print(f"[Ingest] Parsing source {i+1}/{len(sources)}")
                
                chunks = await self._parse_source(source)
                all_chunks.extend(chunks)
                
                self.store.update_source_status(source['id'], 'parsed')
                
                # Update progress
                progress = 10 + (30 * (i + 1) / len(sources))
                self.store.update_batch(
                    batch_id,
                    "parsing",
                    {
                        "step": "parse",
                        "progress": int(progress),
                        "parsed": i + 1,
                        "total": len(sources)
                    }
                )
            
            print(f"[Ingest] Parsed {len(all_chunks)} chunks")
            
            # Step 2: Embed
            self.store.update_batch(
                batch_id,
                "embedding",
                {"step": "embed", "progress": 40, "chunks": len(all_chunks)}
            )
            
            embeddings = await self._embed_chunks(all_chunks)
            
            self.store.update_batch(
                batch_id,
                "embedding",
                {"step": "embed", "progress": 60, "embedded": len(embeddings)}
            )
            
            # Step 3: Store
            self.store.update_batch(
                batch_id,
                "storing",
                {"step": "store", "progress": 70}
            )
            
            stored_count = await self._store_memories(
                kernel_id,
                all_chunks,
                embeddings
            )
            
            self.store.update_batch(
                batch_id,
                "done",
                {
                    "step": "complete",
                    "progress": 100,
                    "sources_processed": len(sources),
                    "chunks_created": len(all_chunks),
                    "memories_stored": stored_count
                }
            )
            
            print(f"[Ingest] ✅ Pipeline complete: {stored_count} memories stored")
            
            return {
                "success": True,
                "sources_processed": len(sources),
                "chunks": len(all_chunks),
                "memories": stored_count
            }
            
        except Exception as e:
            print(f"[Ingest] ❌ Pipeline error: {e}")
            self.store.update_batch(
                batch_id,
                "error",
                {"error": str(e)}
            )
            raise
    
    async def _parse_source(self, source: Dict) -> List[Dict]:
        """
        Parse a single source.
        
        Args:
            source: Source record
            
        Returns:
            List of chunks with metadata
        """
        storage_path = source['storage_path']
        
        # Parse PDF
        # TODO: Handle actual storage path (Supabase Storage URL)
        # For now, assume it's a local path or you need to download
        text = self.parser.parse(storage_path)
        
        if not text:
            print(f"[Ingest] ⚠️ No text extracted from {storage_path}")
            return []
        
        # Chunk text
        chunks = self.chunker.chunk_text(text)
        
        # Add metadata to each chunk
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                'text': chunk,
                'source_id': source['id'],
                'source_label': storage_path,
                'chunk_index': i,
                'total_chunks': len(chunks)
            })
        
        return result
    
    async def _embed_chunks(self, chunks: List[Dict]) -> List[List[float]]:
        """
        Embed all chunks.
        
        Args:
            chunks: List of chunk dicts
            
        Returns:
            List of embeddings
        """
        texts = [c['text'] for c in chunks]
        
        # Batch embed for efficiency
        embeddings = self.embedder.embed_batch(texts, batch_size=32)
        
        return embeddings
    
    async def _store_memories(
        self,
        kernel_id: str,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> int:
        """
        Store chunks as deep memories.
        
        Args:
            kernel_id: Kernel ID
            chunks: List of chunks
            embeddings: List of embeddings
            
        Returns:
            Number of memories stored
        """
        count = 0
        
        for chunk, embedding in zip(chunks, embeddings):
            # Extract any tags (simple keyword extraction)
            tags = self._extract_tags(chunk['text'])
            
            # Determine life phase (would need more sophisticated logic)
            life_phase = None  # or 'early', 'mid', 'late'
            
            self.store.save_deep_memory(kernel_id, {
                'source_label': chunk['source_label'],
                'text': chunk['text'],
                'tags': tags,
                'life_phase': life_phase,
                'embedding': embedding
            })
            
            count += 1
        
        return count
    
    def _extract_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """
        Simple tag extraction from text.
        
        Args:
            text: Text to extract tags from
            max_tags: Maximum number of tags
            
        Returns:
            List of tags
        """
        # Very basic: extract capitalized words
        import re
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        
        # Count frequency
        from collections import Counter
        counts = Counter(words)
        
        # Return most common
        return [word.lower() for word, _ in counts.most_common(max_tags)]
