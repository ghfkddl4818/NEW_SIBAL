"""
M3. 상세 리더 모듈
스토어 상세 페이지에서 정보 추출
"""
import pyautogui
import time
from typing import Optional
from .models import StoreCard
from .utils import logger, get_current_url, wait_for_load


class DetailReader:
    """상세 페이지 리더"""

    def __init__(self, config):
        self.config = config
        self.layout = self.config.get("layout", {})
        self.ocr_lang = self.config.get("ocr", {}).get("lang", "kor+eng")

    def _configure_tesseract(self):
        try:
            import pytesseract  # type: ignore
            import yaml  # type: ignore
            import os
        except ImportError:
            logger.warning('pytesseract가 없어 OCR 기능을 사용할 수 없습니다.')
            return None, None

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        tesseract_cmd = None

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                tesseract_cmd = config_data.get('ocr', {}).get('tesseract_cmd')
            except Exception as e:
                logger.warning(f"config.yaml 로드 실패: {e}")
                tesseract_cmd = None

        if not tesseract_cmd or '${' in str(tesseract_cmd):
            tesseract_cmd = os.getenv('TESSERACT_CMD')

        if not tesseract_cmd:
            logger.warning('tesseract_cmd가 설정되지 않아 OCR 기능을 비활성화합니다.')
            return None, None

        tesseract_cmd = os.path.expanduser(os.path.expandvars(str(tesseract_cmd)))
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        return pytesseract, self.ocr_lang

    def _extract_number_from_text(self, text: str) -> Optional[int]:
        import re
        patterns = [
            r'관심고객수?\s*([0-9,]+)',
            r'관심고객\s*([0-9,]+)',
            r'찜\s*([0-9,]+)',
            r'follower\s*([0-9,]+)',
            r'([0-9,]+)\s*관심',
            r'([0-9,]+)\s*찜',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(',', ''))

        numbers = re.findall(r'([0-9,]+)', text)
        for num_str in numbers:
            try:
                num = int(num_str.replace(',', ''))
            except ValueError:
                continue
            if 0 < num < 100000:
                return num
        return None

    def _read_interest_from_region(self, pytesseract, lang: str, x: int, y: int, width: int, height: int) -> Optional[int]:
        try:
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            text = pytesseract.image_to_string(screenshot, lang=lang)
            return self._extract_number_from_text(text)
        except Exception as exc:
            logger.debug(f"관심고객 영역 OCR 실패: {exc}")
            return None


    def open_card(self, card: StoreCard) -> bool:
        """카드 클릭하여 상세 페이지 열기"""
        try:
            # 카드 중앙 클릭
            center_x = card.x + card.width // 2
            center_y = card.y + card.height // 2

            logger.info(f"카드 클릭: {card.store_name} at ({center_x}, {center_y})")
            pyautogui.click(center_x, center_y)

            # 페이지 로딩 대기
            wait_min = self.config["timing"]["load_wait_min"]
            wait_max = self.config["timing"]["load_wait_max"]
            wait_for_load(wait_min, wait_max)

            return True

        except Exception as e:
            logger.error(f"카드 클릭 실패: {e}")
            return False

    def read_interest_count(self) -> Optional[int]:
        """관심고객수 읽기 (OCR 기반)"""
        try:
            pytesseract, lang = self._configure_tesseract()
            if pytesseract is None:
                logger.warning('Tesseract 설정을 찾지 못해 관심고객수를 건너뜁니다.')
                return None

            anchors = self.config.get("anchors", {})
            layout_cfg = self.layout if isinstance(self.layout, dict) else {}
            anchor_path = anchors.get("label_interest")
            confidence = float(layout_cfg.get("anchor_confidence", 0.75))
            region_cfg = layout_cfg.get("detail_interest_region", {})

            def _get_region_from_anchor(location):
                x_offset = int(region_cfg.get("x_offset", 120))
                y_offset = int(region_cfg.get("y_offset", -10))
                width = int(region_cfg.get("width", 220))
                height = int(region_cfg.get("height", 80))
                return (
                    location.left + x_offset,
                    location.top + y_offset,
                    width,
                    height,
                )

            if anchor_path:
                from pathlib import Path as _Path
                if _Path(anchor_path).exists():
                    try:
                        location = pyautogui.locateOnScreen(anchor_path, confidence=confidence)
                        if location:
                            region = _get_region_from_anchor(location)
                            count = self._read_interest_from_region(pytesseract, lang, *region)
                            if count is not None:
                                logger.debug(f"관심고객수(OCR-앵커): {count}")
                                return count
                    except Exception as e:
                        logger.debug(f"관심 앵커 감지 실패: {e}")

            fallback_cfg = layout_cfg.get("detail_interest_fallback_region", {})
            screen_width, screen_height = pyautogui.size()
            fallback_region = (
                int(fallback_cfg.get("x", screen_width // 4)),
                int(fallback_cfg.get("y", screen_height // 3)),
                int(fallback_cfg.get("width", screen_width // 2)),
                int(fallback_cfg.get("height", screen_height // 3)),
            )
            count = self._read_interest_from_region(pytesseract, lang, *fallback_region)
            if count is not None:
                logger.debug(f"관심고객수(OCR-폴백): {count}")
                return count

            logger.warning("관심고객수를 찾지 못했습니다.")
            return None

        except ImportError:
            logger.warning("pytesseract 없음. 관심고객수를 기본값으로 반환합니다.")
            return 100
        except Exception as e:
            logger.error(f"관심고객수 읽기 실패: {e}")
            return None

    def read_store_name_from_detail(self) -> Optional[str]:
        """상세 페이지에서 스토어명 읽기"""
        try:
            pytesseract, lang = self._configure_tesseract()
            if pytesseract is None:
                return None

            layout_cfg = self.layout if isinstance(self.layout, dict) else {}
            region_cfg = layout_cfg.get("detail_name_region", {})
            screen_width, screen_height = pyautogui.size()
            name_x = int(region_cfg.get("x", 200))
            name_y = int(region_cfg.get("y", 150))
            name_width = int(region_cfg.get("width", screen_width - 400))
            name_height = int(region_cfg.get("height", 100))

            screenshot = pyautogui.screenshot(region=(name_x, name_y, name_width, name_height))
            text = pytesseract.image_to_string(screenshot, lang=lang)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                return max(lines, key=len)
            return None

        except Exception as e:
            logger.error(f"상세 스토어명 읽기 실패: {e}")
            return None

    def get_current_url(self) -> Optional[str]:
        """현재 페이지 URL을 클립보드로부터 읽어오기"""
        try:
            url = get_current_url()
            if url:
                logger.debug(f"상세 URL 추출: {url}")
            else:
                logger.warning("상세 URL을 읽어오지 못했습니다")
            return url
        except Exception as e:
            logger.error(f"상세 URL 추출 실패: {e}")
            return None

    def back_to_list(self) -> bool:
        """목록으로 돌아가기"""
        try:
            logger.info("목록으로 돌아가기")
            # 브라우저 뒤로가기
            pyautogui.hotkey('alt', 'left')

            # 페이지 로딩 대기
            wait_min = self.config["timing"]["load_wait_min"]
            wait_max = self.config["timing"]["load_wait_max"]
            wait_for_load(wait_min, wait_max)

            return True

        except Exception as e:
            logger.error(f"목록 돌아가기 실패: {e}")
            return False
