"""
Kernel Studio v1.1 - FastAPI Backend for Railway
Connects to Supabase Postgres and handles ingest/chat/retrieval.
"""

import os
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import your modules (adjust paths as needed)
from store import store
# Uncomment when you have these modules ready:
# from modules.embedder import Embedder
# from modules.llm import LLM
# from modules.parser import PDFParser
# from modules.contradiction_engine import ContradictionEngine
# from modules.cluster import Clusterer
# from modules.retriever import HybridRetriever

app = FastAPI(title="Kernel Studio API", version="1.1.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.figma.com",
        "http://localhost:*",
        "*"  # In production, restrict this
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== REQUEST MODELS ==========

class BuildRequest(BaseModel):
    kernel_id: str
    batch_id: Optional[str] = None
    sources: Optional[List[str]] = []  # List of source IDs or storage paths


class ChatRequest(BaseModel):
    kernel_id: str
    message: str
    thread_id: Optional[str] = None


class ContradictionQuery(BaseModel):
    kernel_id: str
    query: Optional[str] = None
    limit: int = 200


# ========== HEALTH CHECK ==========

@app.get("/")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Kernel Studio API v1.1",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }


# ========== BUILD PIPELINE ==========

@app.post("/build")
async def build_kernel(req: BuildRequest, background_tasks: BackgroundTasks):
    """
    Start building a kernel from uploaded sources.
    Steps: Parse → Embed → Extract Contradictions → Cluster → Build Graph
    """
    kernel_id = req.kernel_id
    batch_id = req.batch_id
    
    print(f"[Build] Starting build for kernel: {kernel_id}")
    
    # Verify kernel exists
    kernel = store.get_kernel(kernel_id)
    if not kernel:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    # Create batch if not provided
    if not batch_id:
        batch_id = store.create_batch(kernel_id)
        print(f"[Build] Created batch: {batch_id}")
    
    # Update kernel status
    store.update_kernel_status(kernel_id, "building")
    
    # Run pipeline in background
    background_tasks.add_task(run_build_pipeline, kernel_id, batch_id, req.sources)
    
    return {
        "ok": True,
        "kernel_id": kernel_id,
        "batch_id": batch_id,
        "status": "building"
    }


async def run_build_pipeline(kernel_id: str, batch_id: str, source_paths: List[str]):
    """
    Background task: Full ingest pipeline.
    For now, this is a MOCK. Replace with real implementation.
    """
    try:
        # Step 1: Parsing
        store.update_batch(batch_id, "parsing", {"step": "parse", "progress": 0})
        await asyncio.sleep(2)  # Simulate parsing
        
        # TODO: Real implementation:
        # sources = store.get_sources(kernel_id)
        # for source in sources:
        #     pdf_parser = PDFParser()
        #     text = pdf_parser.parse(source['storage_path'])
        #     store.update_source_status(source['id'], 'parsed')
        
        # Step 2: Embedding
        store.update_batch(batch_id, "embedding", {"step": "embed", "progress": 50})
        await asyncio.sleep(2)  # Simulate embedding
        
        # TODO: Real implementation:
        # embedder = Embedder()
        # chunks = split_text(text)
        # for chunk in chunks:
        #     emb = embedder.embed(chunk)
        #     store.save_deep_memory(kernel_id, {
        #         'text': chunk,
        #         'embedding': emb,
        #         'source_label': source['storage_path']
        #     })
        
        # Step 3: Contradiction Extraction
        store.update_batch(batch_id, "extracting", {"step": "contradictions", "progress": 75})
        await asyncio.sleep(2)  # Simulate contradiction extraction
        
        # TODO: Real implementation:
        # contradiction_engine = ContradictionEngine()
        # contradictions = contradiction_engine.extract(kernel_id)
        # for c in contradictions:
        #     store.save_contradiction(kernel_id, c)
        
        # MOCK: Save sample contradictions
        mock_contradictions = [
            {
                "pole_a": "duty",
                "pole_b": "desire",
                "collapse_direction": "toward_b",
                "scar_valence": 0.85,
                "life_phase": "mid",
                "life_phase_weight": 0.6,
                "summary": "Tension between stoic duty and human desire",
                "refusal": False,
                "mask_inner": "Desire",
                "mask_outer": "Control"
            },
            {
                "pole_a": "public",
                "pole_b": "private",
                "collapse_direction": "balanced",
                "scar_valence": 0.72,
                "life_phase": "late",
                "life_phase_weight": 0.8,
                "summary": "Balance between public duty and private reflection",
                "refusal": False
            },
            {
                "pole_a": "reason",
                "pole_b": "emotion",
                "collapse_direction": "toward_a",
                "scar_valence": 0.91,
                "life_phase": "early",
                "life_phase_weight": 0.3,
                "summary": "Privileging reason over emotion in decision-making",
                "refusal": True,
                "mask_inner": "Control",
                "mask_outer": "Knowledge"
            }
        ]
        
        for c in mock_contradictions:
            store.save_contradiction(kernel_id, c)
        
        # Step 4: Clustering
        store.update_batch(batch_id, "clustering", {"step": "cluster", "progress": 90})
        await asyncio.sleep(1)
        
        # TODO: Real clustering
        # clusterer = Clusterer()
        # clusters = clusterer.cluster(kernel_id)
        # for cluster in clusters:
        #     store.save_cluster(kernel_id, cluster['label_tokens'], 
        #                       cluster['member_ids'], cluster['centroid'])
        
        # Step 5: Graph Building
        store.update_batch(batch_id, "graphing", {"step": "graph", "progress": 95})
        await asyncio.sleep(1)
        
        # Build graph edges from contradictions
        contradictions = store.get_contradictions(kernel_id)
        pole_pairs = {}
        
        for c in contradictions:
            key = tuple(sorted([c['pole_a'], c['pole_b']]))
            if key not in pole_pairs:
                pole_pairs[key] = {
                    'frequency': 0,
                    'scar_sum': 0.0,
                    'refusal_count': 0,
                    'toward_a': 0,
                    'toward_b': 0
                }
            
            pole_pairs[key]['frequency'] += 1
            pole_pairs[key]['scar_sum'] += c['scar_valence'] or 0
            if c['refusal']:
                pole_pairs[key]['refusal_count'] += 1
            
            if c['collapse_direction'] == 'toward_a':
                pole_pairs[key]['toward_a'] += 1
            elif c['collapse_direction'] == 'toward_b':
                pole_pairs[key]['toward_b'] += 1
        
        # Save graph edges
        for (pole_a, pole_b), data in pole_pairs.items():
            direction_bias = (data['toward_b'] - data['toward_a']) / data['frequency']
            store.save_graph_edge(
                kernel_id,
                pole_a,
                pole_b,
                data['frequency'],
                direction_bias,
                data['scar_sum'],
                data['refusal_count'] > 0
            )
        
        # Done!
        store.update_batch(batch_id, "done", {"step": "complete", "progress": 100})
        store.update_kernel_status(kernel_id, "ready", {
            "contradictions": len(contradictions),
            "graph_edges": len(pole_pairs),
            "last_build": datetime.utcnow().isoformat()
        })
        
        print(f"[Build] ✅ Kernel {kernel_id} build complete!")
        
    except Exception as e:
        print(f"[Build] ❌ Error: {e}")
        store.update_batch(batch_id, "error", {"error": str(e)})
        store.update_kernel_status(kernel_id, "error")


# ========== CHAT ENDPOINT ==========

@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Chat with a kernel using hybrid retrieval + LLM.
    """
    kernel_id = req.kernel_id
    message = req.message
    
    print(f"[Chat] Kernel: {kernel_id}, Message: {message[:50]}...")
    
    # Verify kernel exists and is ready
    kernel = store.get_kernel(kernel_id)
    if not kernel:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    if kernel['status'] != 'ready':
        raise HTTPException(
            status_code=400, 
            detail=f"Kernel not ready. Status: {kernel['status']}"
        )
    
    # Get settings
    settings = store.get_kernel_settings(kernel_id)
    weights = settings.get('weights', {})
    
    # TODO: Real implementation with embedder + retriever
    # embedder = Embedder()
    # query_emb = embedder.embed(message)
    
    # retriever = HybridRetriever(store, weights)
    # context = retriever.retrieve(kernel_id, message, query_emb)
    
    # MOCK: For now, just grab some contradictions
    contradictions = store.get_contradictions(kernel_id, limit=5)
    
    # Build context
    context_parts = []
    for c in contradictions:
        context_parts.append(
            f"• {c['pole_a']} ↔ {c['pole_b']} "
            f"({c['collapse_direction']}, scar={c['scar_valence']:.2f})"
        )
    
    context_text = "\n".join(context_parts) if context_parts else "No contradictions yet."
    
    # Get system prompt
    system_prompt = store.get_system_prompt(kernel_id) or (
        f"You are {kernel.get('name', 'an AI persona')}. "
        f"Bio: {kernel.get('bio', 'No bio provided.')} "
        f"Respond authentically using the following tensions:\n{context_text}"
    )
    
    # TODO: Real LLM call
    # llm = LLM()
    # answer = llm.generate(system_prompt, message)
    
    # MOCK answer
    answer = (
        f"As {kernel['name']}, I sense the tension in your question. "
        f"Drawing from my understanding of {contradictions[0]['pole_a']} and "
        f"{contradictions[0]['pole_b']}, I would say: Balance is found not in "
        f"choosing one over the other, but in understanding their dynamic interplay."
    )
    
    # Build trace for debugging
    trace = {
        "retrieved_contradictions": len(contradictions),
        "weights_used": weights,
        "context_length": len(context_text),
        "model": settings.get('models', {}).get('llm', 'gpt-4')
    }
    
    return {
        "answer": answer,
        "trace": trace,
        "kernel": {
            "id": kernel_id,
            "name": kernel['name']
        }
    }


# ========== CONTRADICTIONS ==========

@app.get("/contradictions/{kernel_id}")
def get_contradictions(kernel_id: str, limit: int = 200):
    """Get all contradictions for a kernel."""
    kernel = store.get_kernel(kernel_id)
    if not kernel:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    contradictions = store.get_contradictions(kernel_id, limit)
    
    return {
        "kernel_id": kernel_id,
        "count": len(contradictions),
        "contradictions": contradictions
    }


@app.post("/contradictions/search")
def search_contradictions(req: ContradictionQuery):
    """Vector search for contradictions."""
    kernel_id = req.kernel_id
    query = req.query
    
    if not query:
        # Return all if no query
        return get_contradictions(kernel_id, req.limit)
    
    # TODO: Embed query and search
    # embedder = Embedder()
    # query_emb = embedder.embed(query)
    # results = store.search_contradictions(kernel_id, query_emb, req.limit)
    
    # For now, just return all
    results = store.get_contradictions(kernel_id, req.limit)
    
    return {
        "kernel_id": kernel_id,
        "query": query,
        "count": len(results),
        "results": results
    }


# ========== GRAPH ==========

@app.get("/graph/{kernel_id}")
def get_graph(kernel_id: str):
    """Get graph edges for force visualization."""
    kernel = store.get_kernel(kernel_id)
    if not kernel:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    edges = store.get_graph_edges(kernel_id)
    
    # Build nodes from edges
    nodes = set()
    for edge in edges:
        nodes.add(edge['pole_a'])
        nodes.add(edge['pole_b'])
    
    return {
        "kernel_id": kernel_id,
        "nodes": [{"id": n, "label": n} for n in nodes],
        "edges": edges
    }


# ========== FILE UPLOAD ==========

@app.post("/upload/{kernel_id}")
async def upload_source(kernel_id: str, file: UploadFile = File(...)):
    """
    Upload a PDF source for a kernel.
    In production, save to Supabase Storage.
    """
    kernel = store.get_kernel(kernel_id)
    if not kernel:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    # TODO: Save to Supabase Storage
    # For now, just mock
    storage_path = f"sources/{kernel_id}/{file.filename}"
    
    # Create source record
    batch_id = store.create_batch(kernel_id)
    source_id = store.create_source(
        kernel_id,
        batch_id,
        storage_path,
        file.content_type or "application/pdf",
        {"filename": file.filename, "size": 0}
    )
    
    return {
        "ok": True,
        "source_id": source_id,
        "batch_id": batch_id,
        "storage_path": storage_path
    }


# ========== KERNEL INFO ==========

@app.get("/kernel/{kernel_id}")
def get_kernel_info(kernel_id: str):
    """Get kernel details and stats."""
    kernel = store.get_kernel(kernel_id)
    if not kernel:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    # Get counts
    contradictions = store.get_contradictions(kernel_id)
    clusters = store.get_clusters(kernel_id)
    sources = store.get_sources(kernel_id)
    edges = store.get_graph_edges(kernel_id)
    
    return {
        "kernel": kernel,
        "stats": {
            "contradictions": len(contradictions),
            "clusters": len(clusters),
            "sources": len(sources),
            "graph_edges": len(edges)
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
