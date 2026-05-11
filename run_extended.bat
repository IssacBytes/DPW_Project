@echo off
chcp 65001 >nul
title COVID-19 Data Explorer - Extended Edition

echo ================================================
    COVID-19 Data Explorer - Extended Edition
    (13 Tabs: Pipeline, Overview, Global Trends,
     Country Comparison, Deep Dive, Rankings,
     Correlation, Continent, Moving Avg, Anomalies,
     Fatality, Lead-Lag, Clusters)
================================================
echo.

cd /d "%~dp0"

echo [1/2] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [2/2] Starting server, please wait...
echo.
echo Open http://127.0.0.1:8051 in your browser
echo.

start "" http://127.0.0.1:8051

python app_extended.py

pause
