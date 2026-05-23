#!/bin/bash
# -*- coding: utf-8 -*-

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

clear
echo ""
echo " ╔═══════════════════════════════════════════╗"
echo " ║   COVID-19 Data Explorer (Extended)       ║"
echo " ║   13 Tabs: Pipeline, Overview, Global...  ║"
echo " ╚═══════════════════════════════════════════╝"
echo ""

echo " [1/2] Activating virtual environment..."
source "$DIR/.venv/bin/activate"

echo " [2/2] Starting server, please wait..."
echo ""
echo "   Open http://127.0.0.1:8051 in your browser"
echo ""

# 等3秒后自动打开浏览器
(sleep 3 && open http://127.0.0.1:8051) &

python3 app_extended.py
