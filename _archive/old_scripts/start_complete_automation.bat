@echo off
chcp 65001 >nul 2>&1
title Complete Automation System
echo ==========================================
echo   Complete E-commerce Automation System
echo ==========================================
echo.
echo Full Workflow:
echo 1. Web Automation (Data Collection)
echo 2. File Organization
echo 3. AI Cold Email Generation
echo.
echo Starting Complete System...
echo.

cd /d "E:\VSC\all_in_one\all_in_one_new\all_in_one"
python "gui\complete_automation_gui.py"

echo.
echo System closed.
pause