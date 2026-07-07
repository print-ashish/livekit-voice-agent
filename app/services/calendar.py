from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, USER_TIMEZONE
from app.database import SessionLocal
from app.models import User


def _get_user(user_id: int) -> User | None:
    with SessionLocal() as db:
        return db.get(User, user_id)


def _calendar_service(user_id: int):
    user = _get_user(user_id)
    if not user or not user.google_refresh_token:
        return None, user
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return None, user

    creds = Credentials(
        token=None,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    return build("calendar", "v3", credentials=creds), user


def _parse_date_time(date: str, time: str) -> datetime:
    """Parse YYYY-MM-DD and HH:MM in USER_TIMEZONE."""
    tz = ZoneInfo(USER_TIMEZONE)
    cleaned_time = time.strip().upper().replace(".", "")

    # Support 4 PM style if model passes it
    for fmt in ("%H:%M", "%I:%M %p", "%I %p"):
        try:
            parsed_time = datetime.strptime(cleaned_time, fmt).time()
            parsed_date = _normalize_booking_date(date.strip(), datetime.now(tz))
            return datetime.combine(parsed_date, parsed_time, tzinfo=tz)
        except ValueError:
            continue

    raise ValueError(f"Could not parse date '{date}' and time '{time}'.")


def _normalize_booking_date(date_str: str, now: datetime) -> date:
    """Fix common LLM mistake: wrong year (e.g. 2025-07-10 when today is 2026-07-08)."""
    parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = now.date()

    if parsed.year < today.year:
        parsed = parsed.replace(year=today.year)

    if parsed < today:
        next_year = parsed.replace(year=parsed.year + 1)
        if next_year >= today:
            return next_year

    return parsed


def create_event(
    user_id: int,
    title: str,
    date: str,
    time: str,
    agenda: str = "",
    duration_minutes: int = 60,
    attendee_emails: str = "",
) -> str:
    """
    Book a Google Calendar event.
    date: YYYY-MM-DD, time: HH:MM (24h) or e.g. 4:00 PM
    """
    title = title.strip()
    agenda = agenda.strip()

    missing = []
    if not title:
        missing.append("meeting title")
    if not date.strip():
        missing.append("date")
    if not time.strip():
        missing.append("time")
    if not agenda:
        missing.append("agenda or purpose")

    if missing:
        return (
            "Cannot book yet — still need: "
            + ", ".join(missing)
            + ". Ask the user for these before calling this tool again."
        )

    service, user = _calendar_service(user_id)
    if not service or not user:
        return (
            "Calendar is not connected. "
            "Please log out and sign in again with Google Calendar permission."
        )

    try:
        start = _parse_date_time(date, time)
    except ValueError as e:
        return str(e)

    if start < datetime.now(ZoneInfo(USER_TIMEZONE)) - timedelta(minutes=5):
        return (
            f"That slot ({date} {time}) is in the past. "
            f"Today is {datetime.now(ZoneInfo(USER_TIMEZONE)).strftime('%Y-%m-%d')}. "
            "Ask for a future date and time."
        )

    end = start + timedelta(minutes=duration_minutes)

    attendees = []
    if user.email:
        attendees.append({"email": user.email})
    for email in attendee_emails.split(","):
        email = email.strip()
        if email and email not in {a["email"] for a in attendees}:
            attendees.append({"email": email})

    body = {
        "summary": title,
        "description": agenda,
        "start": {"dateTime": start.isoformat(), "timeZone": USER_TIMEZONE},
        "end": {"dateTime": end.isoformat(), "timeZone": USER_TIMEZONE},
    }
    if attendees:
        body["attendees"] = attendees

    try:
        service.events().insert(
            calendarId="primary",
            body=body,
            sendUpdates="none",
        ).execute()
        when = start.strftime("%A %B %d at %I:%M %p")
        return (
            f"Booked '{title}' on {when} ({USER_TIMEZONE}). "
            f"Agenda: {agenda}. Duration: {duration_minutes} minutes."
        )
    except Exception as e:
        return f"Sorry, I could not book the event: {e}"


def get_today_schedule(user_id: int) -> str:
    service, _user = _calendar_service(user_id)
    if not service:
        return "Calendar is not connected. Please sign in with Google Calendar access."

    tz = ZoneInfo(USER_TIMEZONE)
    now = datetime.now(tz)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    try:
        events = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                timeZone=USER_TIMEZONE,
            )
            .execute()
            .get("items", [])
        )
    except Exception as e:
        return f"Could not fetch calendar: {e}"

    if not events:
        return "You have nothing on your calendar today."

    parts = []
    for ev in events[:5]:
        start = ev["start"].get("dateTime", ev["start"].get("date", ""))
        summary = ev.get("summary", "Event")
        parts.append(f"{summary} at {start}")
    return "Today's schedule: " + "; ".join(parts)
