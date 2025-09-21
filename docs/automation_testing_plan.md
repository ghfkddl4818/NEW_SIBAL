# Automation & Testing Plan

## Goals
- Provide reliable, repeatable automation for the "고객사 찾기 → 데이터 정리 → AI 콜드메일" workflow.
- Build a layered testing strategy (unit → integration → E2E) that can be triggered locally, via MCP, and on CI.
- Keep high-risk steps (API usage, account-sensitive work) behind manual approval switches.

## Current Snapshot
- `client_discovery` modules support keyword-driven crawling with filters and CSV output.
- Unit tests cover the LLM pipeline plus `FilterManager` logic.
- Playwright + pytest scaffolding is in place; browsers are installed, and a session storage script captures 네이버 로그인 상태.
- `.github/workflows/tests.yml` runs the unit suite on every push/PR and exposes an optional manual E2E job.

## Work Packages
1. **Unit & Service Tests**
   - Extend pytest suite with fixtures/mocks so logic runs offline (OCR helpers, `FilterManager`, config parsing).
   - Unit cases live under `tests/unit/` (e.g., `test_filter_manager.py`).
2. **UI/E2E Automation**
   - Playwright flows under `tests/e2e/` simulate 네이버 쇼핑 navigation.
   - `scripts/playwright_store_session.py` stores cookies to `playwright/storage_state.json`; tests auto-skip if 세션이 없거나 네이버가 봇 감지를 반환합니다.
3. **Automation Orchestration**
   - `scripts/run_tests.py` (scoped runner) is exposed via MCP commands (`scripts/mcp/commands.json`).
   - GitHub Actions uses the same runner to execute unit/E2E suites.
   - Paid API / production secrets stay behind manual approval toggles.
4. **CI/Reporting**
   - CI pipeline (`.github/workflows/tests.yml`) installs Playwright browsers and runs `python scripts/run_tests.py --scope unit` on push/PR.
   - `workflow_dispatch` can trigger the E2E job (`RUN_PLAYWRIGHT=1`, skips if 세션 없음).
   - Summaries/logs such as `outputs/test_summary.json` can be archived or fed to MCP/LLM for daily status.

## Artifacts Added
- `pytest.ini` for global configuration (`e2e`, `smoke` markers; asyncio mode; testpaths).
- `tests/unit/test_filter_manager.py` verifying blocklist/multi-store logic.
- `tests/e2e/test_playwright_smoke.py` basic Playwright readiness check.
- `tests/e2e/test_naver_search.py` search workflow (skips when 봇 감지 페이지가 나타남).
- `tests/e2e/conftest.py` fixture to load `playwright/storage_state.json`.
- `scripts/playwright_store_session.py` to capture 네이버 로그인 cookies.
- `scripts/run_tests.py` unified runner (`--scope unit|e2e|all`).
- `scripts/mcp/commands.json` mapping MCP commands to the runner.
- `requirements.txt` includes `pytest`, `pytest-asyncio`, `pytest-playwright`, `playwright`.
- `playwright/storage_state.json` (gitignored) stores the reusable session for E2E tests.
- `.github/workflows/tests.yml` runs tests automatically on CI.

## Next Steps
- Maintain 네이버 테스트 계정/cookie to bypass anti-bot page; once stable, assert on actual 상품 카드 셀렉터.
- Add artifact upload (HTML/JSON reports, screenshots) to CI jobs as needed.
- Wire Playwright results into the full automation GUI once login/search flow stabilises.
