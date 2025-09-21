import os
import pytest

pytestmark = pytest.mark.e2e


@pytest.mark.skipif(
    os.environ.get("RUN_PLAYWRIGHT") != "1",
    reason="Set RUN_PLAYWRIGHT=1 to enable Playwright smoke tests",
)
def test_playwright_environment(page):
    page.goto("data:text/html,<html><body><h1>Playwright Ready</h1></body></html>")
    heading = page.text_content("h1")
    assert heading == "Playwright Ready"
