"""
데이터 모델 정의
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import json


@dataclass
class StoreCard:
    """스토어 카드 정보"""
    x: int
    y: int
    width: int
    height: int
    store_name: Optional[str] = None
    review_count: Optional[int] = None


@dataclass
class StoreDetail:
    """스토어 상세 정보"""
    store_name: str
    store_url: str
    review_count: int
    interest_count: int
    collected_at: datetime
    note: str = ""

    def to_csv_row(self) -> List[str]:
        """CSV 행으로 변환"""
        return [
            self.collected_at.strftime("%Y-%m-%d %H:%M:%S"),
            self.store_name,
            self.store_url,
            str(self.review_count),
            str(self.interest_count),
            self.note
        ]

    def to_dict(self) -> Dict[str, Any]:
        """UI 표시용 요약 딕셔너리"""
        return {
            "store_name": self.store_name,
            "store_url": self.store_url,
            "review_count": self.review_count,
            "interest_count": self.interest_count,
            "collected_at": self.collected_at.strftime("%Y-%m-%d %H:%M:%S"),
            "note": self.note,
        }

    @classmethod
    def csv_headers(cls) -> List[str]:
        """CSV 헤더"""
        return [
            "collected_at",
            "store_name",
            "store_url",
            "review_count",
            "interest_count",
            "note"
        ]


@dataclass
class Checkpoint:
    """체크포인트 데이터"""
    last_scroll_position: int
    last_processed_url: str
    processed_urls: set
    visited_count: int
    saved_count: int

    def save(self, filepath: str):
        """체크포인트 저장"""
        data = {
            "last_scroll_position": self.last_scroll_position,
            "last_processed_url": self.last_processed_url,
            "processed_urls": list(self.processed_urls),
            "visited_count": self.visited_count,
            "saved_count": self.saved_count
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'Checkpoint':
        """체크포인트 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(
                last_scroll_position=data.get("last_scroll_position", 0),
                last_processed_url=data.get("last_processed_url", ""),
                processed_urls=set(data.get("processed_urls", [])),
                visited_count=data.get("visited_count", 0),
                saved_count=data.get("saved_count", 0)
            )
        except FileNotFoundError:
            return cls(0, "", set(), 0, 0)


@dataclass
class RunStats:
    """실행 통계"""
    total_visited: int = 0
    total_saved: int = 0
    skipped_review_range: int = 0
    skipped_interest_range: int = 0
    skipped_blocklist: int = 0
    skipped_multi_store: int = 0
    skipped_duplicate: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def summary(self) -> str:
        """요약 문자열"""
        duration = ""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            duration = f"소요시간: {delta.total_seconds():.1f}초"

        return f"""
=== 실행 완료 요약 ===
총 방문: {self.total_visited}
저장: {self.total_saved}
스킵:
  - 리뷰 범위 외: {self.skipped_review_range}
  - 관심고객 범위 외: {self.skipped_interest_range}
  - 차단 목록: {self.skipped_blocklist}
  - 다중 입점: {self.skipped_multi_store}
  - 중복: {self.skipped_duplicate}
오류: {self.errors}
{duration}
"""
