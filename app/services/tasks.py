from app.database import SessionLocal
from app.models import Task


def get_open_tasks(user_id: int) -> list[dict]:
    with SessionLocal() as db:
        rows = (
            db.query(Task)
            .filter(Task.user_id == user_id, Task.done == False)
            .order_by(Task.created_at.desc())
            .limit(20)
            .all()
        )
        return [
            {
                "id": t.id,
                "text": t.text,
                "done": t.done,
                "created_at": t.created_at.isoformat(),
            }
            for t in rows
        ]


def add_task(user_id: int, text: str) -> str:
    with SessionLocal() as db:
        task = Task(user_id=user_id, text=text.strip())
        db.add(task)
        db.commit()
        db.refresh(task)
        return f"Added task (id {task.id}): {text}"


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
        lines = [f"id {t.id}: {t.text}" for t in tasks]
        return "Your tasks: " + "; ".join(lines)


def complete_task(user_id: int, task_id: int) -> str:
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.user_id == user_id, Task.done == False)
            .first()
        )
        if not task:
            return f"No open task found with id {task_id}."
        task.done = True
        db.commit()
        return f"Marked complete (id {task.id}): {task.text}"
