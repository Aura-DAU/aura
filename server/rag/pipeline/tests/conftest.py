"""
Configures env vars and sys.path for all test modules.
Updated for SSO architecture: AURA_JWT_SECRET removed (FastAPI no longer
issues its own JWTs). Added INTERNAL_JWT_SECRET and INTERNAL_RESOLVE_SECRET.
"""

import os, sys, uuid
from pathlib import Path
from cryptography.fernet import Fernet

RAG_DIR    = Path(__file__).resolve().parent.parent.parent   # server/rag
SERVER_DIR = RAG_DIR.parent                                    # server

for p in (str(RAG_DIR), str(SERVER_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

_run = uuid.uuid4().hex[:8]

# ── Auth (SSO architecture) ───────────────────────────────────────────────
# Shared secret between Next.js (mints JWT) and FastAPI (verifies JWT)
os.environ.setdefault("INTERNAL_JWT_SECRET",     "test-internal-secret-for-auth-middleware")
# Secret for /internal/resolve-identity endpoint — Next.js sends this header
os.environ.setdefault("INTERNAL_RESOLVE_SECRET", "test-resolve-secret")

# ── eCampus credential vault ──────────────────────────────────────────────
os.environ.setdefault("ECAMPUS_VAULT_KEY",        Fernet.generate_key().decode())
os.environ.setdefault("ECAMPUS_VAULT_DB",          f"/tmp/aura_test_vault_{_run}.db")
os.environ.setdefault("ECAMPUS_TIMETABLE_POOL_DB", f"/tmp/aura_timetable_{_run}.db")

# ── Misc ──────────────────────────────────────────────────────────────────
os.environ.setdefault("AURA_AUDIT_LOG",  f"/tmp/aura_test_audit_{_run}.log")
os.environ.setdefault("ECAMPUS_BASE_URL","https://ecampus.test.invalid")
os.environ.setdefault("GROQ_API_KEY",    "test-groq-key-unused-in-unit-tests")
os.environ.setdefault("PINECONE_API_KEY","test-pinecone-key-unused-in-unit-tests")
os.environ.setdefault("PINECONE_INDEX",  "test-pinecone-index-unused-in-unit-tests")
# vLLM / Qdrant (InferenceRouter / QdrantIndexAdapter) — unit tests mock the
# actual client calls, these just need to be present so client construction
# in __init__ doesn't raise.
os.environ.setdefault("VLLM_ENDPOINTS",  "http://localhost:8000/v1")
os.environ.setdefault("VLLM_MODEL",      "test-model-unused-in-unit-tests")
os.environ.setdefault("QDRANT_URL",      "http://localhost:6333")
os.environ.setdefault("QDRANT_COLLECTION","test-collection-unused-in-unit-tests")
# Leave ERP_DB_HOST unset → ERPConnector uses scrape mode
