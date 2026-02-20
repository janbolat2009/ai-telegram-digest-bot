#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi
if [ -z "$1" ]; then
  echo "Usage: $0 morning|afternoon|memes"
  exit 2
fi
python run_task.py "$1"
