@echo off
echo === EXE 디버깅 (콘솔 모드) ===
echo.

set VERTEX_PROJECT_ID=jadong-471919
echo 환경변수 설정: %VERTEX_PROJECT_ID%
echo.

echo EXE 실행 중...
"dist\CompleteAutomation\CompleteAutomation.exe"

echo.
echo 프로그램 종료됨. 아무 키나 누르세요...
pause