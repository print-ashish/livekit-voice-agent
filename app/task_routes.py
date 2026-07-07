from fastapi import APIRouter, Depends

from app.models import User
from app.security import get_current_user
from app.services import tasks

router = APIRouter(prefix="/api", tags=["tasks"])


@router.get("/tasks")
def list_tasks(user: User = Depends(get_current_user)):
    return {"tasks": tasks.get_open_tasks(user.id)}
