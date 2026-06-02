#!/usr/bin/env bash
set -e
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn terminatori.api.app:app --host 0.0.0.0 --port ${PORT:-8000} --reload
