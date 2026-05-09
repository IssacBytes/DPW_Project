@echo off
chcp 65001 >nul
title COVID-19 Data Explorer - Extended

echo ========================================
echo   COVID-19 Data Explorer - Extended
echo ========================================
echo.

cd /d "%~dp0"

echo Starting server, please wait...
echo Open http://127.0.0.1:8051 when you see "Dash is running"
echo.

C:\Users\Randy\Anaconda3\python.exe app_extended.py

pause
