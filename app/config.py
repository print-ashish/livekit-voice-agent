import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

_raw_db = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'app.db'}")
# Render/Heroku Postgres URLs use postgres:// — SQLAlchemy needs postgresql://
if _raw_db.startswith("postgres://"):
    DATABASE_URL = _raw_db.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = _raw_db

# Google OAuth (fill in when ready)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback"
)
GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/calendar.events",
]

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# LiveKit
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
AGENT_NAME = os.getenv("AGENT_NAME", "voice-agent")

# Frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Groq LLM (STT stays on Groq)
GROQ_LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-120b")

# Cartesia TTS — low latency, separate from Groq rate limits
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")
CARTESIA_TTS_MODEL = os.getenv("CARTESIA_TTS_MODEL", "sonic-3")
CARTESIA_TTS_VOICE = os.getenv(
    "CARTESIA_TTS_VOICE", "6f84f4b8-58a2-430c-8c79-688dad597532"
)

# Turn-taking latency (LiveKit) — lower = snappier, may cut off slow speakers
AGENT_ENDPOINTING_MIN = float(os.getenv("AGENT_ENDPOINTING_MIN", "0.2"))
AGENT_ENDPOINTING_MAX = float(os.getenv("AGENT_ENDPOINTING_MAX", "0.8"))
AGENT_PREEMPTIVE_TTS = os.getenv("AGENT_PREEMPTIVE_TTS", "true").lower() in (
    "1",
    "true",
    "yes",
)
AGENT_VAD_ACTIVATION = float(os.getenv("AGENT_VAD_ACTIVATION", "0.4"))
AGENT_VAD_MIN_SILENCE = float(os.getenv("AGENT_VAD_MIN_SILENCE", "0.25"))

# Calendar / voice assistant timezone
USER_TIMEZONE = os.getenv("USER_TIMEZONE", "Asia/Kolkata")
