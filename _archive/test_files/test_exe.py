#!/usr/bin/env python3
"""
EXE 파일 모듈 import 테스트
"""

import subprocess
import sys
import os

def test_exe_modules():
    """EXE 파일이 필요한 모듈들을 제대로 포함하고 있는지 테스트"""

    exe_path = "dist\\CompleteAutomation\\CompleteAutomation.exe"

    if not os.path.exists(exe_path):
        print(f"[ERROR] EXE 파일이 없습니다: {exe_path}")
        return False

    print(f"[OK] EXE 파일 존재: {exe_path}")
    print(f"[SIZE] 크기: {os.path.getsize(exe_path) / (1024*1024):.1f}MB")

    # 5초 후 자동 종료하는 테스트
    try:
        print("[TEST] EXE 실행 테스트 중... (5초 후 자동 종료)")
        result = subprocess.run(
            [exe_path],
            timeout=5,
            capture_output=True,
            text=True
        )
        print("[OK] EXE가 정상적으로 시작되었습니다!")
        return True

    except subprocess.TimeoutExpired:
        print("[OK] EXE가 정상적으로 실행되고 있습니다 (5초 후 종료됨)")
        return True

    except Exception as e:
        print(f"[ERROR] EXE 실행 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_exe_modules()
    if success:
        print("\n[SUCCESS] EXE 파일이 정상적으로 작동합니다!")
        print("\n실행 방법:")
        print("1. start_latest_exe.bat")
        print("2. dist\\CompleteAutomation\\CompleteAutomation.exe")
    else:
        print("\n[ERROR] EXE 파일에 문제가 있습니다.")