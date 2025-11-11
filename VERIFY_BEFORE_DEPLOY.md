# ✅ VERIFICATION CHECKLIST - Run Before Deploying

## Pre-Deployment Verification

Use this checklist to ensure everything is correct before uploading to GitHub/Railway.

---

## 1. File Structure Check

Verify these files exist in `backend-for-railway/`:

```
☐ app.py                    (Main FastAPI application)
☐ Procfile                  (Railway startup command - NOT a directory!)
☐ requirements.txt          (Python dependencies)
☐ railway.json             (Railway configuration)
☐ README.md                (Documentation)
☐ modules/                 (Directory with 9 Python files)
```

### Check modules/ folder contains:
```
☐ clear_gate.py            (CLEAR refusal protocol)
☐ compose_fallback.py      (Fallback response handling)
☐ composer.py              (Response composition)
☐ embeddings.py            (Vector embeddings)
☐ graph.py                 (Graph visualization)
☐ ingest.py                (PDF processing)
☐ llm.py                   (GPT-4o integration)
☐ retrieval.py             (Memory retrieval)
☐ store.py                 (Database operations)
```

---

## 2. Procfile Verification (CRITICAL!)

### ✅ Verify Procfile is a TEXT FILE (not a directory)

**How to check:**
- Open `backend-for-railway/` folder
- Look at `Procfile`
- It should be a FILE icon (📄) not a FOLDER icon (📁)

### ✅ Verify Procfile contents

Open `Procfile` in a text editor. It should contain EXACTLY this line:

```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

**Requirements:**
- ☐ File named exactly `Procfile` (no .txt extension)
- ☐ Contains exactly one line
- ☐ No extra spaces or newlines
- ☐ No comments or other content

**If Procfile is wrong or missing:**
1. Delete any existing Procfile or Procfile directory
2. Create new file named `Procfile` (no extension)
3. Add the line above
4. Save

---

## 3. Requirements.txt Check

Open `requirements.txt` and verify it contains:

```
☐ fastapi
☐ uvicorn
☐ pydantic
☐ sentence-transformers
☐ torch
☐ pypdf
☐ openai
☐ networkx
☐ python-multipart
```

---

## 4. Railway.json Check

Open `railway.json` and verify structure:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 5. App.py Verification

Open `app.py` and check:

```
☐ Imports FastAPI from fastapi
☐ Creates FastAPI app instance
☐ Has @app.get("/health") endpoint
☐ Has CORS middleware configured
☐ Imports all modules from modules/
☐ Registers all routes
```

---

## 6. Environment Variables Preparation

Prepare these values (you'll need them in Railway):

```
OPENAI_API_KEY=___________________________________
OPENAI_MODEL=gpt-4o
LLM_PROVIDER=openai
EMBED_MODEL=intfloat/e5-base-v2
DEVICE=cpu
DATA_ROOT=/app/storage
```

**Action items:**
- ☐ Have valid OpenAI API key ready
- ☐ Verified key has credits at platform.openai.com
- ☐ Know your OpenAI usage limits

---

## 7. Size Check

Verify folder isn't too large:

**Acceptable:**
- `backend-for-railway/` folder < 50MB
- No large PDFs or test files included
- No `__pycache__` directories
- No `.pyc` files

**If too large:**
- Remove any test data
- Delete `__pycache__` folders
- Remove any large files not needed for deployment

---

## 8. No Protected/Secret Files

Ensure you're NOT including:

```
☐ No .env files with secrets
☐ No API keys in code
☐ No personal PDFs or documents
☐ No database files (*.db, *.sqlite)
☐ No local config files
```

---

## 9. Module Imports Check

For each file in `modules/`, verify:

```python
# Each module should be importable
from modules.clear_gate import check_clear_protocol
from modules.composer import compose_response
from modules.embeddings import get_embeddings
from modules.graph import build_graph
from modules.ingest import process_pdf
from modules.llm import call_gpt4o
from modules.retrieval import retrieve_memories
from modules.store import get_kernel, create_kernel
```

---

## 10. Final Pre-Upload Checklist

Before uploading to GitHub:

```
☐ All 13 files present (1 app.py + 9 modules + 3 config files)
☐ Procfile is a FILE (not directory) with correct content
☐ No syntax errors in Python files
☐ No TODO or placeholder code
☐ Requirements.txt has all dependencies
☐ Railway.json is valid JSON
☐ No secret keys in any files
☐ Folder size < 50MB
☐ OpenAI API key ready for Railway
☐ GitHub account ready
☐ Railway account ready
```

---

## ✅ ALL CHECKS PASSED?

**You're ready to deploy!**

### Next Steps:

1. **Go to:** `START_HERE_DEPLOY.md`
2. **Choose:** Your deployment guide
3. **Follow:** Step-by-step instructions
4. **Deploy:** To Railway in 20 minutes!

---

## 🚨 IF ANY CHECK FAILED

### Procfile Issues:
→ See `DEPLOY_RAILWAY_FINAL.md` - Troubleshooting Section

### Missing Files:
→ Verify you copied entire `backend-for-railway/` folder

### Module Errors:
→ Check all 9 .py files in `modules/` directory

### Size Too Large:
→ Remove test data, cache files, databases

---

## 🔍 Quick Test (Optional)

If you have Python installed locally, test before deploying:

```bash
cd backend-for-railway/

# Install dependencies
pip install -r requirements.txt

# Set test env vars
export OPENAI_API_KEY=your-key
export OPENAI_MODEL=gpt-4o

# Run locally
uvicorn app:app --reload

# Test health endpoint
curl http://localhost:8000/health
```

**Should return:**
```json
{"ok": true, "service": "kernel-studio"}
```

**Optional test passed?** ✅ Definitely ready to deploy!

---

## 📋 Verification Summary

```
┌─────────────────────────────────────────┐
│  PRE-DEPLOYMENT VERIFICATION            │
├─────────────────────────────────────────┤
│  ☐ File structure correct               │
│  ☐ Procfile is TEXT FILE                │
│  ☐ Procfile content verified            │
│  ☐ Requirements.txt complete            │
│  ☐ Railway.json valid                   │
│  ☐ App.py structure correct             │
│  ☐ All modules present                  │
│  ☐ No secrets in code                   │
│  ☐ Folder size acceptable               │
│  ☐ OpenAI key ready                     │
│  ☐ Accounts ready                       │
└─────────────────────────────────────────┘

All checked? → START_HERE_DEPLOY.md
```

---

## 🎯 Success Indicator

**You should have:**
- 1 app.py file
- 1 Procfile (TEXT FILE!)
- 1 requirements.txt
- 1 railway.json
- 1 README.md
- 9 Python files in modules/

**Total: 14 files ready to upload**

---

*Verification checklist created: November 10, 2025*  
*Procfile issue: FIXED ✅*  
*Status: READY TO VERIFY AND DEPLOY*
