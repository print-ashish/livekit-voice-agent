# Voice Agent — Hiring Task Demo

Voice-driven AI assistant with **Google OAuth**, **LiveKit** real-time voice, and **Groq** LLM/STT.

## Architecture

```
Browser (React) → FastAPI (auth + JWT) → LiveKit Cloud ← agent.py worker
                                              ↓
                                    Groq STT/LLM + Edge TTS
                                    Tools: calendar, tasks (SQLite)
```

## Project structure

```
agent-demo/
├── app/                    # FastAPI backend
│   ├── main.py             # App entry
│   ├── auth_routes.py      # Google OAuth + JWT
│   ├── livekit_routes.py   # Protected LiveKit token
│   ├── security.py         # JWT helpers
│   ├── models.py           # User, Task
│   └── services/
│       ├── tasks.py        # Task CRUD
│       └── calendar.py     # Google Calendar API
├── agent.py                # LiveKit voice worker
├── assistant.py            # VoiceAssistant + @function_tool
├── edge_tts_plugin.py      # Free TTS
└── frontend/               # React + Vite
```

## Setup

### 1. Python environment

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env — add LiveKit, Groq, Google OAuth, JWT_SECRET
```

### 2. Frontend

```powershell
cd frontend
copy .env.example .env
npm install
```

### 3. Google Cloud Console (when you have creds)

1. Create OAuth 2.0 Web client
2. Authorized redirect URI: `http://localhost:8000/auth/callback`
3. Enable **Google Calendar API**
4. Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to `.env`

## Run (3 terminals)

```powershell
# Terminal 1 — API
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2 — voice agent (start before connecting)
python agent.py dev

# Terminal 3 — frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** → Sign in with Google → Connect & talk.

## Voice commands to try

- "What are my tasks?"
- "Add a reminder to buy groceries"
- "Book a meeting tomorrow at 4 PM called Team sync" (needs Calendar scope)
- "What's on my calendar today?"

## Environment variables

See [`.env.example`](.env.example) and [`frontend/.env.example`](frontend/.env.example).

## Notes

- **STT/TTS** run in `agent.py` via Groq + Edge TTS — no LiveKit Cloud AI config needed.
- **Calendar** requires Google login with `calendar.events` scope (re-login after adding scope).
- **Groq Orpheus TTS** needs terms acceptance; we use Edge TTS instead (free).

## Deploy on Render (API + Agent)

The repo includes [`render.yaml`](render.yaml) (Blueprint) and a [`Dockerfile`](Dockerfile).

### Architecture on Render

| Service | Render type | Command |
|---------|-------------|---------|
| `agent-demo-api` | Web | `uvicorn app.main:app` |
| `agent-demo-agent` | Worker | `python agent.py start` |
| `agent-demo-db` | Postgres | shared by both |

Both Python services use the **same Postgres** (SQLite does not work across two containers).

### Option A — Blueprint (recommended)

1. Push this repo to GitHub.
2. Render Dashboard → **New** → **Blueprint** → connect repo.
3. Render creates 3 resources: API, Agent worker, Postgres.
4. After create, open **each service** → **Environment** and set:

   | Variable | Example |
   |----------|---------|
   | `LIVEKIT_URL` | `wss://….livekit.cloud` |
   | `LIVEKIT_API_KEY` | from LiveKit Cloud |
   | `LIVEKIT_API_SECRET` | from LiveKit Cloud |
   | `GROQ_API_KEY` | from Groq |
   | `GOOGLE_CLIENT_ID` | Google Cloud Console |
   | `GOOGLE_CLIENT_SECRET` | Google Cloud Console |
   | `GOOGLE_REDIRECT_URI` | `https://<api-host>.onrender.com/auth/callback` |
   | `FRONTEND_URL` | `https://<your-vercel-app>.vercel.app` (API service only) |

   Copy the same LiveKit/Groq/Google values onto **both** API and Agent services.

