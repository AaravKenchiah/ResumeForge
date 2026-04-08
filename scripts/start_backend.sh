#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

python3 -m uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000
