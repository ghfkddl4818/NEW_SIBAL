#!/usr/bin/env python3
"""
데이터 크롤링 전용 실행기
네이버 쇼핑 자료 수집만 실행
"""

import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))
os.chdir(root_dir)

def main():
    try:
        # (선택) 필요한 환경 변수는 실행 전에 외부에서 설정하세요.

        print("=== 네이버 쇼핑 데이터 크롤러 ===")
        print("1. 고객사 발굴 크롤링")
        print("2. 종료")

        choice = input("\n선택하세요 (1-2): ").strip()

        if choice == "1":
            from client_discovery.main_crawler import NaverShoppingCrawler

            print("\n고객사 발굴 크롤링을 시작합니다...")
            crawler = NaverShoppingCrawler()
            result = crawler.run()
            print(f"크롤링 완료: {result}")

        elif choice == "2":
            print("종료합니다.")
            return
        else:
            print("잘못된 선택입니다.")
            return

    except Exception as e:
        print(f"[오류] 실행 실패: {e}")
        import traceback
        traceback.print_exc()

    input("\n아무 키나 눌러 종료...")

if __name__ == "__main__":
    main()
