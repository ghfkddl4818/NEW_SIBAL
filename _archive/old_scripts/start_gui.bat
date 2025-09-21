@echo off
chcp 65001 >nul
title AI Cold Email Generator
echo ========================================
echo     AI Cold Email Generator Starting
echo ========================================
echo.
echo Starting GUI program...
echo.

cd /d "E:\VSC\all_in_one\all_in_one_new\all_in_one"
python "gui/coldmail_gui_v2.py"

echo.
echo Program finished.
pause