from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth_routes import router as auth_router
from app.config import FRONTEND_URL
from app.database import init_db
from app.livekit_routes import router as api_router
from app.task_routes import router as task_router

app = FastAPI(title="Voice Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(api_router)
app.include_router(task_router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
