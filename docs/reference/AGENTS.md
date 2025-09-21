# Repository Guidelines

## Project Structure & Module Organization
주요 자동화 파이프라인은 `app/` 폴더의 Typer CLI와 `core/` 설정·로깅 유틸에서 시작하며, LLM 연동과 프롬프트 구성은 `llm/`에 정리되어 있습니다. GUI 및 리드 발굴 자동화는 `gui/`, `client_discovery/`가 담당하고, OCR 관련 도구는 `ocr/`에 있습니다. 제품 이미지·리뷰 CSV 등 입력 데이터는 `data/`, 생성된 메일과 로그는 `outputs/`에 저장되며, 전역 설정은 `config/`(`config.yaml`, `.env.example`)을 업데이트하면 됩니다. 실험·백업 자산은 `_archive/`에 있으니 참조만 하고 수정 시에는 별도 정리 PR을 권장합니다.

## Build, Test, and Development Commands
로컬 환경은 `python -m venv .venv`로 만들고 Windows에서는 `.venv\Scripts\activate`, WSL에서는 `source .venv/bin/activate`로 활성화합니다. `pip install -r requirements.txt`로 의존성을 설치한 뒤 `python -m app.main run --job-id demo_001`로 엔드투엔드 파이프라인을 검증하세요. Windows 배치 스크립트(`start_system_safe.bat`, `start_complete_system.bat`)는 동일 파이프라인을 GUI 자동화와 묶으므로 경로 하드코딩을 피하고 윈도 환경에서만 수정합니다. 입력 자산 검증은 `python verify_assets.py`, 리드 소싱 워크플로우는 `python run_client_discovery.py`로 실행합니다.

## Coding Style & Naming Conventions
Python 코드는 4칸 들여쓰기와 타입 힌트를 기본으로 하고, `app/main.py`처럼 간결한 모듈 docstring을 유지합니다. 모듈·함수·변수는 snake_case, 클래스와 Pydantic 모델은 CamelCase를 사용합니다. 로그는 `core/`의 loguru 래퍼를 통해 남겨 일관된 포맷을 유지하고, 설정 키 이름은 `AppConfig` 구조와 동일하게 맞춰 검증 오류를 예방합니다.

## Testing Guidelines
테스트는 `tests/`에 위치하며 `pytest`와 `pytest-asyncio`에 의존합니다. 파일명은 `test_*.py`, 코루틴 테스트는 `@pytest.mark.asyncio`와 함께 `test_*` 이름을 지킵니다. PR 전에는 `pytest -q`를 실행하고, 특정 흐름만 점검하려면 `pytest tests/test_pipeline_smoke.py -k run`을 활용하세요. LLM 호출을 모킹할 때는 `test_pipeline_smoke.py`의 패턴을 참고하고, 파일 시스템·네트워크·GUI 부작용이 생기면 고립된 fixture를 추가합니다.

## Commit & Pull Request Guidelines
커밋 메시지는 단일 책임으로 유지하고 현재시제 동사(`Add`, `Refactor`, `Fix`)로 시작합니다. 저장소 히스토리처럼 한국어·영어를 혼합해도 되며, 필요하면 텍스트 이모지 코드(`:rocket:` 등)를 덧붙일 수 있습니다. PR 본문에는 변경 요약, 관련 이슈나 TODO 링크, 실행한 테스트(`pytest -q`, 자산 검증 결과)를 명시합니다. GUI 혹은 생성물에 변동이 있으면 스크린샷이나 샘플 출력 경로를 첨부하고, `.env` 또는 `config.yaml` 변경 시 리뷰어가 바로 동기화할 수 있도록 강조하세요.
