#!/usr/bin/env python3
"""
2단계 GUI 실행기
"""

import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from gui.two_stage_gui import main
    print("🎯 2단계 분리 처리 GUI를 시작합니다...")
    main()
except Exception as e:
    print(f"❌ GUI 시작 실패: {e}")
    input("아무 키나 눌러주세요...")