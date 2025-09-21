# TODO for Claude

## 0. Decide Specification vs. Code Baseline
- Review the current implementation in `ultimate_automation_system.py:41-120` against the spec narrative in `완전통합자동화시스템_기술명세서_코딩버전.md:56-120`.
- Decide whether to (a) update the spec to describe the existing `UltimateAutomationSystem` UI, or (b) refactor the code to match the documented `FileOrganizerGUI` pattern (including the widgets/methods the spec expects).
- Document the decision so subsequent tasks know which target to follow.

## 1. GUI Class / Widget Parity
- If the spec is the target, implement `FileOrganizerGUI` (or rename the current class) with the buttons/status widgets referenced in the spec (`automation_button`, `update_status`, etc.) so it matches the flow in `완전통합자동화시스템_기술명세서_코딩버전.md:70-115`.
- Audit the UI tab creation logic so each tab mentioned in the spec exists with the same behaviour labels and wiring.
- Ensure all pyautogui-driven flows have matching GUI triggers (start, pause, resume, emergency stop) as described.

## 2. Pending Store FIFO & Duplicate-Control Logic
- Implement the FIFO helpers outlined in `완전통합자동화시스템_기술명세서_코딩버전.md:330-368` (`get_next_pending_store`, `clean_old_pending_stores`, `get_file_hash`). The current code only defines `self.pending_stores` but never uses it (`ultimate_automation_system.py:64`).
- Wire these helpers into the product processing pipeline so screenshots/reviews can be matched in order, and duplicate files are skipped.

## 3. Database Management Functions
- Implement database bootstrap/add/update routines that the spec assumes (`create_database_if_missing`, `add_to_database`, `update_database_entry`, `load_database` in `완전통합자동화시스템_기술명세서_코딩버전.md:404-431`).
- Make sure `pandas`/`openpyxl` imports in `ultimate_automation_system.py:31-33` are actually used by the implemented functions, or remove them if the behaviour moves elsewhere.
- Decide where the database file path should live so hard-coded `E:/업무/...` can be configured via the settings UI.

## 4. Asset Dependencies
- Collect the image templates referenced in the code (`detail_button.png`, `fireshot_save.png`, `analysis_start.png`, `excel_download.png` at `ultimate_automation_system.py:74-78`) and add them to `assets/` (or whichever directory the automation expects).
- Update paths to be relative to the project instead of hard-coded drive letters.
- Verify every `pyautogui.locateOnScreen` call has a real asset and an adjustable confidence value (spec suggests `button_confidence` / `context_confidence` settings at `완전통합자동화시스템_기술명세서_코딩버전.md:1108`).

## 5. Requirements Alignment
- Update `requirements.txt:1-11` to include the packages the spec and code actually require (`pyautogui`, `pyperclip`, `selenium`, `beautifulsoup4`, `requests`, etc., from `완전통합자동화시스템_기술명세서_코딩버전.md:1048-1070`).
- Reconcile the version pins with what the code uses today (e.g., `opencv-python`, `tiktoken` currently present; keep or remove as needed).

## 6. Configuration Files
- Align `config/config.yaml:1-39` with the keys referenced by the GUI (email policy sliders, prompt paths, file organizer thresholds). The spec references `policy.email_min_chars`, `file_organizer.max_scrolls`, `file_organizer.button_confidence`, etc. (`완전통합자동화시스템_기술명세서_코딩버전.md:1088-1110`).
- Align `client_discovery/config.json:1-40` with the documented fields (`selenium.driver_path`, `headless`, `window_size`, etc. at `완전통합자동화시스템_기술명세서_코딩버전.md:1115-1124`). Decide whether to keep the current PyAutoGUI-based config or convert to Selenium as described.
- Ensure the GUI settings tab surfaces these config values for editing if the spec expects it.

## 7. Safety Monitoring / Emergency Stop
- Implement the runtime/ memory/ emergency-stop checks from the spec (`완전통합자동화시스템_기술명세서_코딩버전.md:1176-1199`) inside a dedicated module.
- Reconcile with the existing `core/safety_monitor.py:1-80`, which currently tracks API usage only. Decide whether to merge responsibilities or separate API-cost tracking from automation safety monitoring.

## 8. End-to-End Validation
- After refactors, run the full automation flow (file collection → data organization → AI mail generation → client discovery) with sample assets to confirm integration between modules (`UltimateAutomationSystem`, `llm/two_stage_processor.py:1-80`, `compose/email_sender_manager.py`, `client_discovery/*`).
- Verify logging is coherent (UI console vs. `core/logger.py:1-20`) and that outputs land in the expected folders.
- Update README(s) (`README.md`, `완전통합자동화시스템_기술명세서_코딩버전.md`, `CLAUDE.md`) to mirror the new reality once decisions are implemented.