5. **Google Cloud Console** — add:
   - Authorized redirect URI: `https://<api-host>.onrender.com/auth/callback`
   - Authorized JavaScript origin: your Vercel frontend URL

6. Deploy frontend on Vercel with `VITE_API_URL=https://<api-host>.onrender.com`

7. Smoke test: `https://<api-host>.onrender.com/health` → `{"status":"ok"}`

**Note:** The agent worker uses Render **Starter** plan ($7/mo) — free tier has no background workers. The API can stay on **Free** (cold starts ~30s).

### Option B — Manual (two services in dashboard)

**Service 1 — API (Web)**

- Runtime: **Docker** (or Python 3.12)
- Dockerfile path: `./Dockerfile`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`

**Service 2 — Agent (Background Worker)**

- Same repo + Dockerfile
- Start command: `python agent.py start`
- Same env vars as API (except `FRONTEND_URL` / `GOOGLE_REDIRECT_URI` not needed on agent)

**Database:** Create a Render Postgres instance and set `DATABASE_URL` on both services (Blueprint does this automatically).

### Option C — Free tier hack (one web service)

Run API + agent in **one** container (demo only):

- Start command: `bash scripts/start-combined.sh`
- Use SQLite or attach Postgres
- Agent spins down when API spins down (same cold-start issue)

### After deploy

```powershell
# Terminal — agent worker logs (Render dashboard → agent-demo-agent → Logs)
# Look for: registered worker / connected to LiveKit

# Test voice: login on Vercel → tap mic → agent should join within a few seconds
```

## Deploy on Railway (API + Agent)

Same architecture as Render — **two services + Postgres**, same [`Dockerfile`](Dockerfile).

| Service | Config file | Start command |
|---------|-------------|---------------|
| `agent-demo-api` | [`railway.api.toml`](railway.api.toml) | `uvicorn app.main:app` |
| `agent-demo-agent` | [`railway.agent.toml`](railway.agent.toml) | `python agent.py start` |
| Postgres | Railway plugin | `DATABASE_URL` shared |

### Steps

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub** → select this repo.
2. **Add Postgres:** Project → **+ New** → **Database** → **PostgreSQL**.
3. **Add API service** (if not auto-created):
   - **+ New** → **GitHub Repo** → same repo
   - **Settings** → **Config file path** → `railway.api.toml`
   - **Settings** → **Networking** → **Generate Domain**
4. **Add Agent service:**
   - **+ New** → **GitHub Repo** → same repo again
   - **Settings** → **Config file path** → `railway.agent.toml`
   - No public domain needed (worker has no HTTP)
5. **Link Postgres to both services:**
   - Open API service → **Variables** → **Add Reference** → `DATABASE_URL` from Postgres
   - Same on Agent service
6. **Set env vars** on both services:

   ```
   LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
   GROQ_API_KEY, GROQ_LLM_MODEL=openai/gpt-oss-120b
   AGENT_NAME=voice-agent
   GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
   USER_TIMEZONE=Asia/Kolkata
   ```

   API only:

   ```
   FRONTEND_URL=https://your-app.vercel.app
   GOOGLE_REDIRECT_URI=https://<api-domain>.up.railway.app/auth/callback
   JWT_SECRET=<random-secret>
   ```

7. **Google Console** — redirect URI + JS origin (same as Render).
8. **Vercel** — `VITE_API_URL=https://<api-domain>.up.railway.app`

### Railway vs Render (quick)

| | Railway | Render |
|---|---------|--------|
| Multi-service from one repo | 2 services, different `railway.*.toml` | `render.yaml` Blueprint |
| Agent worker | Second service (always-on on paid) | Background Worker (Starter $7) |
| Cold start | Less painful on Hobby | Free API spins down ~15 min |
| Postgres | Plugin, reference `DATABASE_URL` | Blueprint creates DB |

### One-service demo (Railway)

Single service, start command: `bash scripts/start-combined.sh` — API + agent in one container.
