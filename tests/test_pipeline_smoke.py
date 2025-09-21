import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.main import app
from typer.testing import CliRunner

# To run this test, you might need to install pytest-asyncio
# pip install pytest-asyncio

@pytest.mark.asyncio
async def test_pipeline_smoke_run():
    runner = CliRunner()

    with patch('app.pipeline.process_images') as mock_ocr, \
         patch('app.pipeline.clean_ocr_output') as mock_clean, \
         patch('app.pipeline.normalize_reviews') as mock_reviews, \
         patch('llm.gemini_client.GeminiClient.generate') as mock_gemini, \
         patch('core.config.load_config') as mock_config, \
         patch('llm.gemini_client.vertexai.init') as mock_vertex_init:

        mock_cfg = MagicMock()
        mock_cfg.paths.output_root_dir = "outputs"
        mock_cfg.paths.input_images_dir = "data/product_images"
        mock_cfg.paths.input_reviews_dir = "data/reviews"
        mock_cfg.paths.prompts_dir = "llm/prompts"
        mock_cfg.budget.max_cost_per_job_usd = 0.05
        mock_cfg.runtime.rate_limit = {'rpm_soft': 60, 'tpm_soft': 120000}
        mock_cfg.runtime.backoff = [1, 2]
        mock_cfg.policy.ad_prefix = True
        mock_cfg.policy.suppress_risky_claims = True
        mock_cfg.policy.email_min_chars = 10
        mock_cfg.policy.email_max_chars = 1000
        mock_cfg.policy.tone_default = 'consultant'
        mock_cfg.vertex.project_id = "test-project"
        mock_cfg.vertex.location = "us-central1"
        mock_config.return_value = mock_cfg

        mock_vertex_init.return_value = None

        mock_gemini.side_effect = [
            {"product": "mocked_product"},
            {"email": {"subject": "Test", "body": "Test body"}}
        ]

        job_id = "smoke_test_001"
        output_dir = Path("outputs") / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "ocr_raw.jsonl").touch()
        (output_dir / "ocr_clean.jsonl").touch()
        (output_dir / "reviews_normalized.json").touch()
        Path("llm/prompts/").mkdir(parents=True, exist_ok=True)
        Path("llm/prompts/product_structuring.json").write_text("{}", encoding='utf-8')
        Path("llm/prompts/cold_email.json").write_text("{}", encoding='utf-8')

        result = runner.invoke(app, ["run", "--job-id", job_id])

        assert result.exit_code == 0
        assert f"Starting pipeline for job: {job_id}" in result.stdout

        assert (output_dir / "product_structured.json").exists()
        assert (output_dir / "email_draft.json").exists()
        assert (output_dir / "email_final.txt").exists()
        assert (output_dir / "email_final.json").exists()
        assert (output_dir / "pipeline_state.json").exists()
