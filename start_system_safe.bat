@echo off
setlocal
chcp 65001 >nul 2>&1

echo ======================================
echo    Ultimate Automation System
echo ======================================
echo.

rem Base directories
set "BASE_DIR=%~dp0"
set "DATA_DIR=%BASE_DIR%data"
set "DOWNLOAD_DIR=%BASE_DIR%downloads"
set "STORAGE_DIR=%DATA_DIR%\storage"
set "WORK_DIR=%DATA_DIR%\work"
set "COLDMAIL_DIR=%DATA_DIR%\coldmail"

rem Ensure folders exist
if not exist "%STORAGE_DIR%" mkdir "%STORAGE_DIR%"
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"
if not exist "%COLDMAIL_DIR%" mkdir "%COLDMAIL_DIR%"

rem Export environment variables for Python
set "WORK_DB_PATH=%STORAGE_DIR%\ecommerce_database.xlsx"
set "WORK_ROOT=%WORK_DIR%"
set "DOWNLOAD_DIR=%DOWNLOAD_DIR%"
set "COLDMAIL_ROOT=%COLDMAIL_DIR%"

rem Tesseract location
if not defined TESSERACT_CMD set "TESSERACT_CMD=E:\tesseract\tesseract.exe"
if exist "%TESSERACT_CMD%" (
    echo [INFO] Tesseract path: %TESSERACT_CMD%
) else (
    echo [WARNING] Tesseract executable not found at %TESSERACT_CMD%. OCR features will fail until this is fixed.
)

rem Vertex project
if not defined VERTEX_PROJECT_ID set "VERTEX_PROJECT_ID=jadong-471919"
echo [INFO] VERTEX_PROJECT_ID = %VERTEX_PROJECT_ID%

echo Starting integrated automation system...
echo - Web Automation
echo - AI Cold Email Generation
echo - Client Discovery Crawling
echo - File Organization
echo.

echo Starting GUI...
echo.

python "%BASE_DIR%ultimate_automation_system.py"

echo.
echo Program finished.
echo Press any key to exit...
pause >nul
endlocal
