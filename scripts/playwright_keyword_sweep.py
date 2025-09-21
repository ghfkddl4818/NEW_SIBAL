#!/usr/bin/env python3
"""Manual-assisted keyword sweep for 네이버 쇼핑 (with retries)."""

import urllib.parse
from pathlib import Path

from playwright.sync_api import TimeoutError, sync_playwright

KEYWORDS = [
    "플레이그래이 테스트",
    "가방",
    "노트북",
    "키보드",
    "헤어 드라이어",
    "침구",
]

STORAGE = Path("playwright/storage_state.json")
OUTPUTS = Path("outputs/playwright")
OUTPUTS.mkdir(parents=True, exist_ok=True)

if not STORAGE.exists():
    raise SystemExit("storage_state.json missing. Run scripts/playwright_store_session.py first.")

print("Playwright manual sweep 시작. 안내에 따라 Enter/Q 입력을 진행해 주세요.")
print("캡챠가 뜨면 직접 풀고, 로딩이 오래 걸리는 경우 수동으로 새로고침 후 Enter.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=150)
    context = browser.new_context(storage_state=str(STORAGE))
    page = context.new_page()

    for idx, keyword in enumerate(KEYWORDS, 1):
        proceed = input(f"\n[{idx}/{len(KEYWORDS)}] '{keyword}' 검색을 시작하려면 Enter (중단하려면 q + Enter): ")
        if proceed.strip().lower() == "q":
            print("사용자 요청으로 스크립트를 종료합니다.")
            break

        encoded = urllib.parse.quote(keyword)
        url = f"https://search.shopping.naver.com/search/all?query={encoded}"
        print(f" - '{keyword}' 검색 페이지로 이동 중...")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_load_state("networkidle", timeout=60000)
        except TimeoutError:
            print("   ! 로딩이 오래 걸립니다. 브라우저에서 직접 새로고침한 뒤 Enter를 눌러 진행하세요.")
            input("   └ 새로고침 후 Enter...")

        if page.locator("div.content_error").count() > 0:
            print("   ! 봇 감지 페이지입니다. 캡챠를 풀고 Enter를 눌러주세요.")
            input("   └ 캡챠 해결 후 Enter...")
            page.wait_for_load_state("networkidle", timeout=60000)

        page.screenshot(path=OUTPUTS / f"manual_search_{idx}.png", full_page=True)
        print(f"   - 스크린샷 저장: manual_search_{idx}.png")

        dwell = input("   └ 다음 키워드로 넘어가려면 Enter (잠시 둘러보고 싶으면 숫자(초) 입력): ")
        if dwell.strip().isdigit():
            seconds = int(dwell)
            print(f"     {seconds}초 대기 후 자동 진행")
            page.wait_for_timeout(seconds * 1000)

    context.storage_state(path=STORAGE)
    browser.close()
    print("\n모든 검색을 종료했습니다. 세션이 업데이트되었습니다.")
