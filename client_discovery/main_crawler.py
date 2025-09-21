"""
메인 크롤러
네이버 쇼핑 고객사 발굴 자동화 실행
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .models import StoreDetail, RunStats
from .m1_ui_navigator import UINavigator
from .m2_list_scanner import ListScanner
from .m3_detail_reader import DetailReader
from .m4_filter import FilterManager
from .m5_storage import StorageManager
from .m6_monitor import SafetyMonitor
from .utils import logger


class NaverShoppingCrawler:
    """네이버 쇼핑 크롤러 메인 클래스"""

    def __init__(self, config_path: str = "client_discovery/config.json"):
        # 설정 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config: Dict[str, Any] = json.load(f)

        # 모듈 초기화
        self.storage = StorageManager(self.config)
        self.monitor = SafetyMonitor(self.config, self.storage)
        self.navigator = UINavigator(self.config)
        self.scanner = ListScanner(self.config)
        self.reader = DetailReader(self.config)
        self.filter = FilterManager(self.config)

        # 상태 변수
        self.stats = RunStats()
        self.checkpoint = self.storage.load_checkpoint()
        self.saved_details: List[StoreDetail] = []
        self.current_keyword: str = ""

        logger.info("네이버 쇼핑 크롤러 초기화 완료")

    def run(self) -> Dict[str, Any]:
        """메인 실행 함수"""
        self.saved_details = []
        result: Dict[str, Any] = {"status": "unknown", "message": ""}

        try:
            self.stats.start_time = datetime.now()
            logger.info("크롤링 시작")

            # 1. 초기 설정
            if not self._init_environment():
                notice = self.monitor.abort_with_notice("환경 초기화 실패")
                result = {"status": "aborted", "message": notice}
            # 2. 수동 준비 확인 (검색/정렬은 사용자가 미리 완료)
            elif not self._check_manual_setup():
                notice = self.monitor.abort_with_notice("수동 준비 미완료")
                result = {"status": "aborted", "message": notice}
            else:
                # 3. 메인 크롤링 루프
                crawl_result = self._main_crawling_loop()

                if isinstance(crawl_result, dict):
                    result = crawl_result
                else:
                    result = {
                        "status": "success",
                        "message": crawl_result,
                        "visited_count": self.stats.total_visited,
                        "saved_count": self.checkpoint.saved_count,
                        "csv_path": str(self.storage.get_csv_filepath()),
                        "details": [detail.to_dict() for detail in self.saved_details],
                    }

        except Exception as e:
            logger.error(f"크롤링 중 예외 발생: {e}")
            notice = self.monitor.abort_with_notice(f"예외 발생: {e}")
            result = {
                "status": "error",
                "message": notice,
                "exception": str(e),
            }

        finally:
            self.stats.end_time = datetime.now()
            reason = result.get("message", "실행 완료")
            self.monitor.graceful_exit(self.checkpoint, self.stats, reason)

        return result

    def start_crawling(self) -> Dict[str, Any]:
        """구 버전 호환용 진입점"""
        return self.run()

    def apply_config_updates(self, updates: Dict[str, Dict[str, Any]]):
        """외부에서 전달된 설정값을 런타임에 반영"""
        for section, values in (updates or {}).items():
            if not isinstance(values, dict):
                continue
            current = self.config.get(section)
            if isinstance(current, dict):
                current.update(values)
            else:
                self.config[section] = values

        if updates:
            logger.info(f"설정 업데이트 적용: {updates}")

        # 하위 모듈들도 동일 설정 참조
        self.storage.config = self.config
        self.monitor.config = self.config
        self.navigator.config = self.config
        self.scanner.config = self.config
        self.reader.config = self.config
        self.filter.config = self.config

    def _resolve_keywords(self) -> List[str]:
        """설정에서 키워드 목록을 정리"""
        search_cfg = self.config.get("search", {})
        keywords = [kw.strip() for kw in search_cfg.get("keywords", []) if isinstance(kw, str) and kw.strip()]

        single_keyword = search_cfg.get("keyword", "")
        if single_keyword and isinstance(single_keyword, str):
            single_keyword = single_keyword.strip()
            if single_keyword and single_keyword not in keywords:
                keywords.append(single_keyword)

        return keywords

    def _init_environment(self) -> bool:
        """환경 초기화"""
        try:
            logger.info("환경 초기화 시작...")

            # 필요한 디렉토리 생성
            logger.info("디렉토리 생성 중...")
            from pathlib import Path
            Path("client_discovery").mkdir(exist_ok=True)
            Path("client_discovery/screens").mkdir(exist_ok=True)
            logger.info("디렉토리 생성 완료")

            # 기존 데이터 확인
            logger.info("기존 데이터 확인 중...")
            existing_count = self.storage.get_existing_store_count()
            logger.info(f"기존 저장된 스토어: {existing_count}개")

            logger.info("환경 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"환경 초기화 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _check_manual_setup(self) -> bool:
        """브라우저 포커스 상태만 확인"""
        try:
            if not self.navigator.ensure_browser_focus():
                logger.warning("브라우저 창이 포커스되어 있지 않습니다. 창을 활성화한 뒤 다시 실행해 주세요.")
            return True
        except Exception as e:
            logger.error(f"준비 상태 확인 중 오류: {e}")
            return True

    def _main_crawling_loop(self) -> str:
        """메인 크롤링 루프"""
        keywords = self._resolve_keywords()
        if not keywords:
            message = "검색 키워드를 설정해 주세요."
            logger.error(message)
            self.current_keyword = ""
            return {"status": "aborted", "message": message}

        search_cfg = self.config.get("search", {})
        max_overall = int(search_cfg.get("max_visits_per_run", 0) or 0)
        max_per_keyword = int(search_cfg.get("max_results_per_keyword", 0) or 0)

        logger.info(f"크롤링 시작: 키워드 {len(keywords)}개")

        total_visited = self.checkpoint.visited_count

        for index, keyword in enumerate(keywords, 1):
            if max_overall and total_visited >= max_overall:
                logger.info("전체 방문 한도에 도달했으므로 중단합니다.")
                break

            logger.info(f"=== 키워드 {index}/{len(keywords)}: {keyword} ===")
            self.current_keyword = keyword

            if not self.navigator.prepare_keyword_run(keyword):
                logger.error(f"키워드 준비 실패: {keyword}")
                continue

            visited_for_keyword = 0
            keyword_stop = False

            while True:
                if max_per_keyword and visited_for_keyword >= max_per_keyword:
                    logger.info(f"키워드 방문 한도 도달 ({keyword})")
                    break

                if max_overall and total_visited >= max_overall:
                    logger.info("전체 방문 한도에 도달했습니다.")
                    keyword_stop = True
                    break

                can_continue, reason = self.monitor.should_continue()
                if not can_continue:
                    notice = self.monitor.abort_with_notice(reason)
                    self.current_keyword = ""
                    return {"status": "aborted", "message": notice}

                cards = self.scanner.scan_visible_cards()
                if not cards:
                    if not self.navigator.scroll_down_once():
                        logger.info("더 이상 스크롤할 카드가 없어 다음 키워드로 이동합니다.")
                        break
                    continue

                for card in cards:
                    if max_per_keyword and visited_for_keyword >= max_per_keyword:
                        break
                    if max_overall and total_visited >= max_overall:
                        keyword_stop = True
                        break

                    self.storage.save_sample_screenshot(total_visited)

                    if not self._process_card(card):
                        continue

                    visited_for_keyword += 1
                    total_visited += 1
                    self.checkpoint.visited_count = total_visited

                    if total_visited % 10 == 0:
                        self.storage.save_checkpoint(self.checkpoint)

                if keyword_stop:
                    break

            self.navigator.scroll_to_top()

        self.current_keyword = ""
        self.stats.total_visited = total_visited
        self.stats.total_saved = self.checkpoint.saved_count
        self.storage.save_checkpoint(self.checkpoint)

        return {
            "status": "success",
            "message": "크롤링 정상 종료",
            "visited_count": total_visited,
            "saved_count": self.checkpoint.saved_count,
            "csv_path": str(self.storage.get_csv_filepath()),
            "details": [detail.to_dict() for detail in self.saved_details],
        }

    def _process_card(self, card) -> bool:
        """개별 카드 처리"""
        try:
            # 1단계: 리스트에서 기본 정보 추출
            store_name_list = card.store_name
            review_count = card.review_count

            # 리뷰 수 필터링
            if not self.filter.passes_review_range(review_count):
                self.stats.skipped_review_range += 1
                logger.debug(f"리뷰 범위 외 스킵: {review_count}")
                return False

            # 차단 목록 체크
            if self.filter.is_blocklisted(store_name_list):
                self.stats.skipped_blocklist += 1
                logger.debug(f"차단 목록 스킵: {store_name_list}")
                return False

            if self.filter.is_multi_store(store_name_list):
                self.stats.skipped_multi_store += 1
                logger.debug(f"다중 입점 스킵: {store_name_list}")
                return False

            # 2단계: 상세 페이지 열기
            if not self.reader.open_card(card):
                self.stats.errors += 1
                return False

            # 의심 화면 체크
            if self.monitor.is_suspicious_screen():
                self.monitor.abort_with_notice("상세 페이지에서 의심 화면 감지")
                return False

            # 3단계: 상세 정보 추출
            url = self.reader.get_current_url()
            store_name_detail = self.reader.read_store_name_from_detail() or store_name_list

            # 중복 체크
            if self.filter.is_duplicate(url, store_name_detail):
                self.stats.skipped_duplicate += 1
                logger.debug(f"중복 스킵: {store_name_detail}")
                self.reader.back_to_list()
                return False

            # 관심고객 수 추출
            interest_count = self.reader.read_interest_count()

            # 관심고객 수 필터링
            if not self.filter.passes_interest_range(interest_count):
                self.stats.skipped_interest_range += 1
                logger.debug(f"관심고객 범위 외 스킵: {interest_count}")
                self.reader.back_to_list()
                return False

            # 4단계: 저장
            store_detail = StoreDetail(
                store_name=store_name_detail,
                store_url=url or "",
                review_count=review_count,
                interest_count=interest_count,
                collected_at=datetime.now(),
                note=self.current_keyword or ""
            )

            if self.storage.append_csv(store_detail):
                self.filter.add_to_processed(url, store_name_detail)
                self.checkpoint.saved_count += 1
                self.checkpoint.processed_urls.add(url or "")
                self.saved_details.append(store_detail)
                logger.info(f"저장 완료: {store_name_detail} (리뷰: {review_count}, 관심: {interest_count})")

            # 목록으로 돌아가기
            self.reader.back_to_list()
            return True

        except Exception as e:
            logger.error(f"카드 처리 실패: {e}")
            self.stats.errors += 1
            # 목록으로 돌아가기 시도
            try:
                self.reader.back_to_list()
            except:
                pass
            return False


def run_crawler():
    """크롤러 실행 함수"""
    try:
        crawler = NaverShoppingCrawler()
        result = crawler.run()
        print(f"크롤링 완료: {result}")
        return result
    except Exception as e:
        logger.error(f"크롤러 실행 실패: {e}")
        return f"실행 실패: {e}"


if __name__ == "__main__":
    run_crawler()
