import pytest
from pathlib import Path

STORAGE_STATE = Path("playwright/storage_state.json")

@pytest.fixture(scope="session")
def storage_state():
    if not STORAGE_STATE.exists():
        pytest.skip("Playwright storage_state.json missing; run scripts/playwright_store_session.py")
    return str(STORAGE_STATE)

@pytest.fixture()
def auth_page(browser, storage_state):
    context = browser.new_context(storage_state=storage_state)
    page = context.new_page()
    yield page
    context.close()
