"""
M4. 필터 & 디둡 모듈
리뷰/관심고객 범위 필터링 및 중복 제거
"""
import csv
import re
from pathlib import Path
from typing import Set, Optional
from .utils import logger


class FilterManager:
    """필터링 및 중복 제거 관리"""

    def __init__(self, config):
        self.config = config
        self.processed_urls: Set[str] = set()
        self.processed_names: Set[str] = set()
        filters_cfg = self.config.get("filters", {}) if isinstance(self.config, dict) else {}
        self.multi_store_keywords = [kw.lower() for kw in filters_cfg.get("multi_store_keywords", ["가격비교", "외"]) if isinstance(kw, str)]
        self.multi_store_separators = ['/', '|', '·', 'ㆍ', '+', ',']
        self._load_existing_data()

    def _load_existing_data(self):
        """기존 CSV에서 중복 체크용 데이터 로드"""
        try:
            output_file = self._get_output_file()
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'store_url' in row and row['store_url']:
                            self.processed_urls.add(row['store_url'])
                        if 'store_name' in row and row['store_name']:
                            self.processed_names.add(row['store_name'])

                logger.info(f"기존 데이터 로드: URL {len(self.processed_urls)}개, 이름 {len(self.processed_names)}개")

        except Exception as e:
            logger.error(f"기존 데이터 로드 실패: {e}")

    def _get_output_file(self) -> Path:
        """출력 파일 경로 생성"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        filename = self.config["output"]["csv_file"].format(date=date_str)
        return Path("client_discovery") / filename

    def passes_review_range(self, review_count: Optional[int]) -> bool:
        """리뷰 수 범위 체크"""
        if review_count is None:
            return False

        min_reviews = self.config["search"]["review_min"]
        max_reviews = self.config["search"]["review_max"]

        return min_reviews <= review_count <= max_reviews

    def passes_interest_range(self, interest_count: Optional[int]) -> bool:
        """관심고객 수 범위 체크"""
        if interest_count is None:
            return False

        min_followers = self.config["search"]["follower_min"]
        max_followers = self.config["search"]["follower_max"]

        return min_followers <= interest_count <= max_followers

    def is_blocklisted(self, store_name: Optional[str]) -> bool:
        """차단 목록 체크"""
        if not store_name:
            return False

        store_name_lower = store_name.lower()
        blocklist = self.config["blocklist"]

        for blocked_keyword in blocklist:
            if blocked_keyword.lower() in store_name_lower:
                logger.debug(f"차단됨: {store_name} (키워드: {blocked_keyword})")
                return True

        return False

    def is_multi_store(self, store_name: Optional[str]) -> bool:
        """여러 판매처가 묶인 스토어인지 판단"""
        if not store_name:
            return False

        name = store_name.strip()
        if not name:
            return False

        lowered = name.lower()

        if any(sep in name for sep in self.multi_store_separators):
            return True

        if re.search(r'\uc678\s*\d', name):
            return True

        for keyword in self.multi_store_keywords:
            if keyword and keyword in lowered:
                return True

        return False

    def is_duplicate(self, store_url: Optional[str] = None, store_name: Optional[str] = None) -> bool:
        """중복 체크"""
        # URL 중복 체크 (우선순위)
        if store_url and store_url in self.processed_urls:
            logger.debug(f"URL 중복: {store_url}")
            return True

        # 이름 중복 체크 (보조)
        if store_name and store_name in self.processed_names:
            logger.debug(f"이름 중복: {store_name}")
            return True

        return False

    def add_to_processed(self, store_url: Optional[str] = None, store_name: Optional[str] = None):
        """처리된 항목으로 추가"""
        if store_url:
            self.processed_urls.add(store_url)
        if store_name:
            self.processed_names.add(store_name)

    def get_filter_reason(self, review_count: Optional[int], interest_count: Optional[int],
                         store_name: Optional[str], store_url: Optional[str]) -> Optional[str]:
        """필터링 사유 반환 (디버깅용)"""
        if not self.passes_review_range(review_count):
            return f"리뷰 범위 외 ({review_count})"

        if self.is_blocklisted(store_name):
            return f"차단 목록 ({store_name})"
        if self.is_multi_store(store_name):
            return f"?? ?? ({store_name})"

        if not self.passes_interest_range(interest_count):
            return f"관심고객 범위 외 ({interest_count})"

        if self.is_duplicate(store_url, store_name):
            return "중복"

        return None  # 통과
