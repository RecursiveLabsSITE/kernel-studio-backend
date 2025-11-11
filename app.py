"""
Λ_Kernel Studio — FastAPI Backend
Production-ready server for Railway deployment
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid

# Import our modules
from modules.store import Store
from modules.ingest import ingest_pdf_bytes
from modules.retrieval import Retrieval
from modules.composer import compose_answer
from modules.graph import build_graph
from modules.clear_gate import run_clear

# Initialize FastAPI
app = FastAPI(
    title="Kernel Studio API",
    description="AI persona creation and conversation system",
    version="1.0.0"
)

# CORS middleware - allow all origins for development
# TODO: Restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage and retrieval
DATA_ROOT = os.getenv("DATA_ROOT", "./storage")
store = Store(DATA_ROOT)
retrieval = Retrieval(store)

# Pydantic models
class KernelCreate(BaseModel):
    name: str
    bio: Optional[str] = ""
    era: Optional[str] = ""

class ChatRequest(BaseModel):
    kernel_id: str
    message: str
    doc_lens: Optional[List[str]] = None
    masks: Optional[List[str]] = None

class ChatResponse(BaseModel):
    answer: str
    trace: dict
    used: dict

# Routes
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"ok": True, "service": "kernel-studio"}

@app.post("/kernels")
def create_kernel(req: KernelCreate):
    """Create a new kernel"""
    kernel_id = str(uuid.uuid4())[:8]
    
    store.save_meta(kernel_id, {
        "kernel_id": kernel_id,
        "name": req.name,
        "bio": req.bio,
        "era": req.era,
        "created_at": None  # Could add timestamp
    })
    
    return {
        "kernel_id": kernel_id,
        "name": req.name,
        "bio": req.bio,
        "era": req.era
    }

@app.get("/kernels")
def list_kernels():
    """List all kernels"""
    return store.list_kernels()

@app.get("/kernels/{kernel_id}")
def get_kernel(kernel_id: str):
    """Get kernel metadata"""
    meta = store.get_meta(kernel_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    # Get stats
    deep = store.get_deep(kernel_id)
    contradictions = store.get_contradictions(kernel_id)
    
    return {
        **meta,
        "stats": {
            "deep_count": len(deep),
            "contradiction_count": len(contradictions)
        }
    }

@app.delete("/kernels/{kernel_id}")
def delete_kernel(kernel_id: str):
    """Delete a kernel"""
    success = store.delete_kernel(kernel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kernel not found")
    return {"ok": True}

@app.post("/ingest")
async def ingest_pdfs(
    kernel_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Ingest PDF files into a kernel"""
    
    # Verify kernel exists
    meta = store.get_meta(kernel_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    total_deep = 0
    total_contradictions = 0
    
    for upload_file in files:
        # Read PDF bytes
        pdf_bytes = await upload_file.read()
        
        # Ingest (this creates chunks, detects contradictions, embeds everything)
        result = ingest_pdf_bytes(
            kernel_id=kernel_id,
            pdf_bytes=pdf_bytes,
            filename=upload_file.filename,
            store=store
        )
        
        total_deep += result["deep_added"]
        total_contradictions += result["contradictions_added"]
    
    # Get updated stats
    deep = store.get_deep(kernel_id)
    contradictions = store.get_contradictions(kernel_id)
    
    return {
        "ok": True,
        "files_processed": len(files),
        "deep_added": total_deep,
        "contradictions_added": total_contradictions,
        "total_deep": len(deep),
        "total_contradictions": len(contradictions)
    }

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Chat with a kernel"""
    
    # Verify kernel exists
    meta = store.get_meta(req.kernel_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Kernel not found")
    
    # Retrieve relevant contexts
    pack = retrieval.retrieve(
        kernel_id=req.kernel_id,
        message=req.message,
        doc_lens=req.doc_lens or [],
        masks=req.masks or []
    )
    
    # Detect poles
    poles = retrieval.detect_poles(req.message)
    
    # Run CLEAR gate
    clear_result = run_clear(pack, poles)
    
    if clear_result["refuse"]:
        # Return refusal
        return ChatResponse(
            answer=f"Ω_clear: {clear_result['message']}",
            trace={"refused": True, "reason": clear_result["message"]},
            used={"contradictions": [], "deep": []}
        )
    
    # Compose answer
    answer, trace = compose_answer(
        kernel_id=req.kernel_id,
        message=req.message,
        pack=pack,
        poles=poles,
        store=store
    )
    
    return ChatResponse(
        answer=answer,
        trace=trace,
        used={
            "contradictions": pack.get("contradictions", []),
            "deep": pack.get("deep", [])
        }
    )

@app.get("/contradictions")
def get_contradictions(kernel_id: str):
    """Get all contradictions for a kernel"""
    contradictions = store.get_contradictions(kernel_id)
    return {"contradictions": contradictions}

@app.get("/graph")
def get_graph(kernel_id: str):
    """Get graph data for visualization"""
    contradictions = store.get_contradictions(kernel_id)
    graph = build_graph(contradictions)
    return graph

@app.get("/deep")
def get_deep_memories(kernel_id: str, limit: Optional[int] = 100):
    """Get deep memories for a kernel"""
    deep = store.get_deep(kernel_id)
    return {"deep": deep[:limit], "total": len(deep)}

# For Railway: expose port via environment variable
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8300))
    uvicorn.run(app, host="0.0.0.0", port=port)
