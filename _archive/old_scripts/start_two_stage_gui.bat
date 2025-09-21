@echo off
chcp 65001 >nul 2>&1
title AI Cold Email System
echo ==========================================
echo   AI Cold Email 2-Stage Processing System
echo ==========================================
echo.
echo Workflow: Stage 1 (OCR) - Stage 2 (Email)
echo Temperature: 0.3 (Google AI Studio Style)
echo.
echo Starting GUI...
echo.

cd /d "E:\VSC\all_in_one\all_in_one_new\all_in_one"
python "gui\two_stage_gui.py"

echo.
echo GUI closed.
pause