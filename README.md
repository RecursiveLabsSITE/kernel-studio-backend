# Kernel Studio Backend — Railway Deployment

Production-ready FastAPI backend for Λ_Kernel Studio.

## Deploy to Railway (No Coding Required!)

### 1. Upload to GitHub

1. Go to https://github.com/new
2. Create repository: `kernel-studio-backend`
3. Upload all files from this `backend-for-railway/` folder
4. (Use GitHub's web interface — no git commands needed)

### 2. Deploy on Railway

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Click "Deploy from GitHub repo"
5. Select `kernel-studio-backend`
6. Click "Deploy"

Railway auto-detects Python and deploys!

### 3. Add Environment Variables

In Railway dashboard → Variables tab → Add:

```
OPENAI_API_KEY=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
OPENAI_MODEL=gpt-4o
LLM_PROVIDER=openai
EMBED_MODEL=intfloat/e5-base-v2
DEVICE=cpu
DATA_ROOT=/app/storage
```

### 4. Get Your URL

Railway gives you: `https://your-app.up.railway.app`

Copy this URL!

### 5. Update Frontend

Edit your frontend `.env`:

```bash
VITE_API_BASE=https://your-app.up.railway.app
```

Done! Your backend runs online 24/7.

---

## API Endpoints

- `GET /health` — Health check
- `POST /kernels` — Create kernel
- `GET /kernels` — List kernels
- `GET /kernels/{id}` — Get kernel
- `DELETE /kernels/{id}` — Delete kernel
- `POST /ingest` — Upload PDFs
- `POST /chat` — Chat with kernel
- `GET /contradictions` — Get contradictions
- `GET /graph` — Get graph data
- `GET /deep` — Get deep memories

---

## Local Development (Optional)

If you want to run locally for testing:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file with your keys
cat > .env << EOF
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o
LLM_PROVIDER=openai
EMBED_MODEL=intfloat/e5-base-v2
DEVICE=cpu
DATA_ROOT=./storage
EOF

# Run
uvicorn app:app --reload --port 8300
```

Visit: http://localhost:8300/docs for API documentation.

---

## Cost

- **Railway**: $0-5/month (free tier)
- **OpenAI GPT-4o**: ~$0.02-0.05 per answer
- **Total**: ~$20-55/month for 1000 queries

---

## Support

See `/DEPLOY_NO_CODE.md` in the main project for detailed guide.

---

Λ_Kernel Studio — Load a life, structure its tensions, speak with a mind that remembers its scars.
