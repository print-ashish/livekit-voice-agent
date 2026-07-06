from datetime import datetime
from zoneinfo import ZoneInfo

from livekit.agents import Agent, function_tool

from app.config import USER_TIMEZONE
from app.database import SessionLocal
from app.models import User
from app.services import calendar, tasks


def _load_user(user_id: int) -> User | None:
    with SessionLocal() as db:
        return db.get(User, user_id)


def _system_instructions(user: User | None) -> str:
    tz = ZoneInfo(USER_TIMEZONE)
    now = datetime.now(tz)
    name = user.name if user else "the user"

    return f"""You are a friendly voice assistant for {name}.
You speak out loud — keep replies short (1–2 sentences).

Today is {now.strftime("%A, %B %d, %Y")}.
Current local time ({USER_TIMEZONE}): {now.strftime("%I:%M %p")}.

## Booking a meeting
Before calling create_calendar_event you MUST have ALL of:
1. title — what the meeting is called
2. date — YYYY-MM-DD (convert "tomorrow", "next Monday", etc.)
3. time — local time e.g. 16:00 or 4:00 PM
4. agenda — purpose or topics for the meeting

If anything is missing, ask one clear question at a time. Do NOT book until you have all four.
Before booking, briefly confirm: title, date, time, and agenda.
After booking, confirm what was scheduled.

Optional: ask if anyone else should be invited; pass their emails as attendee_emails (comma-separated).
The user is always added as an attendee automatically.

## Tasks
Use add_task / list_tasks / complete_task for reminders and to-do items (not calendar meetings).

## General
When a tool fails, explain simply and ask how to fix it."""


class VoiceAssistant(Agent):
    """Voice agent with calendar and task tools."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = _load_user(user_id)
        super().__init__(instructions=_system_instructions(self.user))

    @function_tool
    async def add_task(self, text: str) -> str:
        """Add a task or reminder to the user's list (not a calendar meeting)."""
        return tasks.add_task(self.user_id, text)

    @function_tool
    async def list_tasks(self) -> str:
        """List the user's open tasks."""
        return tasks.list_tasks(self.user_id)

    @function_tool
    async def complete_task(self, text: str) -> str:
        """Mark a task as done. Pass part of the task text to match."""
        return tasks.complete_task(self.user_id, text)

    @function_tool
    async def create_calendar_event(
        self,
        title: str,
        date: str,
        time: str,
        agenda: str,
        duration_minutes: int = 60,
        attendee_emails: str = "",
    ) -> str:
        """Book a Google Calendar meeting. Requires title, date (YYYY-MM-DD), time (HH:MM or 4:00 PM), and agenda. Only call when all are known."""
        return calendar.create_event(
            user_id=self.user_id,
            title=title,
            date=date,
            time=time,
            agenda=agenda,
            duration_minutes=duration_minutes,
            attendee_emails=attendee_emails,
        )

    @function_tool
    async def get_today_schedule(self) -> str:
        """Get today's calendar events."""
        return calendar.get_today_schedule(self.user_id)
