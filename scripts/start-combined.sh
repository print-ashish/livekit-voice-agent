#!/usr/bin/env bash
# Run API + agent in one container (free Render web tier — demo only).
set -euo pipefail

python agent.py start &
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
