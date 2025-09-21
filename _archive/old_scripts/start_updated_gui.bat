@echo off
echo ===== 수정된 GUI 시스템 시작 =====
echo 개별 모듈 제어 버튼이 추가되었습니다.
echo.

set VERTEX_PROJECT_ID=jadong-471919
echo 환경변수 설정: %VERTEX_PROJECT_ID%
echo.

echo 새로운 GUI 실행 중...
echo - 고객사 발굴 탭에서 개별 모듈 버튼 확인하세요
echo.

python test_gui.py

echo.
echo 프로그램 종료됨.
pause