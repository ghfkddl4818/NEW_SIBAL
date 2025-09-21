import asyncio
import threading
import typer
from typing import Annotated, List
from core.config import load_config, AppConfig

# Support both root-level pipeline.py and app/pipeline.py
try:
    from pipeline import run_pipeline  # root-style
except Exception:
    from app.pipeline import run_pipeline  # app-style


app = typer.Typer()


@app.command()
def run(
    job_id: Annotated[str, typer.Option(help="Unique ID for the job")] = "test_001",
    tone: Annotated[str, typer.Option(help="Override default tone")] = None,
    email_min_chars: Annotated[int, typer.Option(help="Override email min characters")] = None,
    email_max_chars: Annotated[int, typer.Option(help="Override email max characters")] = None,
    concurrency: Annotated[int, typer.Option(help="Override concurrency level")] = None,
    budget: Annotated[float, typer.Option(help="Override max cost per job (USD)")] = None,
    config_path: Annotated[str, typer.Option(help="config.yaml path")] = "config/config.yaml",
):
    cfg: AppConfig = load_config(config_path)

    if tone: cfg.policy.tone_default = tone
    if email_min_chars: cfg.policy.email_min_chars = email_min_chars
    if email_max_chars: cfg.policy.email_max_chars = email_max_chars
    if concurrency: cfg.runtime.concurrency = concurrency
    if budget: cfg.budget.max_cost_per_job_usd = budget

    typer.echo(f"Starting pipeline for job: {job_id}")

    async def _runner():
        await run_pipeline(job_id, cfg)

    try:
        asyncio.get_running_loop()
        loop_running = True
    except RuntimeError:
        loop_running = False

    if not loop_running:
        asyncio.run(_runner())
    else:
        errors: List[BaseException] = []

        def _run_in_thread():
            try:
                asyncio.run(_runner())
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        thread = threading.Thread(target=_run_in_thread, name=f"pipeline-{job_id}")
        thread.start()
        thread.join()

        if errors:
            raise errors[0]

    typer.echo(f"Pipeline finished for job: {job_id}")

@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Allow calling without explicit subcommand by invoking run."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


if __name__ == "__main__":
    app()
