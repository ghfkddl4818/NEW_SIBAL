@echo off
echo ===== 완전 자동화 시스템 시작 =====
echo.

set VERTEX_PROJECT_ID=jadong-471919
echo 환경변수 설정: %VERTEX_PROJECT_ID%
echo.

echo GUI 실행 중...
python test_gui.py

echo.
echo 프로그램 종료됨.
pause