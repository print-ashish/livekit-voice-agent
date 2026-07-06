FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY assistant.py agent.py edge_tts_plugin.py ./

RUN mkdir -p data
# Pre-download LiveKit agent models (helps Railway agent worker start reliably)
RUN python agent.py download-files

# Overridden per service in render.yaml (api vs agent)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
