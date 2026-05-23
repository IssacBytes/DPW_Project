#!/bin/bash
# -*- coding: utf-8 -*-
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "========================================"
echo "  COVID-19 Data Explorer"
echo "  Starting..."
echo "========================================"
echo ""

echo "[1/2] Activating virtual environment..."
source "$DIR/.venv/bin/activate"

echo "[2/2] Loading data and starting server..."
open http://127.0.0.1:8050

python3 app.py
