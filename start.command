#!/bin/bash
cd "$(dirname "$0")"

if [ ! -x .venv/bin/streamlit ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

(sleep 4 && open "http://localhost:8501") &
exec .venv/bin/streamlit run app.py --server.port 8501 --server.headless true
