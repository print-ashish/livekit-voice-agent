from app.database import SessionLocal
from app.models import Task


def add_task(user_id: int, text: str) -> str:
    with SessionLocal() as db:
        task = Task(user_id=user_id, text=text.strip())
        db.add(task)
        db.commit()
        return f"Added task: {text}"


def list_tasks(user_id: int) -> str:
    with SessionLocal() as db:
        tasks = (
            db.query(Task)
            .filter(Task.user_id == user_id, Task.done == False)
            .order_by(Task.created_at.desc())
            .limit(10)
            .all()
        )
        if not tasks:
            return "You have no open tasks."
        lines = [f"{i + 1}. {t.text}" for i, t in enumerate(tasks)]
        return "Your tasks: " + "; ".join(lines)


def complete_task(user_id: int, text: str) -> str:
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.user_id == user_id, Task.text.ilike(f"%{text}%"), Task.done == False)
            .first()
        )
        if not task:
            return f"No open task found matching '{text}'."
        task.done = True
        db.commit()
        return f"Marked complete: {task.text}"
