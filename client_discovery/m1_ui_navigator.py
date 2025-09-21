"""
M1. UI 진입 & 정렬 모듈
네이버 쇼핑 검색/정렬 기능
"""
import time
import random
import pyautogui
import pyperclip
from typing import Optional, Tuple

from .utils import find_image_on_screen, wait_for_load, logger, is_browser_focused


class UINavigator:
    """UI 진입 및 정렬 제어"""

    def __init__(self, config):
        self.config = config
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    # === 공개 API ===

    def prepare_keyword_run(self, keyword: str) -> bool:
        """키워드별 검색 준비 (브라우저 활성화 → 쇼핑 홈 이동 → 검색/정렬)"""
        logger.info(f"[네비게이터] 키워드 준비: {keyword}")

        if not self.ensure_browser_focus():
            logger.warning("브라우저 창이 포커스 되어 있지 않습니다. 직접 활성화해 주세요.")
            return False

        if not self.open_shopping_home():
            return False

        if not self.open_search(keyword):
            return False

        if not self.go_tab_shoppingmall():
            logger.warning("쇼핑몰 탭을 찾지 못했습니다. 현재 탭 구성을 확인해 주세요.")
            return False

        if not self.set_sort_by_review_desc():
            logger.warning("리뷰 많은순 정렬을 설정하지 못했습니다. 수동으로 정렬 상태를 확인해 주세요.")

        self.set_items_per_page(80)
        self.scroll_to_top()
        return True

    def ensure_browser_focus(self) -> bool:
        """브라우저 창이 활성화되어 있는지 확인"""
        return is_browser_focused()

    def open_shopping_home(self) -> bool:
        """네이버 쇼핑 검색 홈으로 이동"""
        try:
            url = self.config.get("search", {}).get("shopping_url")
            if not url:
                return True

            logger.info(f"네이버 쇼핑 이동: {url}")
            pyautogui.hotkey('ctrl', 'l')
            wait_for_load(0.2, 0.4)
            self._type_with_clipboard(url)
            pyautogui.press('enter')

            wait_min, wait_max = self._get_load_wait()
            wait_for_load(wait_min, wait_max)
            return True

        except Exception as e:
            logger.error(f"쇼핑 홈 이동 실패: {e}")
            return False

    def open_search(self, keyword: str) -> bool:
        """검색창에 키워드를 입력하고 검색"""
        try:
            logger.info(f"검색 실행: {keyword}")
            search_box_coords = self._find_search_box()
            if not search_box_coords:
                logger.error("검색창을 찾지 못했습니다. 좌표나 앵커 설정을 확인해 주세요.")
                return False

            pyautogui.click(search_box_coords[0], search_box_coords[1])
            wait_for_load(0.3, 0.6)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            self._type_with_clipboard(keyword)
            pyautogui.press('enter')

            wait_min, wait_max = self._get_load_wait()
            wait_for_load(wait_min, wait_max)
            logger.info("검색 완료")
            return True

        except Exception as e:
            logger.error(f"검색 실패: {e}")
            return False

    def go_tab_shoppingmall(self) -> bool:
        """쇼핑몰 탭 클릭"""
        try:
            anchors = self.config.get("anchors", {})
            tab_image = anchors.get("tab_shoppingmall")
            tab_coords = find_image_on_screen(tab_image, confidence=0.8) if tab_image else None

            if not tab_coords:
                logger.error("쇼핑몰 탭 이미지를 찾지 못했습니다.")
                return False

            self._click_with_offset(tab_coords)
            wait_min, wait_max = self._get_load_wait()
            wait_for_load(wait_min, wait_max)
            logger.info("쇼핑몰 탭 활성화 완료")
            return True

        except Exception as e:
            logger.error(f"쇼핑몰 탭 이동 실패: {e}")
            return False

    def set_sort_by_review_desc(self) -> bool:
        """리뷰 많은순 정렬 버튼 클릭"""
        try:
            anchors = self.config.get("anchors", {})
            sort_image = anchors.get("sort_review_desc")
            sort_coords = find_image_on_screen(sort_image, confidence=0.8) if sort_image else None

            if not sort_coords:
                logger.error("리뷰 정렬 버튼 이미지를 찾지 못했습니다.")
                return False

            self._click_with_offset(sort_coords)
            wait_min, wait_max = self._get_load_wait()
            wait_for_load(wait_min, wait_max)
            logger.info("리뷰 많은순 정렬 설정 완료")
            return True

        except Exception as e:
            logger.error(f"정렬 설정 실패: {e}")
            return False

    def set_items_per_page(self, items: int = 80) -> bool:
        """페이지당 표시 개수를 설정 (기본 80개 보기)"""
        try:
            ui_config = self.config.get("ui", {})
            anchors = self.config.get("anchors", {})
            click_offset = self.config.get("timing", {}).get("click_offset_range", 5)

            button_point = self._get_point(ui_config.get("items_per_page_button"))
            if not button_point:
                button_image = anchors.get("items_per_page_button")
                if button_image:
                    button_point = find_image_on_screen(button_image, confidence=0.8)

            if not button_point:
                logger.debug("페이지당 개수 버튼이 설정되지 않아 건너뜁니다.")
                return False

            self._click_with_offset(button_point, offset=click_offset)
            wait_for_load(0.2, 0.5)

            option_key = f"items_per_page_option_{items}"
            option_point = self._get_point(ui_config.get(option_key))
            if not option_point:
                option_image = anchors.get(f"view_{items}") or anchors.get(option_key)
                if option_image:
                    option_point = find_image_on_screen(option_image, confidence=0.8)

            if option_point:
                self._click_with_offset(option_point, offset=click_offset)
                wait_for_load(0.3, 0.6)
                logger.info(f"페이지당 {items}개 보기 설정")
                return True

            logger.warning("페이지당 보기 옵션을 찾지 못했습니다. 수동 확인이 필요합니다.")
            return False

        except Exception as e:
            logger.error(f"페이지당 개수 설정 실패: {e}")
            return False

    def scroll_down_once(self) -> bool:
        """결과 페이지를 한 번 스크롤"""
        try:
            logger.info("스크롤 다운")
            scroll_amount = random.randint(300, 500)
            pyautogui.scroll(-scroll_amount)
            wait_min = self.config.get("timing", {}).get("scroll_wait_min", 0.5)
            wait_max = self.config.get("timing", {}).get("scroll_wait_max", 1.0)
            wait_for_load(wait_min, wait_max)
            return True

        except Exception as e:
            logger.error(f"스크롤 실패: {e}")
            return False

    def scroll_to_top(self):
        """검색 결과 페이지 최상단으로 이동"""
        try:
            pyautogui.press('home')
            wait_for_load(0.2, 0.5)
        except Exception as e:
            logger.debug(f"스크롤 최상단 이동 실패(무시): {e}")

    # === 내부 유틸 ===

    def _find_search_box(self) -> Optional[Tuple[int, int]]:
        anchors = self.config.get("anchors", {})
        search_image = anchors.get("search_box")
        if search_image:
            coords = find_image_on_screen(search_image, confidence=0.85)
            if coords:
                return coords

        ui_config = self.config.get("ui", {})
        search_box = self._get_point(ui_config.get("search_box"))
        if search_box:
            return search_box

        # 기본 좌표 (1920x1080 기준): 필요 시 config에서 덮어쓰기
        return (500, 100)

    def _click_with_offset(self, coords: Tuple[int, int], offset: int = None):
        if offset is None:
            offset = self.config.get("timing", {}).get("click_offset_range", 5)
        x = coords[0] + random.randint(-offset, offset)
        y = coords[1] + random.randint(-offset, offset)
        pyautogui.click(x, y)

    def _type_with_clipboard(self, text: str):
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)

    def _get_point(self, value) -> Optional[Tuple[int, int]]:
        if isinstance(value, dict) and "x" in value and "y" in value:
            return int(value["x"]), int(value["y"])
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return int(value[0]), int(value[1])
        return None

    def _get_load_wait(self) -> Tuple[float, float]:
        timing = self.config.get("timing", {})
        return timing.get("load_wait_min", 1.0), timing.get("load_wait_max", 2.0)
