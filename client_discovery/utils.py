"""
공통 유틸리티 함수들
"""
import time
import random
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import logging
from typing import Optional, Tuple
from pathlib import Path
import re


# 로거 설정
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def wait_for_load(min_sec: float = 1.0, max_sec: float = 2.0):
    """랜덤 대기 시간"""
    wait_time = random.uniform(min_sec, max_sec)
    time.sleep(wait_time)


def find_image_on_screen(image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
    """화면에서 이미지 찾기"""
    try:
        if not Path(image_path).exists():
            logger.warning(f"앵커 이미지가 없습니다: {image_path}")
            return None

        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            return (center.x, center.y)
        return None

    except Exception as e:
        logger.error(f"이미지 검색 실패 {image_path}: {e}")
        return None


def extract_numbers_from_text(text: str) -> Optional[int]:
    """텍스트에서 숫자 추출 (쉼표 제거)"""
    try:
        # 숫자와 쉼표만 추출
        numbers = re.findall(r'([\d,]+)', text)
        if numbers:
            # 쉼표 제거 후 정수 변환
            clean_number = numbers[0].replace(',', '')
            return int(clean_number)
        return None
    except (ValueError, IndexError):
        return None


def capture_screen_region(x: int, y: int, width: int, height: int) -> np.ndarray:
    """화면 영역 캡처"""
    try:
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.error(f"화면 캡처 실패: {e}")
        return None


def save_screenshot(filename: str, region: Optional[Tuple[int, int, int, int]] = None):
    """스크린샷 저장"""
    try:
        screenshot_dir = Path("client_discovery/screens")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        filepath = screenshot_dir / filename
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        screenshot.save(filepath)
        logger.info(f"스크린샷 저장: {filepath}")

    except Exception as e:
        logger.error(f"스크린샷 저장 실패: {e}")


def is_browser_focused() -> bool:
    """브라우저가 포커스되어 있는지 확인"""
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            title = active_window.title.lower()
            logger.debug(f"활성 창 제목: {title}")
            # 네이버, 쇼핑, chrome, edge 등 브라우저 관련 키워드 포함 시 True
            browser_keywords = ['chrome', 'firefox', 'edge', 'safari', 'naver', 'shopping', '네이버', '쇼핑']
            is_focused = any(keyword in title for keyword in browser_keywords)
            logger.debug(f"브라우저 포커스: {is_focused}")
            return is_focused
        return False
    except Exception as e:
        logger.warning(f"브라우저 포커스 확인 실패: {e}")
        return True  # 확인 실패 시 True로 가정


def extract_review_count_from_region(x: int, y: int, width: int, height: int) -> Optional[int]:
    """특정 영역에서 리뷰 수 추출"""
    try:
        # 화면 캡처
        region_image = capture_screen_region(x, y, width, height)
        if region_image is None:
            return None

        # OCR 처리 (pytesseract 필요)
        try:
            import pytesseract
            import yaml
            import os
            # Tesseract 경로 설정 (config.yaml에서 읽기)
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                tesseract_cmd = config_data.get('ocr', {}).get('tesseract_cmd', r'E:\tesseract\tesseract.exe')
            else:
                tesseract_cmd = r'E:\tesseract\tesseract.exe'  # 기본값
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            text = pytesseract.image_to_string(region_image, lang='kor+eng')
            logger.debug(f"OCR 텍스트: {text}")

            # 리뷰 패턴 매칭
            review_pattern = r'리뷰\s*([\d,]+)'
            match = re.search(review_pattern, text)
            if match:
                return int(match.group(1).replace(',', ''))

            # 숫자만 추출
            return extract_numbers_from_text(text)

        except ImportError:
            logger.warning("pytesseract가 설치되지 않음. OCR 기능 비활성화")
            return None

    except Exception as e:
        logger.error(f"리뷰 수 추출 실패: {e}")
        return None


def extract_interest_count_from_region(x: int, y: int, width: int, height: int) -> Optional[int]:
    """특정 영역에서 관심고객 수 추출"""
    try:
        # 화면 캡처
        region_image = capture_screen_region(x, y, width, height)
        if region_image is None:
            return None

        # OCR 처리
        try:
            import pytesseract
            import yaml
            import os
            # Tesseract 경로 설정 (config.yaml에서 읽기)
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                tesseract_cmd = config_data.get('ocr', {}).get('tesseract_cmd', r'E:\tesseract\tesseract.exe')
            else:
                tesseract_cmd = r'E:\tesseract\tesseract.exe'  # 기본값
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            text = pytesseract.image_to_string(region_image, lang='kor+eng')
            logger.debug(f"관심고객 OCR 텍스트: {text}")

            # 숫자 추출
            return extract_numbers_from_text(text)

        except ImportError:
            logger.warning("pytesseract가 설치되지 않음. OCR 기능 비활성화")
            return None

    except Exception as e:
        logger.error(f"관심고객 수 추출 실패: {e}")
        return None


def get_current_url() -> Optional[str]:
    """현재 브라우저 URL 가져오기"""
    try:
        # 주소창 클릭 후 복사
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)

        import pyperclip
        url = pyperclip.paste()
        return url if url and url.startswith('http') else None

    except Exception as e:
        logger.error(f"URL 추출 실패: {e}")
        return None


def detect_suspicious_screen() -> bool:
    """의심스러운 화면 감지 (캡챠, 로그인 등)"""
    try:
        # 화면 전체 캡처
        screenshot = pyautogui.screenshot()

        # 간단한 텍스트 기반 감지
        try:
            import pytesseract
            import yaml
            import os
            # Tesseract 경로 설정 (config.yaml에서 읽기)
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                tesseract_cmd = config_data.get('ocr', {}).get('tesseract_cmd', r'E:\tesseract\tesseract.exe')
            else:
                tesseract_cmd = r'E:\tesseract\tesseract.exe'  # 기본값
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            text = pytesseract.image_to_string(screenshot, lang='kor+eng').lower()

            suspicious_keywords = [
                'captcha', '캡챠', '로그인', 'login', '자동', '로봇', 'robot',
                '보안', 'security', '차단', 'blocked', '접근', 'access',
                '중단', '인증', '재확인'
            ]

            return any(keyword in text for keyword in suspicious_keywords)

        except ImportError:
            # OCR 없이는 기본적으로 안전하다고 가정
            return False

    except Exception as e:
        logger.error(f"의심 화면 감지 실패: {e}")
        return False
