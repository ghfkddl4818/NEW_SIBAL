# Instruction Brief for Claude (Full Pass)

Claude, please fix the current automation by following the checklist below. The current `ultimate_automation_system.py` UI reports success while doing nothing; the goal is to restore real automation without losing the existing absolute-coordinate fallbacks.

## 0. General Expectations
- Keep the current Tkinter GUI; do not rip out tabs or redesign UX.
- Preserve the existing absolute-coordinate clicks. Where we rely on coordinates (e.g., tiny or ambiguous targets), keep them but centralize the numbers in one place (constants or config) so they can be adjusted easily.
- When an older working implementation exists in `_archive/` or `all_in_one_sibal/`, use it as a reference for missing logic, but adapt it to the current class names and settings instead of copy/pasting wholesale.
- All paths that users may need to tweak (downloads, work/output folders, database path, tesseract path, coordinate overrides) should surface via config or GUI fields rather than hard-coded `E:/...` strings.

## 1. Web Automation Loop
- In `execute_web_automation`, replace the bogus `self.web_progress_bar.set(...)` calls with assignments to `self.web_progress_bar['value']` and update `self.processed_count` (increment on success) so the UI reflects real progress.
- Honor `self.automation_paused` inside the loop. Insert checks that sleep or wait until the flag clears, and allow `emergency_stop` to break out immediately.
- After closing a tab with `ctrl+w`, actually open or navigate to the next product (reuse logic from older versions if necessary). Right now the loop never loads a new page, so only the first item is touched.
- Add retry/error handling so one failure moves on to the next product without stopping the run.

## 2. Image Templates & Absolute Coordinates
- Fix `crawling_sequence` to pass `self.image_files['review_button']`, `self.image_files['analysis_start']`, etc., instead of bare filenames. Audit every `wait_for_button_with_timeout` call to ensure it receives an actual path.
- Confirm all entries in `self.image_files` exist. Add the missing templates (`tab_shoppingmall.png`, `sort_review_desc.png`, `label_review.png`, `label_interest.png`, etc.) to `assets/img/`. Use the guidance in `assets/img/README.md` and capture from the environment where the automation runs.
- For the handful of places where template matching fails and we deliberately use absolute coordinates, isolate the values in a helper (e.g., `self.coords['close_popup'] = (x, y)`). Load overrides from config if possible so future adjustments do not require code edits.

## 3. File FIFO & Database Wiring
- Call `create_database_if_missing` during startup.
- When a product capture succeeds, push it through the FIFO helpers (`add_pending_store`, `get_next_pending_store`, `clean_old_pending_stores`) and check `is_duplicate_file` before copying or processing files.
- Invoke `add_to_database` when a new product is recorded, and `update_database_entry` after the corresponding email is generated.
- Move download/work/database/output paths to come from `config/config.yaml` (with GUI overrides). Remove the hard-coded `E:/업무...` defaults.

## 4. AI Stage Uses Real Data
- Replace the placeholder `user_payload` in `execute_ai_generation`. Load OCR results and review summaries from `data/product_images` / `data/reviews` (or invoke the pipeline modules in `app/`). Combine them into the payload that gets sent to `GeminiClient.generate`.
- Allow the "AI only" button to run without `self.automation_running`; check `self.automation_running` only when you truly need the full pipeline.
- After generating each email, append metadata to `self.generated_emails` and update the UI counts.

## 5. Client Discovery (Naver Shopping Crawler)
- Replace the stub in `client_discovery/m2_list_scanner.py` that returns the three fake `테스트스토어_*` cards. Implement real scanning: capture card regions, run OCR (respecting `config.ocr.tesseract_cmd`), and return actual data.
- Ensure the anchor images referenced in `client_discovery/config.json` exist and load. If a button is too small, fall back to a coordinate stored in the config.
- Write successful finds to CSV through `StorageManager.append_csv` and persist checkpoints. The result should no longer rely on synthetic data.

## 6. Safety Monitoring & Shutdown
- Add a flag (e.g., `self._stop_monitoring = True`) that is set inside `emergency_stop_all` and when the GUI closes. Modify the background safety thread loop to respect this flag so it exits cleanly.
- Make sure `emergency_stop`/`emergency_stop_all` not only log messages but also break active loops (`while` loops in web automation, AI generation, client discovery).

## 7. Configuration & Dependencies
- Load GUI defaults (folders, product counts, confidence thresholds) from `config/config.yaml` during initialization, and write back if the user changes them in the GUI.
- Update `requirements.txt` to cover every runtime import: add `vertexai`, `numpy`, `pygetwindow`, and anything else currently missing.
- Ensure all modules refer to the Tesseract path specified in `config/config.yaml`. Remove hard-coded `E:\tesseract\tesseract.exe` literals in helper files.

## 8. API & OCR Checks
- Verify `VERTEX_PROJECT_ID` is read from env/config and that `GeminiClient` receives valid credentials (ADC). Keep the API safety wrapper (`core/safety_monitor.py`) active so spending limits still apply.
- Confirm OCR modules call `pytesseract.pytesseract.tesseract_cmd = config.ocr.tesseract_cmd` before each use. Expose a GUI field if operators need to tweak the path quickly.

## 9. Regression Checklist
After implementing everything above, run these validations and capture screenshots/logs:
1. Complete 30-product web automation with real browser interaction (buttons clicked, files saved, progress increments).
2. Check that new images/reviews land in `data/`, the Excel DB updates, and `outputs/` has meaningful email JSON files referencing the captured content.
3. Run the client discovery crawler; confirm the CSV contains real store rows gathered from the screen.
4. Trigger pause/resume and emergency stop to ensure loops respond immediately and the safety thread shuts down.
5. Provide a short summary of any coordinates/templates that still require manual adjustment so the operator knows where to tweak them.

Thank you.
