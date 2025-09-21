import os
from pathlib import Path
import urllib.parse
import pytest

pytestmark = pytest.mark.e2e

SEARCH_KEYWORD = os.getenv("NAVER_PLAYWRIGHT_KEYWORD", "플레이그래이 테스트")

@pytest.mark.skipif(os.environ.get("RUN_PLAYWRIGHT") != "1", reason="Set RUN_PLAYWRIGHT=1 to enable Playwright flows")
def test_naver_shopping_search(auth_page):
    outputs_dir = Path("outputs/playwright")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    query = urllib.parse.quote(SEARCH_KEYWORD)
    search_url = f"https://search.shopping.naver.com/search/all?query={query}"

    auth_page.goto(search_url, wait_until="domcontentloaded")
    auth_page.wait_for_load_state("networkidle")
    auth_page.screenshot(path=outputs_dir / "shopping_search.png", full_page=True)

    if auth_page.locator("div.content_error").count() > 0:
        pytest.skip("Naver responded with bot-detection page; retry with refreshed session")

    assert "search/all" in auth_page.url
    result_links = auth_page.locator("a[class*='basicList_link__']")
    assert result_links.count() >= 1
