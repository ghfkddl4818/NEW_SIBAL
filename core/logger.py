import sys
from loguru import logger
from pathlib import Path

def setup_logger(job_id: str, output_dir: str):
    logger.remove()
    log_path = Path(output_dir) / job_id / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}.{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(
        log_path,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}.{function}:{line} - {message}",
        rotation="10 MB",
        retention="10 days",
        encoding="utf-8",
    )
    return logger
