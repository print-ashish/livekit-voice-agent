from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import GOOGLE_REDIRECT_URI, JWT_EXPIRE_MINUTES, JWT_SECRET
from app.database import get_db
from app.models import User

COOKIE_NAME = "session"


def cookie_kwargs() -> dict:
    """Shared cookie options for set/delete (must match).

    When the API is HTTPS (e.g. Railway) but the frontend is another origin
    (localhost or Vercel), the session cookie must be Secure + SameSite=None
    or the browser won't send it on fetch(..., { credentials: "include" }).
    """
    cross_origin = GOOGLE_REDIRECT_URI.startswith("https://")
    return {
        "key": COOKIE_NAME,
        "path": "/",
        "httponly": True,
        "secure": cross_origin,
        "samesite": "none" if cross_origin else "lax",
    }


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except jwt.PyJWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        ) from err


def get_current_user(
    session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = session
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    user_id = decode_token(token)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
