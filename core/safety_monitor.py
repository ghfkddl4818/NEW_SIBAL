#!/usr/bin/env python3
"""
API 안전 모니터링 시스템
- 비용 추적
- 호출 횟수 제한
- 에러 모니터링
- 응급 중단 기능
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger
import threading
import time


class APIUsageTracker:
    """API 사용량 추적 및 안전 관리"""

    def __init__(self, max_daily_cost: float = 1.0, max_hourly_calls: int = 100):
        self.max_daily_cost = max_daily_cost  # 일일 최대 비용 (USD)
        self.max_hourly_calls = max_hourly_calls  # 시간당 최대 호출

        self.usage_file = Path("./outputs/api_usage.json")
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)

        self.usage_data = self._load_usage_data()
        self._lock = threading.Lock()

    def _load_usage_data(self) -> Dict[str, Any]:
        """사용량 데이터 로드"""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"사용량 데이터 로드 실패: {e}")

        return {
            "daily_cost": {},
            "hourly_calls": {},
            "total_calls": 0,
            "total_cost": 0.0,
            "last_reset": datetime.now().isoformat()
        }

    def _save_usage_data(self):
        """사용량 데이터 저장"""
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"사용량 데이터 저장 실패: {e}")

    def check_limits_before_call(self) -> bool:
        """API 호출 전 한도 확인"""
        with self._lock:
            today = datetime.now().strftime("%Y-%m-%d")
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")

            # 일일 비용 확인
            daily_cost = self.usage_data["daily_cost"].get(today, 0.0)
            if daily_cost >= self.max_daily_cost:
                logger.error(f"🚨 일일 비용 한도 초과: ${daily_cost:.3f} >= ${self.max_daily_cost}")
                return False

            # 시간당 호출 확인
            hourly_calls = self.usage_data["hourly_calls"].get(current_hour, 0)
            if hourly_calls >= self.max_hourly_calls:
                logger.error(f"🚨 시간당 호출 한도 초과: {hourly_calls} >= {self.max_hourly_calls}")
                return False

            return True

    def record_api_call(self, estimated_cost: float = 0.01, success: bool = True):
        """API 호출 기록"""
        with self._lock:
            today = datetime.now().strftime("%Y-%m-%d")
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")

            # 비용 기록
            if today not in self.usage_data["daily_cost"]:
                self.usage_data["daily_cost"][today] = 0.0
            self.usage_data["daily_cost"][today] += estimated_cost

            # 호출 횟수 기록
            if current_hour not in self.usage_data["hourly_calls"]:
                self.usage_data["hourly_calls"][current_hour] = 0
            self.usage_data["hourly_calls"][current_hour] += 1

            # 전체 통계
            self.usage_data["total_calls"] += 1
            if success:
                self.usage_data["total_cost"] += estimated_cost

            # 저장
            self._save_usage_data()

            # 경고 표시
            if self.usage_data["daily_cost"][today] > self.max_daily_cost * 0.8:
                logger.warning(f"⚠️  일일 비용 80% 도달: ${self.usage_data['daily_cost'][today]:.3f}")

            if self.usage_data["hourly_calls"][current_hour] > self.max_hourly_calls * 0.8:
                logger.warning(f"⚠️  시간당 호출 80% 도달: {self.usage_data['hourly_calls'][current_hour]}")

    def get_usage_summary(self) -> Dict[str, Any]:
        """사용량 요약 정보"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")

        return {
            "today_cost": self.usage_data["daily_cost"].get(today, 0.0),
            "max_daily_cost": self.max_daily_cost,
            "current_hour_calls": self.usage_data["hourly_calls"].get(current_hour, 0),
            "max_hourly_calls": self.max_hourly_calls,
            "total_calls": self.usage_data["total_calls"],
            "total_cost": self.usage_data["total_cost"],
            "cost_percentage": (self.usage_data["daily_cost"].get(today, 0.0) / self.max_daily_cost) * 100,
            "calls_percentage": (self.usage_data["hourly_calls"].get(current_hour, 0) / self.max_hourly_calls) * 100
        }

    def emergency_stop(self) -> bool:
        """응급 중단 필요 여부 확인"""
        summary = self.get_usage_summary()

        # 한도의 90% 이상이면 응급 중단
        if summary["cost_percentage"] >= 90 or summary["calls_percentage"] >= 90:
            logger.error("🛑 응급 중단 조건 달성!")
            return True

        return False


