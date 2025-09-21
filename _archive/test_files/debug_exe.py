#!/usr/bin/env python3
"""
EXE 실행 오류 디버깅
"""

import subprocess
import sys
import os
import time

def debug_exe():
    """EXE 실행하고 오류 캐치"""

    exe_path = "dist\\CompleteAutomation\\CompleteAutomation.exe"

    print("=== EXE 오류 디버깅 ===")
    print(f"EXE 경로: {exe_path}")
    print(f"EXE 존재: {os.path.exists(exe_path)}")

    if os.path.exists(exe_path):
        print(f"EXE 크기: {os.path.getsize(exe_path) / (1024*1024):.1f}MB")

    print("\n=== 실행 시도 ===")

    try:
        # EXE 실행하고 출력 캐치
        process = subprocess.Popen(
            [exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        print("프로세스 시작됨... 10초 대기 중")

        # 10초 대기
        time.sleep(10)

        # 프로세스 종료
        if process.poll() is None:
            print("프로세스가 아직 실행 중... 강제 종료")
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()

        # 출력 수집
        stdout, stderr = process.communicate(timeout=5)

        print("\n=== STDOUT ===")
        print(stdout if stdout else "(출력 없음)")

        print("\n=== STDERR ===")
        print(stderr if stderr else "(오류 없음)")

        print(f"\n종료 코드: {process.returncode}")

        if process.returncode == 0:
            print("✅ 정상 실행됨")
        else:
            print("❌ 오류로 종료됨")

    except Exception as e:
        print(f"❌ 실행 실패: {e}")

if __name__ == "__main__":
    debug_exe()