@echo off
chcp 65001 >nul 2>&1
title Complete Automation System v2.0 (Latest)
echo ==========================================
echo   Complete E-commerce Automation v2.0
echo   🚀 최신 패치 적용 버전
echo ==========================================
echo.
echo ✅ 새로운 기능들:
echo   • Tesseract OCR (무료, 비용 50%% 절약)
echo   • API 안전장치 (비용/호출량 모니터링)
echo   • 발송대기 엑셀 관리 시스템
echo   • 환경변수 보안 강화
echo.
echo Starting Latest Version...
echo.

cd /d "E:\VSC\all_in_one\all_in_one_new\all_in_one"

REM 환경변수 확인
if "%VERTEX_PROJECT_ID%"=="" (
    echo [WARNING] VERTEX_PROJECT_ID 환경변수가 설정되지 않았습니다.
    echo 기본값으로 실행합니다...
    set VERTEX_PROJECT_ID=jadong-471919
)

echo [INFO] 프로젝트 ID: %VERTEX_PROJECT_ID%
echo.

REM 최신 EXE 실행
"dist\CompleteAutomation\CompleteAutomation.exe"

echo.
echo System closed.
pause