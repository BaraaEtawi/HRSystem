## Rubix Chat API

A FastAPI-powered RAG assistant designed for company policy Q&A. It processes markdown policy documents into a local Chroma vector store and provides authenticated chat-based answers using either a local Ollama model (the default in this project) or a Hugging Face Transformers pipeline.

### Quickstart: commands from start to end
```powershell
# From project root

# 1) Setup
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2) Create .env (edit values as needed)
Copy-Item .env.example .env  # if available; otherwise create manually

# 3) (Optional) Start Ollama and pull model
ollama serve
ollama pull llama3.2:3b

# 4) Ingest data (ensure files are in the data/ folder)
python -m app.rag.ingest

# 5) Initialize the database
python -m app.init_db

# 6) Run the API server
uvicorn app.main:app --reload
```

- Open `http://127.0.0.1:8000/`.

- If you want to register, just write the name and password in the boxes and click Register.


### Prerequisites
- Python 3.10
- pip
- Optional (recommended default): Ollama running locally with a model (e.g., `llama3`)

### 1) Setup
```bash
# From project root
python -m venv venv
venv\Scripts\activate  # Windows PowerShell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Create .env
The app requires a `.env` file at the repository root. At minimum set `SECRET_KEY`. Other values have sensible defaults.

Minimal (Ollama backend - default):
```env
SECRET_KEY=change-me
# Database (SQLite default)
DATABASE_URL=sqlite:///./app.db

# CORS (comma-separated list)
CORS_ORIGINS=http://localhost:3000

# Embeddings / Vector store
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_DIR=./.chroma

# LLM backend: "ollama" (default) or "transformers"
LLM_BACKEND=ollama

# Ollama settings
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2:3b

# Optional generation controls (used mainly by transformers backend)
MAX_NEW_TOKENS=256
TEMPERATURE=0.2
```

Alternative (Transformers backend):
```env
SECRET_KEY=change-me
LLM_BACKEND=transformers
HF_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
MAX_NEW_TOKENS=256
TEMPERATURE=0.2
```

Notes:
- If `.env` is missing or invalid, the app will raise a startup error.
- Using `transformers` will download models on first run and requires more CPU/RAM.
- Using `ollama` requires the Ollama service to be running and the model available.

Start Ollama (example):
```bash
# Ensure the service is running and the model is present
ollama serve        # if not already running as a service
ollama pull llama3.2:3b  # once
```

check `.env.example`

### 3) Ingest policy data
This builds the Chroma vector index from the policy markdown files in `data/`.

**Important**: Ensure your policy/source data files are placed inside the `data/` folder before running the ingest command. Only files found under `data/` will be indexed.
```bash
python -m app.rag.ingest
# Example output: "Ingested <N> chunks into Chroma collection 'policies'"
```
If you change the source files, re-run the ingest command. To fully reset, delete the folder specified by `CHROMA_DIR` (default `./.chroma`) and ingest again.

### 4) Initialize the database
```bash
python -m app.init_db
```

### 5) Run the API server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open `http://127.0.0.1:8000/docs` for interactive Swagger UI.

Static pages are served from `static/` at the root path: `http://127.0.0.1:8000/`.

### 6) Quick auth + chat walkthrough
1. Register a user
   - POST `http://127.0.0.1:8000/api/v1/auth/register`
   - Body:
     ```json
     {"email": "user@example.com", "full_name": "Test User", "password": "StrongPass123"}
     ```
2. Login to get a token
   - POST `http://127.0.0.1:8000/api/v1/auth/login`
   - Body:
     ```json
     {"email": "user@example.com", "password": "StrongPass123"}
     ```
   - Copy the `access_token` from the response.
3. Call the chat endpoint
   - POST `http://127.0.0.1:8000/api/v1/chat/`
   - Header: `Authorization: Bearer <access_token>`
   - Body:
     ```json
     {"question": "What is the sick leave policy?"}
     ```

### 7) Run tests
```bash
pytest -q
```

### Logs
- Rotating logs are written to `logs/app.log` (directory is auto-created at runtime).

### Project structure (high level)
```
app/
  api/v1/        # Auth and Chat endpoints
  core/          # Config, logging, security
  db/            # SQLAlchemy engine and base
  models/        # ORM models (e.g., User)
  rag/           # Ingestion, vector store, classifier, generator
  schemas/       # Pydantic models
  main.py        # FastAPI app entry
data/            # Policy markdown sources
static/          # Simple UI
tests/           # Unit tests
```

### Troubleshooting
- "`.env not found`": Create `.env` in the project root (see above).
- "vector store unavailable/timeout": Ensure ingestion has been run and `CHROMA_DIR` is accessible.
- Ollama errors: Ensure the service is running and `OLLAMA_HOST` is reachable; pull the model.
- Slow or memory issues with Transformers: switch to `LLM_BACKEND=ollama` or use a smaller model.

