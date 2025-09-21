@echo off
echo ======================================
echo   API 환경변수 설정 스크립트
echo ======================================

echo.
echo 현재 설정된 환경변수들:
echo VERTEX_PROJECT_ID: %VERTEX_PROJECT_ID%
echo GOOGLE_APPLICATION_CREDENTIALS: %GOOGLE_APPLICATION_CREDENTIALS%

echo.
echo 새로운 환경변수 설정 중...

REM Vertex AI 프로젝트 ID 설정
setx VERTEX_PROJECT_ID "your-project-id-here"

REM Google Cloud 인증 파일 경로 (필요시)
REM setx GOOGLE_APPLICATION_CREDENTIALS "C:\path\to\service-account.json"

echo.
echo ======================================
echo   환경변수 설정 완료!
echo ======================================
echo.
echo 주의사항:
echo 1. 설정이 적용되려면 새 터미널/CMD를 열어야 합니다
echo 2. 프로그램을 재시작해야 환경변수가 인식됩니다
echo.
echo 확인 방법:
echo   echo %%VERTEX_PROJECT_ID%%
echo.
pause