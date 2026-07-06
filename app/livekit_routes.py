import uuid

from fastapi import APIRouter, Depends, HTTPException
from livekit import api

from app.config import AGENT_NAME, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL
from app.models import User
from app.security import get_current_user

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/livekit/token")
def livekit_token(user: User = Depends(get_current_user)):
    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        raise HTTPException(status_code=503, detail="LiveKit not configured")

    room = f"user-{user.id}-{uuid.uuid4().hex[:8]}"

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(f"user-{user.id}")
        .with_name(user.name or user.email)
        .with_attributes({"user_id": str(user.id)})
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .with_room_config(
            api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name=AGENT_NAME)]
            )
        )
        .to_jwt()
    )

    return {"token": token, "url": LIVEKIT_URL, "room": room}
