#!/bin/bash
# -*- coding: utf-8 -*-
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "========================================"
echo "  COVID-19 Data Explorer - Extended"
echo "========================================"
echo ""

# 使用上级目录的虚拟环境
source "$DIR/../.venv/bin/activate"

echo "Starting server, please wait..."
echo "Open http://127.0.0.1:8051 when you see 'Dash is running'"
echo ""

(sleep 3 && open http://127.0.0.1:8051) &

python3 app_extended.py
