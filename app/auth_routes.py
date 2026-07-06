import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import (
    FRONTEND_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
)
from app.database import get_db
from app.models import User
from app.security import cookie_kwargs, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth_states: dict[str, bool] = {}


def _google_configured() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


@router.get("/google")
def login_google():
    if not _google_configured():
        raise HTTPException(
            status_code=503,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env",
        )

    state = secrets.token_urlsafe(16)
    _oauth_states[state] = True

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/callback")
async def auth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        return RedirectResponse(f"{FRONTEND_URL}/login?error={error}")

    if not code or not state or state not in _oauth_states:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=invalid_state")
    del _oauth_states[state]

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            return RedirectResponse(f"{FRONTEND_URL}/login?error=token_exchange_failed")

        tokens = token_res.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            return RedirectResponse(f"{FRONTEND_URL}/login?error=userinfo_failed")

        info = user_res.json()

    google_sub = info["sub"]
    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        user = User(
            google_sub=google_sub,
            email=info.get("email", ""),
            name=info.get("name", ""),
            picture=info.get("picture"),
        )
        db.add(user)
    else:
        user.email = info.get("email", user.email)
        user.name = info.get("name", user.name)
        user.picture = info.get("picture", user.picture)

    if refresh_token:
        user.google_refresh_token = refresh_token

    db.commit()
    db.refresh(user)

    response = RedirectResponse(f"{FRONTEND_URL}/assistant")
    response.set_cookie(
        value=create_token(user.id),
        max_age=60 * 60 * 24,
        **cookie_kwargs(),
    )
    return response


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }


@router.post("/logout")
def logout():
    response = Response(status_code=204)
    response.delete_cookie(**cookie_kwargs())
    return response
