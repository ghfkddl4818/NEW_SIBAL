@echo off
chcp 65001 >nul
title Master System - Complete Automation
echo ========================================
echo   Master System - Complete Automation
echo ========================================
echo.
echo Starting integrated system...
echo.

cd /d "E:\VSC\all_in_one\all_in_one_new\all_in_one"
python "gui/master_system.py"

echo.
echo System finished.
pause