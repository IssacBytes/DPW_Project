@echo off
chcp 65001 >nul
title COVID-19 Data Explorer

echo ========================================
echo   COVID-19 Data Explorer
echo   Starting...
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Loading data and starting server...
start "" http://127.0.0.1:8050

py app.py

pause