class SafetyWrapper:
    """API 호출을 안전하게 래핑하는 클래스"""

    def __init__(self, max_daily_cost: float = 1.0, max_hourly_calls: int = 100):
        self.tracker = APIUsageTracker(max_daily_cost, max_hourly_calls)
        self.enabled = True

    def safe_api_call(self, api_func, *args, estimated_cost: float = 0.01, **kwargs):
        """안전한 API 호출"""
        if not self.enabled:
            raise Exception("🛑 안전 모드로 인해 API 호출이 차단되었습니다")

        # 응급 중단 확인
        if self.tracker.emergency_stop():
            self.enabled = False
            raise Exception("🛑 응급 중단: API 한도 초과")

        # 호출 전 한도 확인
        if not self.tracker.check_limits_before_call():
            raise Exception("🚨 API 호출 한도 초과")

        try:
            # API 호출 실행
            logger.info(f"🔒 안전 API 호출 시작 (예상 비용: ${estimated_cost:.3f})")
            result = api_func(*args, **kwargs)

            # 성공 기록
            self.tracker.record_api_call(estimated_cost, success=True)
            logger.info("✅ API 호출 성공")

            return result

        except Exception as e:
            # 실패 기록
            self.tracker.record_api_call(0, success=False)
            logger.error(f"❌ API 호출 실패: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        summary = self.tracker.get_usage_summary()
        summary["safety_enabled"] = self.enabled
        return summary

    def enable_safety(self):
        """안전 모드 활성화"""
        self.enabled = True
        logger.info("🔒 API 안전 모드 활성화")

    def disable_safety(self):
        """안전 모드 비활성화 (위험!)"""
        self.enabled = False
        logger.warning("⚠️  API 안전 모드 비활성화 - 위험!")


# 전역 안전 래퍼 인스턴스
api_safety = SafetyWrapper(max_daily_cost=2.0, max_hourly_calls=50)


class RuntimeSafetyMonitor:
    """런타임 및 메모리 안전 모니터링"""

    def __init__(self, max_runtime_hours=6, memory_threshold_mb=2048):
        self.start_time = time.time()
        self.max_runtime_hours = max_runtime_hours
        self.memory_threshold_mb = memory_threshold_mb
        self.emergency_stop_triggered = False

    def check_runtime_limit(self):
        """실행 시간 제한 체크"""
        elapsed_hours = (time.time() - self.start_time) / 3600
        if elapsed_hours > self.max_runtime_hours:
            self.emergency_stop_triggered = True
            raise RuntimeError(f"최대 실행 시간 초과: {elapsed_hours:.1f}시간")
        return elapsed_hours

    def check_memory_usage(self):
        """메모리 사용량 체크"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            if memory_mb > self.memory_threshold_mb:
                self.emergency_stop_triggered = True
                raise RuntimeError(f"메모리 사용량 초과: {memory_mb:.1f}MB > {self.memory_threshold_mb}MB")

            return memory_mb
        except ImportError:
            logger.warning("psutil 모듈이 없어 메모리 모니터링 불가")
            return 0

    def emergency_stop_check(self):
        """응급 중단 조건 종합 체크"""
        if self.emergency_stop_triggered:
            return True

        try:
            runtime_hours = self.check_runtime_limit()
            memory_mb = self.check_memory_usage()

            # 경고 레벨 체크 (80% 도달시)
            if runtime_hours > self.max_runtime_hours * 0.8:
                logger.warning(f"⚠️ 실행시간 80% 도달: {runtime_hours:.1f}/{self.max_runtime_hours}시간")

            if memory_mb > self.memory_threshold_mb * 0.8:
                logger.warning(f"⚠️ 메모리 사용량 80% 도달: {memory_mb:.1f}/{self.memory_threshold_mb}MB")

            return False

        except RuntimeError as e:
            logger.error(f"🛑 응급 중단: {e}")
            return True

    def get_status(self):
        """현재 안전 상태 반환"""
        elapsed_hours = (time.time() - self.start_time) / 3600
        try:
            import psutil
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            memory_mb = 0

        return {
            'runtime_hours': elapsed_hours,
            'max_runtime_hours': self.max_runtime_hours,
            'memory_mb': memory_mb,
            'memory_threshold_mb': self.memory_threshold_mb,
            'emergency_stop_triggered': self.emergency_stop_triggered,
            'runtime_percentage': (elapsed_hours / self.max_runtime_hours) * 100,
            'memory_percentage': (memory_mb / self.memory_threshold_mb) * 100 if memory_mb > 0 else 0
        }


class ComprehensiveSafetyMonitor:
    """API + 런타임 종합 안전 모니터링"""

    def __init__(self, max_daily_cost=2.0, max_hourly_calls=50, max_runtime_hours=6, memory_threshold_mb=2048):
        self.api_safety = SafetyWrapper(max_daily_cost, max_hourly_calls)
        self.runtime_safety = RuntimeSafetyMonitor(max_runtime_hours, memory_threshold_mb)

    def comprehensive_safety_check(self):
        """종합 안전 검사"""
        # API 안전 검사
        if self.api_safety.tracker.emergency_stop():
            logger.error("🛑 API 사용량 한도 초과로 응급 중단")
            return False

        # 런타임 안전 검사
        if self.runtime_safety.emergency_stop_check():
            logger.error("🛑 런타임/메모리 한도 초과로 응급 중단")
            return False

        return True

    def get_comprehensive_status(self):
        """종합 안전 상태 반환"""
        api_status = self.api_safety.get_status()
        runtime_status = self.runtime_safety.get_status()

        return {
            'api': api_status,
            'runtime': runtime_status,
            'overall_safe': self.comprehensive_safety_check()
        }


# 전역 종합 안전 모니터
comprehensive_safety = ComprehensiveSafetyMonitor()


if __name__ == "__main__":
    # 테스트
    print("API 안전 모니터 테스트")

    # 상태 확인
    status = api_safety.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")

    # 가상 API 호출 테스트
    def dummy_api():
        return "API 호출 성공"

    try:
        result = api_safety.safe_api_call(dummy_api, estimated_cost=0.005)
        print(f"결과: {result}")
    except Exception as e:
        print(f"오류: {e}")