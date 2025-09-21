import json
from pathlib import Path
import asyncio
import pandas as pd  # ★ 추가: 실패로그에서 pd.Timestamp 사용

from core.config import AppConfig
from core.logger import setup_logger
from ocr.engine import process_images
from ocr.postproc import clean_ocr_output
from reviews.normalize import normalize_reviews
from llm.gemini_client import GeminiClient, BudgetGuard, RateLimiter
from compose.composer import compose_final_email

async def run_pipeline(job_id: str, cfg: AppConfig):
    output_dir = Path(cfg.paths.output_root_dir) / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(job_id, cfg.paths.output_root_dir)

    # Setup clients
    budget_guard = BudgetGuard(cfg.budget.max_cost_per_job_usd)
    rate_limiter = RateLimiter(cfg.runtime.rate_limit['rpm_soft'], cfg.runtime.rate_limit['tpm_soft'])
    gemini_client = GeminiClient(cfg)

    # --- Pipeline Stages ---
    pipeline_state = {"job_id": job_id, "status": "STARTED"}

    try:
        # 1. Discover (Implicitly done by other steps)
        logger.info("Pipeline started.")

        # 2. OCR
        ocr_raw_path = output_dir / "ocr_raw.jsonl"
        process_images(cfg.paths.input_images_dir, str(ocr_raw_path), cfg, logger)
        pipeline_state['ocr_raw_path'] = str(ocr_raw_path)

        # 3. OCR Cleanup
        ocr_clean_path = output_dir / "ocr_clean.jsonl"
        clean_ocr_output(str(ocr_raw_path), str(ocr_clean_path), logger)
        pipeline_state['ocr_clean_path'] = str(ocr_clean_path)

        # 4. LLM Call #1: Structuring
        with open(ocr_clean_path, 'r', encoding='utf-8') as f:
            ocr_text = " ".join([json.loads(line)['cleaned_text'] for line in f])

        with open(Path(cfg.paths.prompts_dir) / 'product_structuring.json', 'r', encoding='utf-8') as f:
            structuring_prompt = json.load(f)

        structured_product = await gemini_client.generate(structuring_prompt, ocr_text)
        structured_product_path = output_dir / "product_structured.json"
        with open(structured_product_path, 'w', encoding='utf-8') as f:
            json.dump(structured_product, f, ensure_ascii=False, indent=2)
        pipeline_state['structured_product_path'] = str(structured_product_path)
        logger.info("Product structuring complete.")

        # 5. Normalize Reviews
        reviews_normalized_path = output_dir / "reviews_normalized.json"
        reviews_payload = normalize_reviews(cfg.paths.input_reviews_dir, str(reviews_normalized_path), logger)
        pipeline_state['reviews_normalized_path'] = str(reviews_normalized_path)

        if reviews_payload is None:
            with open(reviews_normalized_path, 'r', encoding='utf-8') as f:
                review_data = json.load(f)
        else:
            try:
                json.dumps(reviews_payload)
                review_data = reviews_payload
            except TypeError:
                logger.warning("normalize_reviews returned non-serializable data — using empty dict")
                review_data = {}
            try:
                with open(reviews_normalized_path, 'w', encoding='utf-8') as f:
                    json.dump(review_data, f, ensure_ascii=False, indent=2)
            except TypeError:
                # review_data가 직렬화 불가능한 경우를 대비한 최소한의 보호
                with open(reviews_normalized_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps({}, ensure_ascii=False))

        # 6. LLM Call #2: Cold Email
        with open(Path(cfg.paths.prompts_dir) / 'cold_email.json', 'r', encoding='utf-8') as f:
            cold_email_prompt = json.load(f)
        cold_email_prompt.setdefault("constraints", {})["tone_default"] = cfg.policy.tone_default

        combined_input = f"Product Info:\n{json.dumps(structured_product)}\n\nReview Info:\n{json.dumps(review_data)}"
        email_draft = await gemini_client.generate(cold_email_prompt, combined_input)
        email_draft_path = output_dir / "email_draft.json"
        with open(email_draft_path, 'w', encoding='utf-8') as f:
            json.dump(email_draft, f, ensure_ascii=False, indent=2)
        pipeline_state['email_draft_path'] = str(email_draft_path)
        logger.info("Cold email draft complete.")

        # 7. Final Composition
        final_email = compose_final_email(email_draft, cfg.policy)
        email_final_txt_path = output_dir / "email_final.txt"
        email_final_json_path = output_dir / "email_final.json"
        with open(email_final_txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {final_email['subject']}\n\n{final_email['body']}")
        with open(email_final_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_email, f, ensure_ascii=False, indent=2)
        pipeline_state['final_email_paths'] = [str(email_final_txt_path), str(email_final_json_path)]
        logger.info("Final email composed.")

        pipeline_state["status"] = "SUCCESS"

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        pipeline_state["status"] = "FAILED"
        pipeline_state["error"] = str(e)
        # Failure logging
        failure_path = Path(cfg.paths.output_root_dir) / "failures.csv"
        with open(failure_path, 'a', encoding='utf-8') as f:
            # timestamp, job_id, stage, reason, retries, est_cost_usd, tokens_in, tokens_out
            f.write(f"{pd.Timestamp.now()},{job_id},UNKNOWN,{str(e)},0,0,0,0\n")  # Simplified

    finally:
        state_path = output_dir / "pipeline_state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(pipeline_state, f, ensure_ascii=False, indent=2)
        logger.info("Pipeline finished.")
