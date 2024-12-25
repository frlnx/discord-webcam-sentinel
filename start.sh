#!/bin/bash
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    deactivate
fi
source .venv/bin/activate
python3 script.py
