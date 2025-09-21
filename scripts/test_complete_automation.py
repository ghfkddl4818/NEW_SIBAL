#!/usr/bin/env python3
"""
완전 자동화 시작 오류 디버깅 스크립트
"""

import sys
import os
from pathlib import Path
import traceback

# 환경변수 설정
os.environ['VERTEX_PROJECT_ID'] = 'jadong-471919'

# 프로젝트 루트 기준으로 실행되도록 보정
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))
os.chdir(root_dir)

def main():
    try:
        print("=== 완전 자동화 시작 오류 디버깅 ===")
        print("1. 모듈 임포트 테스트...")

        from ultimate_automation_system import UltimateAutomationSystem
        print("   - UltimateAutomationSystem 임포트 성공")

        print("2. 시스템 초기화 테스트...")
        system = UltimateAutomationSystem()
        print("   - 시스템 초기화 성공")

        print("3. 사전 체크 테스트...")
        pre_check = system.pre_automation_check()
        print(f"   - 사전 체크 결과: {pre_check}")

        if not pre_check:
            print("   - 사전 체크 실패로 인해 자동화 시작 불가")

            # 구체적인 문제점 확인
            print("\n4. 상세 문제점 분석...")

            # 이미지 파일 체크
            print("   - 이미지 파일들:")
            missing_images = []
            for name, path in system.image_files.items():
                exists = os.path.exists(path)
                print(f"     {name}: {path} ({'존재' if exists else '누락'})")
                if not exists:
                    missing_images.append(name)

            if missing_images:
                print(f"   - 누락된 이미지: {missing_images}")

            # 설정 파일 체크
            config_exists = os.path.exists(system.config_path)
            print(f"   - 설정 파일: {system.config_path} ({'존재' if config_exists else '누락'})")

            # 폴더 체크
            if hasattr(system, 'download_path_var'):
                download_path = system.download_path_var.get()
                download_exists = os.path.exists(download_path)
                print(f"   - 다운로드 폴더: {download_path} ({'존재' if download_exists else '누락'})")
        else:
            print("   - 사전 체크 통과! 자동화 시작 가능")

        print("\n5. 완전 자동화 시작 함수 테스트...")
        try:
            # dry-run으로 실제 실행하지 않고 함수 호출 가능성만 테스트
            print("   - start_complete_automation 함수 존재 확인")
            if hasattr(system, 'start_complete_automation'):
                print("   - start_complete_automation 함수 존재")
            else:
                print("   - start_complete_automation 함수 누락!")

        except Exception as e:
            print(f"   - 완전 자동화 함수 테스트 실패: {e}")

    except Exception as e:
        print(f"오류 발생: {e}")
        print("\n상세 오류 정보:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
