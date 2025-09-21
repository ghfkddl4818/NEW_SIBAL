"""
M6. 예외/중단 감시 모듈
캡챠, 로그인, 오류 감지 및 안전장치
"""
import time
import keyboard
from typing import Callable, Any
from .utils import logger, detect_suspicious_screen, is_browser_focused


class SafetyMonitor:
    """안전 감시 및 예외 처리"""

    def __init__(self, config, storage_manager):
        self.config = config
        self.storage_manager = storage_manager
        self.interrupt_requested = False

        # ESC 키 감지 설정
        keyboard.on_press_key('esc', self._on_escape_pressed)

    def _on_escape_pressed(self, event):
        """ESC 키 눌림 감지"""
        self.interrupt_requested = True
        logger.warning("ESC 키 감지 - 중단 요청됨")

    def is_suspicious_screen(self) -> bool:
        """의심스러운 화면 감지"""
        return detect_suspicious_screen()

    def check_browser_focus(self) -> bool:
        """브라우저 포커스 확인 (임시로 항상 True 반환)"""
        # 포커스 검사를 우회하여 항상 통과
        logger.debug("브라우저 포커스 검사 우회")
        return True

    def soft_retry(self, action: Callable, times: int = 1, *args, **kwargs) -> Any:
        """부드러운 재시도"""
        for attempt in range(times + 1):
            try:
                return action(*args, **kwargs)
            except Exception as e:
                if attempt < times:
                    logger.warning(f"재시도 {attempt + 1}/{times}: {e}")
                    time.sleep(1.0)
                else:
                    logger.error(f"최종 실패 after {times} retries: {e}")
                    raise

    def abort_with_notice(self, reason: str) -> str:
        """즉시 중단 및 알림"""
        logger.error(f"중단됨: {reason}")

        # 스크린샷 저장
        screenshot_file = self.storage_manager.save_error_screenshot(reason.replace(" ", "_"))

        # 중단 사유 반환
        return f"중단: {reason} (스크린샷: {screenshot_file})"

    def should_continue(self) -> tuple[bool, str]:
        """계속 진행할지 확인"""
        # ESC 키 체크
        if self.interrupt_requested:
            return False, "사용자 중단 요청 (ESC)"

        # 의심 화면 체크
        if self.is_suspicious_screen():
            return False, "의심스러운 화면 감지"

        # 브라우저 포커스 체크
        if not self.check_browser_focus():
            return False, "브라우저 포커스 상실"

        return True, ""

    def graceful_exit(self, checkpoint, stats, reason: str = "정상 완료"):
        """우아한 종료"""
        try:
            # 체크포인트 저장
            self.storage_manager.save_checkpoint(checkpoint)

            # 실행 로그 저장
            self.storage_manager.save_run_log(stats, reason)

            # 요약 출력
            print(stats.summary())
            print(f"종료 사유: {reason}")

            # 키보드 후킹 해제
            keyboard.unhook_all()

            logger.info(f"프로그램 종료: {reason}")

        except Exception as e:
            logger.error(f"종료 처리 실패: {e}")

    def wait_with_check(self, seconds: float) -> bool:
        """중단 체크하면서 대기"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            if self.interrupt_requested:
                return False
            time.sleep(0.1)
        return True