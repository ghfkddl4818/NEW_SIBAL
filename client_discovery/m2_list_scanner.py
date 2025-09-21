"""
M2. 리스트 스캐너 모듈
현재 화면의 스토어 카드들을 스캔하고 정보 추출
"""
import pyautogui
from pathlib import Path
from typing import List, Optional
from .models import StoreCard
from .utils import logger, find_image_on_screen, capture_screen_region


class ListScanner:
    """리스트 스캐너"""

    def __init__(self, config):
        self.config = config
        self.layout = self.config.get("layout", {})
        self.ocr_lang = self.config.get("ocr", {}).get("lang", "kor+eng")

    def _get_relative_region(self, key: str, fallback: tuple) -> tuple:
        region = self.layout.get(key, {}) if isinstance(self.layout, dict) else {}
        x = int(region.get('x', fallback[0]))
        y = int(region.get('y', fallback[1]))
        width = int(region.get('width', fallback[2]))
        height = int(region.get('height', fallback[3]))
        return x, y, width, height

    def _configure_tesseract(self):
        try:
            import pytesseract  # type: ignore
            import yaml  # type: ignore
            import os
        except ImportError:
            logger.warning('pytesseract가 설치되지 않아 OCR을 사용할 수 없습니다.')
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


    def scan_visible_cards(self) -> List[StoreCard]:
        """현재 가시 영역의 스토어 카드들 스캔 (OCR 기반)"""
        try:
            logger.info("화면 전체 OCR 스캔 시작...")
            cards = []

            # 전체 화면 캡처 후 실제 카드 영역 감지
            screenshot = pyautogui.screenshot()
            card_areas = self._detect_card_areas()

            # 각 카드 영역에서 실제 정보 추출
            for i, (x, y, width, height) in enumerate(card_areas):
                # 임시 카드 객체 생성 (나중에 실제 데이터로 업데이트)
                card = StoreCard(
                    store_name="",
                    review_count=0,
                    x=x,
                    y=y,
                    width=width,
                    height=height
                )

                # 실제 스토어명 추출
                store_name = self.read_store_name_from_list(card)
                if not store_name:
                    store_name = f"상점_{i+1}"

                # 실제 리뷰 수 추출
                review_count = self.read_review_count(card)
                if review_count is None:
                    logger.warning(f"리뷰 수 추출 실패: {store_name}")
                    continue

                # 설정 범위 체크
                review_min = self.config["search"]["review_min"]
                review_max = self.config["search"]["review_max"]

                if review_min <= review_count <= review_max:
                    # 카드 정보 업데이트
                    card.store_name = store_name
                    card.review_count = review_count
                    cards.append(card)
                    logger.info(f"유효한 카드 발견: {store_name}, 리뷰: {review_count}")
                else:
                    logger.debug(f"범위 외 카드 제외: {store_name}, 리뷰: {review_count}")

            if not cards:
                logger.warning("유효한 카드를 찾지 못했습니다.")
            else:
                logger.info(f"총 {len(cards)}개의 유효한 카드 발견")

            return cards

        except Exception as e:
            logger.error(f"카드 스캔 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _detect_card_areas(self) -> List[tuple]:
        """스토어 카드 영역 감지 (앵커 기반 추론)"""
        anchors = self.config.get("anchors", {})
        layout_cfg = self.config.get("layout", {})
        screen_width, screen_height = pyautogui.size()

        card_width = int(layout_cfg.get("card_width", 320))
        card_height = int(layout_cfg.get("card_height", 420))
        offset_x = int(layout_cfg.get("review_anchor_offset_x", 30))
        offset_y = int(layout_cfg.get("review_anchor_offset_y", 360))
        confidence = float(layout_cfg.get("anchor_confidence", 0.75))
        dedupe_px = int(layout_cfg.get("dedupe_threshold_px", 40))

        detected_cards: List[tuple] = []
        review_anchor = anchors.get("label_review")

        if review_anchor and Path(review_anchor).exists():
            try:
                matches = list(pyautogui.locateAllOnScreen(review_anchor, confidence=confidence))

                for match in matches:
                    card_x = max(0, match.left - offset_x)
                    card_y = max(0, match.top - offset_y)
                    width = min(card_width, screen_width - card_x)
                    height = min(card_height, screen_height - card_y)

                    if width <= 0 or height <= 0:
                        continue

                    if any(abs(card_x - existing[0]) < dedupe_px and abs(card_y - existing[1]) < dedupe_px for existing in detected_cards):
                        continue

                    detected_cards.append((int(card_x), int(card_y), int(width), int(height)))

                if detected_cards:
                    logger.info(f"엔진이 {len(detected_cards)}개의 카드 영역을 감지했습니다.")
                    return detected_cards

                logger.warning("리뷰 라벨 앵커를 찾지 못했습니다. 폴백 로직을 사용합니다.")

            except Exception as e:
                logger.warning(f"카드 앵커 감지 실패: {e}")
        else:
            if review_anchor:
                logger.warning(f"리뷰 라벨 앵커 경로가 존재하지 않습니다: {review_anchor}")
            else:
                logger.debug("리뷰 앵커가 설정되지 않았습니다.")

        logger.debug("앵커 기반 추론 실패로 고정 격자 폴백을 사용합니다.")

        cols = 3
        start_x = 200
        start_y = 300
        gap_x = 320
        gap_y = 420

        cards = []
        for row in range(3):
            for col in range(cols):
                x = start_x + col * gap_x
                y = start_y + row * gap_y

                if x + card_width < screen_width and y + card_height < screen_height:
                    cards.append((x, y, card_width, card_height))

        return cards

    def read_review_count(self, card: StoreCard) -> Optional[int]:
        """카드에서 리뷰 수 읽기 (OCR 기반)"""
        try:
            rel_x, rel_y, text_width, text_height = self._get_relative_region(
                'list_review_region', (10, card.height - 80, card.width - 20, 60)
            )
            text_x = card.x + rel_x
            text_y = card.y + rel_y

            pytesseract, lang = self._configure_tesseract()
            if pytesseract is None:
                logger.warning('Tesseract 설정을 찾지 못해 리뷰 수를 건너뜁니다.')
                return None

            region_image = capture_screen_region(text_x, text_y, text_width, text_height)
            if region_image is None:
                return None

            import re
            text = pytesseract.image_to_string(region_image, lang=lang)
            patterns = [
                r'\(([0-9,]+)\)\s*·\s*구매',
                r'구매\s*([0-9,]+)',
                r'리뷰\s*([0-9,]+)',
                r'([0-9,]+)\s*구매',
                r'([0-9,]+)\s*리뷰',
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    review_count = int(match.group(1).replace(',', ''))
                    logger.debug(f"리뷰 수 추출: {review_count} (패턴: {pattern})")
                    return review_count

            numbers = re.findall(r'([0-9,]+)', text)
            if numbers:
                review_count = int(numbers[0].replace(',', ''))
                logger.debug(f"리뷰 숫자 추론: {review_count}")
                return review_count

            return None

        except Exception as e:
            logger.error(f"리뷰 수 읽기 실패: {e}")
            return None

    def read_store_name_from_list(self, card: StoreCard) -> Optional[str]:
        """카드에서 스토어명 읽기"""
        try:
            rel_x, rel_y, name_width, name_height = self._get_relative_region(
                'list_name_region', (10, 10, card.width - 20, 40)
            )
            name_x = card.x + rel_x
            name_y = card.y + rel_y

            pytesseract, lang = self._configure_tesseract()
            if pytesseract is None:
                return None

            region_image = capture_screen_region(name_x, name_y, name_width, name_height)
            if region_image is None:
                return None

            text = pytesseract.image_to_string(region_image, lang=lang)
            candidates = [line.strip() for line in text.split('\n') if line.strip()]
            if candidates:
                return candidates[0]

            return None

        except Exception as e:
            logger.error(f"스토어명 읽기 실패: {e}")
            return None

