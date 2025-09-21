@echo off
chcp 65001 >nul 2>&1
title AI Cold Email Unified System
echo ==========================================
echo   AI Cold Email Unified System
echo ==========================================
echo.
echo All-in-One Interface:
echo - 2-Stage Processing (Recommended)
echo - Quick Processing
echo - Settings & Management
echo.
echo Starting Unified GUI...
echo.

cd /d "E:\VSC\all_in_one\all_in_one_new\all_in_one"
python "gui\unified_gui.py"

echo.
echo GUI closed.
pause