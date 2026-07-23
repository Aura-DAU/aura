# 🚀 AURA PWA — Full Setup & Local Development Guide

Welcome to **AURA (Academic Unified Responsive Assistant)** — the AI-powered student assistant and timetable management system for Dhirubhai Ambani University (DAU / DA-IICT).

This guide covers everything you need to set up and run the complete stack (Next.js Frontend, FastAPI Backend, PostgreSQL Database, and RAG Pipeline) on your local computer from scratch.

---

## 📋 System Prerequisites

Ensure you have the following installed on your system before proceeding:

1. **Docker Desktop** (for running the PostgreSQL database container)
2. **Node.js** (v18.x or v20.x recommended)
3. **pnpm** (install via `npm install -g pnpm`)
4. **Python** (v3.10 or v3.12 recommended)
5. **Git**

---

## 🛠️ Step-by-Step Setup Guide

### Step 1: Unzip the Project
Extract the zip file to your preferred folder:
```powershell
# Example path:
cd C:\Users\madha\Documents\DAU-pwa
```

---

### Step 2: Set Up Environment Files (`.env`)

Copy the provided `.env.example` templates to create active `.env` files:

#### 1. Frontend Environment (`aura/.env`)
Copy `aura/.env.example` to `aura/.env`:
```ini
BACKEND_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
INTERNAL_JWT_SECRET=your_internal_jwt_secret_here
INTERNAL_RESOLVE_SECRET=your_internal_resolve_secret_here
```

#### 2. Backend Environment (`server/.env`)
Copy `server/.env.example` to `server/.env`:
```ini
AUTH_DB_URL=postgresql://aura_app@127.0.0.1:5433/aura_auth
GOOGLE_CALENDAR_CLIENT_ID=your_google_calendar_client_id_here
GOOGLE_CALENDAR_CLIENT_SECRET=your_google_calendar_client_secret_here
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:3000/api/calendar/callback
GOOGLE_CALENDAR_VAULT_KEY=your_fernet_encryption_key_here
INTERNAL_JWT_SECRET=your_internal_jwt_secret_here
INTERNAL_RESOLVE_SECRET=your_internal_resolve_secret_here
```

#### 3. RAG Pipeline Environment (`server/rag/.env`)
Copy `server/rag/.env.example` to `server/rag/.env`:
```ini
PINECONE_INDEX=dau-rag
PINECONE_API_KEY=your_pinecone_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

---

### Step 3: Start PostgreSQL Database Container (Docker)

1. Open **Docker Desktop**.
2. Run the following command in PowerShell:
```powershell
docker-compose up -d
```
3. Verify that the container is running:
```powershell
docker ps
```
*(You should see `aura_postgres` running on port `5433:5432`)*

---

### Step 4: Set Up Python Virtual Environment & Install Backend Dependencies

1. Create and activate a Python virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install required Python packages:
```powershell
pip install fastapi uvicorn psycopg2-binary pyjwt groq pinecone rank-bm25 sentence-transformers requests python-dotenv cryptography
```

---

### Step 5: Install Frontend Node.js Dependencies

In a new terminal window:
```powershell
cd aura
pnpm install
```

---

### Step 6: Seed Database Timetable Records & Users

Populate the database with Autumn 2026 timetable data and initial user maps:
```powershell
$env:AUTH_DB_URL="postgresql://aura_app@127.0.0.1:5433/aura_auth"
.\.venv\Scripts\python.exe server/db/import_timetable.py
```

---

## 🏃 Running the Application locally

### Terminal 1: Start FastAPI Backend Server
```powershell
cd server
..\.venv\Scripts\Activate.ps1
$env:AUTH_DB_URL="postgresql://aura_app@127.0.0.1:5433/aura_auth"
fastapi dev api/api.py
```
*(Backend will run on `http://127.0.0.1:8000`)*

### Terminal 2: Start Next.js Frontend Server
```powershell
cd aura
pnpm dev
```
*(Frontend will run on `http://localhost:3000`)*

---

## 🧪 Testing Features on `http://localhost:3000`

1. **Student Login & Auto-Cohort Detection**:
   - Go to `http://localhost:3000/login`.
   - Click **"Demo Student"** or sign in with a student email starting with admission year (e.g. `202401226@dau.ac.in`).
   - AURA automatically infers your cohort: **Year 3, Semester 5, Section A**!

2. **Managing Electives**:
   - On the Student Dashboard, click **"Manage / Change Electives"**.
   - Select your elective courses and click **Save**.
   - Your timetable instantly updates to display your chosen electives merged with your core classes!

3. **Interactive Timetable Editing in Chat**:
   - Ask AURA in chat:
     - 💬 *"What is my timetable?"*
     - 💬 *"Move my Monday 2 PM class to 4 PM in CEP-102"*
     - 💬 *"I am in Section B"* (Updates your section permanently in PostgreSQL!)

4. **Google Calendar Sync**:
   - Click **"Add classes to Google Calendar"** on the dashboard.
   - Connect your Google account and click **Sync** to automatically populate your primary Google Calendar!

---

## 🔍 Database Inspection Commands (PostgreSQL)

You can query the PostgreSQL database directly anytime:

```powershell
# View all users & saved cohorts
docker exec -it aura_postgres psql -U aura_app -d aura_auth -c "SELECT email, erp_id, role, current_year, current_sem, current_sec FROM user_identity_map;"

# View timetable master rows
docker exec -it aura_postgres psql -U aura_app -d aura_auth -c "SELECT course_code, course_name, day_of_week, start_time, room, faculty_name FROM timetable_master LIMIT 10;"

# View student elective selections
docker exec -it aura_postgres psql -U aura_app -d aura_auth -c "SELECT * FROM student_elective_selections;"
```
