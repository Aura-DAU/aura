# AURA RAG & Backend Local Development Runbook

This guide helps you set up the AURA RAG backend and API Gateway locally.

## Prerequisites
- Python 3.11+
- PostgreSQL (Local or Supabase Cloud instance)
- FFMPEG (for audio transcription features)

## Setup Steps

### 1. Configure the Environment
1. Copy the `.env.example` file to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in the required credentials:
   - Provide your PostgreSQL connection string in `AUTH_DB_URL`.
   - Provide your Groq API key in `GROQ_API_KEY`.
   - Provide your Qdrant Cloud URL, API key, and collection name in `QDRANT_URL`, `QDRANT_API_KEY`, and `QDRANT_COLLECTION`.

### 2. Set Up Python Virtual Environment
Create a virtual environment and install the required dependencies:
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run Database Migrations
Run the migration script to set up all tables (including auth schema and latency logs):
```bash
python db/migrate.py
```

### 4. Start the Development Server
Run the FastAPI development server:
```bash
uvicorn api.api:app --host 127.0.0.1 --port 8000 --reload
```

## Running Verification Tests
Ensure everything works as expected by running the pytest suite:
```bash
pytest
```
