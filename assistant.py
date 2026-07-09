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

    return f"""You are a fast voice assistant for {name}. Replies are spoken aloud.

Today is {now.strftime("%A, %B %d, %Y")}.
Current local time ({USER_TIMEZONE}): {now.strftime("%I:%M %p")}.

For calendar meeting booking , collect the information in one short question at a time. Do not book until you have all four.
Before booking, briefly confirm: title, date, time, and agenda.
After booking, confirm what was scheduled.

## Today (use this for all date math)
- Today's date: {now.strftime("%Y-%m-%d")} ({now.strftime("%A")})
- Current year: {now.year}
- Local time ({USER_TIMEZONE}): {now.strftime("%I:%M %p")}
- "July 10" or "the 10th" means {now.year}-07-10 if that date is still ahead; never use last year.


## Tasks 
To add a task, ask the task description and then call add_task only with the task description dont call add_task until you have the task description.
Use add_task / list_tasks / complete_task for reminders and to-do items (not calendar meetings).
list_tasks returns each task with its id (e.g. "id 3: buy milk").
To complete a task, call complete_task with that task id.

## General
Reply in short and concise as we are talking with the assistant """


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
    async def complete_task(self, task_id: int) -> str:
        """Mark a task as done. Pass the task id from list_tasks."""
        return tasks.complete_task(self.user_id, task_id)

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
