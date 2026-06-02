#!/usr/bin/env bash
set -e
pip install -r requirements.txt
exec uvicorn terminatori.api.app:app --host 0.0.0.0 --port ${PORT:-8000}
