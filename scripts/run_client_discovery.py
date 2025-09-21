#!/usr/bin/env python3
"""
고객사 발굴 전용 실행기
네이버 쇼핑 고객사 발굴 크롤링만 실행
"""

import sys
import os
from pathlib import Path
import json

# 스크립트 위치 기준으로 프로젝트 루트 경로 추가
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))

# 상대 경로가 항상 루트 기준으로 동작하도록 보정
os.chdir(root_dir)

def main():
    try:
        # 환경 변수 설정
        os.environ['VERTEX_PROJECT_ID'] = 'jadong-471919'

        print("=== 네이버 쇼핑 고객사 발굴 크롤러 ===")
        print("OCR 기반 실시간 크롤링 시스템")

        # 설정 확인
        config_path = "client_discovery/config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            print(f"설정 로드 완료:")
            print(f"  - 대상 제품 수: {config.get('search', {}).get('max_products', 'N/A')}개")
            print(f"  - 최소 리뷰 수: {config.get('filter', {}).get('min_review_count', 'N/A')}개")
            print(f"  - 최소 관심고객 수: {config.get('filter', {}).get('min_interest_count', 'N/A')}명")

        print("\n크롤링을 시작하시겠습니까?")
        print("브라우저에서 네이버 쇼핑 검색 페이지를 열어주세요.")

        start = input("\n시작하려면 Enter 키를 누르세요... ")

        from client_discovery.main_crawler import NaverShoppingCrawler

        print("\n[시작] 고객사 발굴 크롤링 시작...")
        crawler = NaverShoppingCrawler()
        result = crawler.run()

        status = (result or {}).get("status", "unknown")
        message = (result or {}).get("message", "")
        if status == "success":
            saved = result.get("saved_count", 0)
            visited = result.get("visited_count", 0)
            print(f"\n[완료] 저장 {saved}건 / 방문 {visited}건")
            csv_path = result.get("csv_path")
            if csv_path:
                print(f"결과 파일: {csv_path}")
        else:
            print(f"\n[종료] 상태: {status} - {message}")

    except Exception as e:
        print(f"[오류] 실행 실패: {e}")
        import traceback
        traceback.print_exc()

    input("\n아무 키나 눌러 종료...")

if __name__ == "__main__":
    main()
