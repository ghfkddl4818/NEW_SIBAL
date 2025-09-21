"""
M5. 저장 & 체크포인트 모듈
CSV 저장 및 체크포인트 관리
"""
import csv
from pathlib import Path
from datetime import datetime
from typing import List
from .models import StoreDetail, Checkpoint
from .utils import logger


class StorageManager:
    """저장 및 체크포인트 관리"""

    def __init__(self, config):
        self.config = config
        self.output_dir = Path("client_discovery")
        self.output_dir.mkdir(exist_ok=True)

    def get_csv_filepath(self) -> Path:
        """CSV 파일 경로 생성"""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = self.config["output"]["csv_file"].format(date=date_str)
        return self.output_dir / filename

    def append_csv(self, store_detail: StoreDetail) -> bool:
        """CSV에 스토어 정보 추가"""
        try:
            csv_file = self.get_csv_filepath()

            # 파일이 없으면 헤더 추가
            write_header = not csv_file.exists()

            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                if write_header:
                    writer.writerow(StoreDetail.csv_headers())

                writer.writerow(store_detail.to_csv_row())

            logger.info(f"저장 완료: {store_detail.store_name}")
            return True

        except Exception as e:
            logger.error(f"CSV 저장 실패: {e}")
            return False

    def save_checkpoint(self, checkpoint: Checkpoint) -> bool:
        """체크포인트 저장"""
        try:
            checkpoint_file = self.output_dir / "checkpoint.json"
            checkpoint.save(str(checkpoint_file))
            logger.debug("체크포인트 저장 완료")
            return True

        except Exception as e:
            logger.error(f"체크포인트 저장 실패: {e}")
            return False

    def load_checkpoint(self) -> Checkpoint:
        """체크포인트 로드"""
        try:
            checkpoint_file = self.output_dir / "checkpoint.json"
            checkpoint = Checkpoint.load(str(checkpoint_file))
            logger.info(f"체크포인트 로드: 방문 {checkpoint.visited_count}, 저장 {checkpoint.saved_count}")
            return checkpoint

        except Exception as e:
            logger.error(f"체크포인트 로드 실패: {e}")
            return Checkpoint(0, "", set(), 0, 0)

    def save_run_log(self, stats, end_reason: str = "정상 완료") -> bool:
        """실행 로그 저장"""
        try:
            log_file = self.output_dir / self.config["output"]["log_file"]

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== 실행 로그 {datetime.now()} ===\n")
                f.write(stats.summary())
                f.write(f"종료 사유: {end_reason}\n")
                f.write("=" * 50 + "\n")

            logger.info(f"실행 로그 저장: {log_file}")
            return True

        except Exception as e:
            logger.error(f"실행 로그 저장 실패: {e}")
            return False

    def save_error_screenshot(self, reason: str) -> str:
        """오류 스크린샷 저장"""
        try:
            from .utils import save_screenshot

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_{timestamp}_{reason}.png"

            save_screenshot(filename)
            logger.warning(f"오류 스크린샷 저장: {filename}")
            return filename

        except Exception as e:
            logger.error(f"오류 스크린샷 저장 실패: {e}")
            return ""

    def save_sample_screenshot(self, index: int) -> bool:
        """샘플 스크린샷 저장 (1/20 간격)"""
        try:
            if index % 20 != 0:  # 20번에 1번만 저장
                return True

            from .utils import save_screenshot

            filename = f"sample_card_{index:03d}.png"
            save_screenshot(filename)
            return True

        except Exception as e:
            logger.error(f"샘플 스크린샷 저장 실패: {e}")
            return False

    def get_existing_store_count(self) -> int:
        """기존 저장된 스토어 수 반환"""
        try:
            csv_file = self.get_csv_filepath()
            if not csv_file.exists():
                return 0

            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = sum(1 for _ in reader)
                # 헤더 제외(0보다 작아지지 않도록 보호)
                return max(rows - 1, 0)

        except Exception as e:
            logger.error(f"기존 스토어 수 계산 실패: {e}")
            return 0
