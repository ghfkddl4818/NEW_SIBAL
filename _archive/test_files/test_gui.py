#!/usr/bin/env python3
"""
GUI 테스트용 간단 실행 파일
"""

import tkinter as tk
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("GUI 모듈 import 시도...")
    from gui.complete_automation_gui import CompleteAutomationGUI

    print("GUI 실행 중...")
    root = tk.Tk()
    app = CompleteAutomationGUI(root)

    print("GUI 준비 완료. 창을 확인해주세요.")
    root.mainloop()

except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
    input("엔터를 눌러 종료...")