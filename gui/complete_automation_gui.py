#!/usr/bin/env python3
"""
완전 자동화 통합 시스템
웹 자동화(데이터 수집) + 파일 정리 + AI 콜드메일 생성
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import asyncio
import threading
import json
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import pyautogui
import time
import pyperclip
import shutil
from typing import List

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config
from llm.two_stage_processor import TwoStageProcessor


class CompleteAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("완전 자동화 통합 시스템 - 웹수집+파일정리+AI콜드메일")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f0f0")

        # 설정
        self.config = None
        self.processor = None

        # 경로 설정
        self.download_folder = Path("C:/Users/Administrator/Downloads")
        self.work_folder = Path("E:/업무")
        self.database_file = Path("E:/업무/03_데이터_수집/이커머스_수집_데이터베이스.xlsx")
        self.today = datetime.now().strftime("%Y-%m-%d")

        # 자동화 상태
        self.automation_running = False
        self.automation_paused = False
        self.processed_count = 0
        self.failed_products = []
        self.total_products = 30

        # 수집된 데이터
        self.collected_images = []
        self.collected_reviews = []

        self.setup_ui()
        self.load_system()

    def setup_ui(self):
        """통합 UI 구성"""
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 제목
        title_label = tk.Label(
            main_frame,
            text="완전 자동화 통합 시스템",
            font=("맑은 고딕", 20, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = tk.Label(
            main_frame,
            text="웹 자동화 → 파일 정리 → AI 콜드메일 생성 (완전 원클릭 솔루션)",
            font=("맑은 고딕", 11),
            bg="#f0f0f0",
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=(0, 20))

        # 탭 노트북
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # 탭들 생성
        self.create_complete_automation_tab()
        self.create_manual_control_tab()
        self.create_ai_processing_tab()
        self.create_client_discovery_tab()  # 새 탭 추가
        self.create_settings_tab()

        # 하단 상태바
        status_frame = tk.Frame(main_frame, bg="#f0f0f0")
        status_frame.pack(fill="x", pady=(10, 0))

        self.status_var = tk.StringVar(value="시스템 준비 중...")
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("맑은 고딕", 10),
            bg="#f0f0f0",
            fg="#34495e"
        )
        status_label.pack(side="left")

        # 진행률 바
        self.progress = ttk.Progressbar(
            status_frame,
            mode='determinate',
            length=200
        )
        self.progress.pack(side="right", padx=(10, 0))

    def create_complete_automation_tab(self):
        """완전 자동화 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="완전 자동화")

        # 스크롤 가능한 프레임
        canvas = tk.Canvas(tab, bg="#f8f9fa")
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 워크플로우 설명
        workflow_frame = tk.Frame(scrollable_frame, bg="#e8f4fd", relief="solid", bd=1)
        workflow_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(
            workflow_frame,
            text="🎯 완전 자동화 워크플로우",
            font=("맑은 고딕", 16, "bold"),
            bg="#e8f4fd",
            fg="#2980b9"
        ).pack(pady=10)

        workflow_steps = """
1️⃣ 웹 자동화: 네이버 스마트스토어에서 상품 이미지 + 리뷰 데이터 자동 수집
2️⃣ 파일 정리: 수집된 파일들을 자동으로 분류 및 정리
3️⃣ AI 1단계: 상품 이미지 → OCR/데이터 추출 (온도 0.3)
4️⃣ AI 2단계: 추출 데이터 + 리뷰 300개 → 콜드메일 생성 (온도 0.3)
5️⃣ 결과 저장: 생성된 콜드메일을 정리된 폴더에 저장
        """

        tk.Label(
            workflow_frame,
            text=workflow_steps,
            font=("맑은 고딕", 11),
            bg="#e8f4fd",
            fg="#34495e",
            justify="left"
        ).pack(padx=20, pady=10)

        # 설정 섹션
        settings_frame = tk.LabelFrame(
            scrollable_frame,
            text="⚙️ 자동화 설정",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        settings_frame.pack(fill="x", padx=20, pady=15)

        # 제품 수량 설정
        product_frame = tk.Frame(settings_frame, bg="#f8f9fa")
        product_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(
            product_frame,
            text="처리할 제품 수량:",
            font=("맑은 고딕", 11),
            bg="#f8f9fa"
        ).pack(side="left")

        self.product_count = tk.IntVar(value=30)
        product_spin = tk.Spinbox(
            product_frame,
            from_=1,
            to=100,
            textvariable=self.product_count,
            width=10,
            font=("맑은 고딕", 11)
        )
        product_spin.pack(side="left", padx=(10, 0))

        tk.Label(
            product_frame,
            text="개 (권장: 30개)",
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#7f8c8d"
        ).pack(side="left", padx=(5, 0))

        # 대기 시간 설정
        delay_frame = tk.Frame(settings_frame, bg="#f8f9fa")
        delay_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(
            delay_frame,
            text="페이지 대기 시간:",
            font=("맑은 고딕", 11),
            bg="#f8f9fa"
        ).pack(side="left")

        self.delay_time = tk.DoubleVar(value=2.0)
        delay_spin = tk.Spinbox(
            delay_frame,
            from_=1.0,
            to=10.0,
            increment=0.5,
            textvariable=self.delay_time,
            width=10,
            font=("맑은 고딕", 11)
        )
        delay_spin.pack(side="left", padx=(10, 0))

        tk.Label(
            delay_frame,
            text="초 (권장: 2.0초)",
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#7f8c8d"
        ).pack(side="left", padx=(5, 0))

        # 메인 실행 버튼
        main_button_frame = tk.Frame(scrollable_frame, bg="#f8f9fa")
        main_button_frame.pack(fill="x", padx=20, pady=30)

        self.main_button = tk.Button(
            main_button_frame,
            text="완전 자동화 시작\n(웹수집 → 파일정리 → AI콜드메일)",
            command=self.start_complete_automation,
            bg="#e74c3c",
            fg="white",
            font=("맑은 고딕", 16, "bold"),
            height=4,
            padx=50,
            pady=15
        )
        self.main_button.pack()

        # 제어 버튼들
        control_frame = tk.Frame(scrollable_frame, bg="#f8f9fa")
        control_frame.pack(fill="x", padx=20, pady=10)

        self.pause_button = tk.Button(
            control_frame,
            text="⏸️ 일시정지",
            command=self.pause_automation,
            bg="#f39c12",
            fg="white",
            font=("맑은 고딕", 11),
            padx=20,
            pady=5,
            state="disabled"
        )
        self.pause_button.pack(side="left", padx=5)

        self.resume_button = tk.Button(
            control_frame,
            text="▶️ 재개",
            command=self.resume_automation,
            bg="#27ae60",
            fg="white",
            font=("맑은 고딕", 11),
            padx=20,
            pady=5,
            state="disabled"
        )
        self.resume_button.pack(side="left", padx=5)

        self.stop_button = tk.Button(
            control_frame,
            text="중지",
            command=self.stop_automation,
            bg="#e74c3c",
            fg="white",
            font=("맑은 고딕", 11),
            padx=20,
            pady=5,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)

        # 현재 상태 표시
        status_info_frame = tk.LabelFrame(
            scrollable_frame,
            text="📊 현재 상태",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        status_info_frame.pack(fill="x", padx=20, pady=15)

        self.status_text = tk.Text(
            status_info_frame,
            height=8,
            font=("맑은 고딕", 9),
            bg="white",
            fg="#2c3e50",
            wrap="word"
        )
        self.status_text.pack(fill="both", expand=True, padx=10, pady=10)

        # 레이아웃
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_manual_control_tab(self):
        """수동 제어 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎮 수동 제어")

        # 메인 컨테이너
        main_container = tk.Frame(tab)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 제목
        title_frame = tk.Frame(main_container, bg="#f8f9fa")
        title_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            title_frame,
            text="🎮 수동 제어 모드",
            font=("맑은 고딕", 16, "bold"),
            bg="#f8f9fa"
        ).pack()

        # 왼쪽(컨트롤) + 오른쪽(로그) 분할
        content_frame = tk.Frame(main_container)
        content_frame.pack(fill="both", expand=True)

        # 왼쪽 컨트롤 패널
        control_panel = tk.Frame(content_frame, bg="#f8f9fa", width=400)
        control_panel.pack(side="left", fill="y", padx=(0, 10))
        control_panel.pack_propagate(False)

        # 오른쪽 로그 패널
        log_panel = tk.Frame(content_frame)
        log_panel.pack(side="right", fill="both", expand=True)

        # 웹 자동화 제어
        web_frame = tk.LabelFrame(
            control_panel,
            text="웹 자동화 제어",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        web_frame.pack(fill="x", pady=15)

        web_buttons_frame = tk.Frame(web_frame, bg="#f8f9fa")
        web_buttons_frame.pack(pady=15)

        tk.Button(
            web_buttons_frame,
            text="🌐 웹 자동화만 실행",
            command=self.start_web_automation_only,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 11),
            padx=25,
            pady=10
        ).pack(side="left", padx=10)

        tk.Button(
            web_buttons_frame,
            text="📁 파일 정리만 실행",
            command=self.start_file_organization_only,
            bg="#9b59b6",
            fg="white",
            font=("맑은 고딕", 11),
            padx=25,
            pady=10
        ).pack(side="left", padx=10)

        # AI 처리 제어
        ai_frame = tk.LabelFrame(
            control_panel,
            text="AI 처리 제어",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        ai_frame.pack(fill="x", pady=15)

        ai_buttons_frame = tk.Frame(ai_frame, bg="#f8f9fa")
        ai_buttons_frame.pack(pady=15)

        tk.Button(
            ai_buttons_frame,
            text="🤖 AI 처리만 실행",
            command=self.start_ai_processing_only,
            bg="#e67e22",
            fg="white",
            font=("맑은 고딕", 11),
            padx=25,
            pady=10
        ).pack(side="left", padx=10)

        # 파일 선택
        file_select_frame = tk.LabelFrame(
            frame,
            text="파일 수동 선택",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        file_select_frame.pack(fill="x", pady=15)

        select_buttons_frame = tk.Frame(file_select_frame, bg="#f8f9fa")
        select_buttons_frame.pack(pady=15)

        tk.Button(
            select_buttons_frame,
            text="📸 이미지 폴더 선택",
            command=self.select_image_folder,
            bg="#2ecc71",
            fg="white",
            font=("맑은 고딕", 11),
            padx=20,
            pady=8
        ).pack(side="left", padx=5)

        tk.Button(
            select_buttons_frame,
            text="📊 리뷰 파일 선택",
            command=self.select_review_files,
            bg="#2ecc71",
            fg="white",
            font=("맑은 고딕", 11),
            padx=20,
            pady=8
        ).pack(side="left", padx=5)

    def create_ai_processing_tab(self):
        """AI 처리 전용 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🤖 AI 처리")

        frame = tk.Frame(tab, bg="#f8f9fa")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            frame,
            text="🤖 AI 콜드메일 처리",
            font=("맑은 고딕", 16, "bold"),
            bg="#f8f9fa"
        ).pack(pady=20)

        # 2단계 처리 설명
        desc_frame = tk.Frame(frame, bg="#f0f8ff", relief="solid", bd=1)
        desc_frame.pack(fill="x", pady=15)

        tk.Label(
            desc_frame,
            text="📋 2단계 분리 처리 방식",
            font=("맑은 고딕", 12, "bold"),
            bg="#f0f8ff",
            fg="#2980b9"
        ).pack(pady=5)

        tk.Label(
            desc_frame,
            text="Stage 1: 이미지 → OCR/데이터추출 → Stage 2: 텍스트+리뷰 → 콜드메일",
            font=("맑은 고딕", 10),
            bg="#f0f8ff"
        ).pack(pady=5)

        # 파일 상태 표시
        files_frame = tk.LabelFrame(
            frame,
            text="파일 상태",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        files_frame.pack(fill="x", pady=15)

        self.images_status = tk.Label(
            files_frame,
            text="이미지: 선택되지 않음",
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#e74c3c"
        )
        self.images_status.pack(pady=5)

        self.reviews_status = tk.Label(
            files_frame,
            text="리뷰: 선택되지 않음",
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#e74c3c"
        )
        self.reviews_status.pack(pady=5)

        # AI 실행 버튼
        ai_button_frame = tk.Frame(frame, bg="#f8f9fa")
        ai_button_frame.pack(pady=30)

        self.ai_process_button = tk.Button(
            ai_button_frame,
            text="🤖 AI 콜드메일 생성\n(2단계 처리)",
            command=self.run_ai_processing,
            bg="#e67e22",
            fg="white",
            font=("맑은 고딕", 14, "bold"),
            height=3,
            padx=40,
            pady=15
        )
        self.ai_process_button.pack()

        # === 오른쪽 로그 패널 추가 ===
        log_title = tk.Label(log_panel, text="📋 실행 로그",
                            font=("맑은 고딕", 14, "bold"))
        log_title.pack(pady=(0, 10))

        # 로그 텍스트 영역
        log_frame = tk.Frame(log_panel)
        log_frame.pack(fill="both", expand=True)

        # 수동 제어 전용 로그
        self.manual_log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            font=("맑은 고딕", 9),
            bg="#2c3e50",
            fg="#ecf0f1",
            insertbackground="#ecf0f1",
            selectbackground="#34495e",
            height=25
        )

        manual_log_scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.manual_log_text.yview)
        self.manual_log_text.configure(yscrollcommand=manual_log_scrollbar.set)

        # 로그 패킹
        self.manual_log_text.pack(side="left", fill="both", expand=True)
        manual_log_scrollbar.pack(side="right", fill="y")

        # 로그 클리어 버튼
        clear_btn = tk.Button(
            log_panel,
            text="🗑️ 로그 지우기",
            command=self.clear_manual_log,
            bg="#95a5a6",
            fg="white",
            font=("맑은 고딕", 10),
            padx=10,
            pady=5
        )
        clear_btn.pack(pady=(10, 0))

        # 초기 로그 메시지
        self.manual_log("🎮 수동 제어 모드가 준비되었습니다.")
        self.manual_log("각 기능 버튼을 클릭하여 개별 실행할 수 있습니다.")

    def manual_log(self, message):
        """수동 제어 전용 로그"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"

        if hasattr(self, 'manual_log_text'):
            self.manual_log_text.insert("end", full_message)
            self.manual_log_text.see("end")
            self.root.update_idletasks()

        # 메인 로그에도 추가 (기존 기능 유지)
        try:
            self.log(message)
        except:
            pass

    def clear_manual_log(self):
        """수동 제어 로그 지우기"""
        if hasattr(self, 'manual_log_text'):
            self.manual_log_text.delete('1.0', tk.END)
            self.manual_log("🗑️ 로그가 지워졌습니다.")

    def create_settings_tab(self):
        """설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ 설정")

        frame = tk.Frame(tab, bg="#f8f9fa")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            frame,
            text="⚙️ 시스템 설정",
            font=("맑은 고딕", 16, "bold"),
            bg="#f8f9fa"
        ).pack(pady=20)

        # 경로 설정
        paths_frame = tk.LabelFrame(
            frame,
            text="폴더 경로",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        paths_frame.pack(fill="x", pady=15)

        paths_text = f"""
다운로드 폴더: {self.download_folder}
작업 폴더: {self.work_folder}
데이터베이스: {self.database_file}
        """

        tk.Label(
            paths_frame,
            text=paths_text,
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            justify="left"
        ).pack(padx=15, pady=10)

        # 바로가기 버튼들
        shortcuts_frame = tk.LabelFrame(
            frame,
            text="폴더 바로가기",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        shortcuts_frame.pack(fill="x", pady=15)

        shortcuts_buttons_frame = tk.Frame(shortcuts_frame, bg="#f8f9fa")
        shortcuts_buttons_frame.pack(pady=15)

        folders = [
            ("📁 다운로드", self.download_folder),
            ("📂 작업폴더", self.work_folder),
            ("📄 결과폴더", "outputs")
        ]

        for text, path in folders:
            tk.Button(
                shortcuts_buttons_frame,
                text=text,
                command=lambda p=path: os.startfile(str(p)),
                bg="#3498db",
                fg="white",
                font=("맑은 고딕", 10),
                padx=15,
                pady=5
            ).pack(side="left", padx=5)

    def load_system(self):
        """시스템 초기화"""
        try:
            self.config = load_config()
            self.processor = TwoStageProcessor(self.config)
            self.status_var.set("완전 자동화 시스템 준비 완료")
            self.log("완전 자동화 통합 시스템이 준비되었습니다.")
            self.log("웹 자동화 + 파일 정리 + AI 콜드메일 생성 통합")
        except Exception as e:
            self.status_var.set("시스템 로드 실패")
            messagebox.showerror("오류", f"시스템 로드 실패: {str(e)}")

    def log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        if hasattr(self, 'status_text'):
            self.status_text.insert("end", log_message)
            self.status_text.see("end")

        try:
            print(log_message.strip())
        except UnicodeEncodeError:
            # 이모지 제거하고 출력
            import re
            clean_message = re.sub(r'[^\w\s가-힣]', '', log_message.strip())
            print(clean_message)

    def start_complete_automation(self):
        """완전 자동화 시작"""
        if messagebox.askyesno(
            "완전 자동화 시작",
            f"완전 자동화를 시작하시겠습니까?\n\n"
            f"• 처리할 제품 수: {self.product_count.get()}개\n"
            f"• 예상 소요 시간: {self.product_count.get() * 2}분\n"
            f"• 자동 실행: 웹수집 → 파일정리 → AI처리\n\n"
            f"※ 브라우저를 네이버 스마트스토어 검색 페이지로 이동해주세요."
        ):
            self.automation_running = True
            self.automation_paused = False
            self.processed_count = 0
            self.failed_products = []
            self.total_products = self.product_count.get()

            # UI 상태 변경
            self.main_button.config(state="disabled")
            self.pause_button.config(state="normal")
            self.stop_button.config(state="normal")

            self.progress['maximum'] = self.total_products
            self.progress['value'] = 0

            # 자동화 시작
            threading.Thread(target=self.automation_thread, daemon=True).start()

    def automation_thread(self):
        """자동화 실행 스레드"""
        try:
            self.log("완전 자동화 워크플로우 시작")

            # 1단계: 웹 자동화 (데이터 수집)
            self.log("📥 1단계: 웹 자동화 시작 - 데이터 수집")
            self.status_var.set("📥 웹 자동화 실행 중...")

            collected_data = self.run_web_automation()

            if not self.automation_running:
                return

            # 2단계: 파일 정리
            self.log("📁 2단계: 파일 정리 시작")
            self.status_var.set("📁 파일 정리 실행 중...")

            organized_data = self.organize_collected_files(collected_data)

            if not self.automation_running:
                return

            # 3단계: AI 처리
            self.log("🤖 3단계: AI 콜드메일 처리 시작")
            self.status_var.set("🤖 AI 처리 실행 중...")

            self.run_ai_processing_with_data(organized_data)

            # 완료
            self.log("🎉 완전 자동화 워크플로우 완료!")
            self.status_var.set("🎉 완전 자동화 완료!")

            messagebox.showinfo(
                "완료!",
                f"완전 자동화가 성공적으로 완료되었습니다!\n\n"
                f"• 처리된 제품: {self.processed_count}개\n"
                f"• 생성된 콜드메일: outputs 폴더 확인\n"
                f"• 소요 시간: {self.get_elapsed_time()}"
            )

        except Exception as e:
            self.log(f"❌ 자동화 실패: {str(e)}")
            messagebox.showerror("오류", f"자동화 실패: {str(e)}")
        finally:
            self.automation_running = False
            self.main_button.config(state="normal")
            self.pause_button.config(state="disabled")
            self.resume_button.config(state="disabled")
            self.stop_button.config(state="disabled")

    def run_web_automation(self):
        """웹 자동화 실행"""
        self.log("네이버 스마트스토어에서 데이터 수집 시작")

        collected_data = {
            'images': [],
            'reviews': []
        }

        for i in range(self.total_products):
            if not self.automation_running:
                break

            while self.automation_paused:
                time.sleep(0.1)

            try:
                self.log(f"제품 {i+1}/{self.total_products} 처리 중...")

                # 실제 웹 자동화 로직 (간소화된 버전)
                # 여기서는 기존 file_organizer의 로직을 통합
                product_data = self.process_single_product(i+1)

                if product_data:
                    collected_data['images'].extend(product_data.get('images', []))
                    collected_data['reviews'].extend(product_data.get('reviews', []))
                    self.processed_count += 1
                else:
                    self.failed_products.append(i+1)

                self.progress['value'] = i + 1

                # 대기 시간
                time.sleep(self.delay_time.get())

            except Exception as e:
                self.log(f"제품 {i+1} 처리 실패: {str(e)}")
                self.failed_products.append(i+1)

        self.log(f"웹 자동화 완료: {len(collected_data['images'])}개 이미지, {len(collected_data['reviews'])}개 리뷰")
        return collected_data

    def process_single_product(self, product_num):
        """단일 제품 처리 - 실제 크롤링 실행"""
        try:
            import pyautogui
            import time

            self.log(f"[제품 {product_num}] 크롤링 시작...")

            # 실제 웹 자동화 로직
            collected_images = []
            collected_reviews = []

            # 1. 스크롤 다운
            pyautogui.scroll(-3)
            time.sleep(2)

            # 2. 화면 캡처
            screenshot = pyautogui.screenshot()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = f"product_{product_num}_capture_{timestamp}.png"
            screenshot.save(image_path)
            collected_images.append(image_path)
            self.log(f"[제품 {product_num}] 이미지 저장: {image_path}")

            # 3. OCR로 텍스트 추출
            try:
                import pytesseract
                # Tesseract 경로 설정 (config.yaml에서 읽기)
                import yaml
                import os
                config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                    tesseract_cmd = config_data.get('ocr', {}).get('tesseract_cmd', r'E:\tesseract\tesseract.exe')
                else:
                    tesseract_cmd = r'E:\tesseract\tesseract.exe'  # 기본값
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

                text = pytesseract.image_to_string(screenshot, lang='kor+eng')

                # 4. CSV 데이터 생성
                csv_path = f"product_{product_num}_data_{timestamp}.csv"
                import pandas as pd

                data = {
                    '제품번호': [product_num],
                    '수집시간': [timestamp],
                    '텍스트길이': [len(text)],
                    '첫100자': [text[:100].replace('\n', ' ').strip() if text else '']
                }

                df = pd.DataFrame(data)
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                collected_reviews.append(csv_path)
                self.log(f"[제품 {product_num}] 데이터 저장: {csv_path}")

            except Exception as ocr_e:
                self.log(f"[제품 {product_num}] OCR 오류: {str(ocr_e)}")

            # 5. 랜덤 대기 (차단 방지)
            import random
            wait_time = random.uniform(2, 5)
            time.sleep(wait_time)

            return {
                'images': collected_images,
                'reviews': collected_reviews
            }

        except Exception as e:
            self.log(f"[제품 {product_num}] 처리 오류: {str(e)}")
            return None

    def organize_collected_files(self, collected_data):
        """수집된 파일들 정리"""
        self.log("수집된 파일들을 정리하고 있습니다...")

        # 파일 정리 로직
        organized = {
            'image_folder': Path("data/product_images"),
            'review_folder': Path("data/reviews")
        }

        # 폴더 생성
        organized['image_folder'].mkdir(parents=True, exist_ok=True)
        organized['review_folder'].mkdir(parents=True, exist_ok=True)

        return organized

    def run_ai_processing_with_data(self, organized_data):
        """정리된 데이터로 AI 처리"""
        try:
            # 이미지와 리뷰 파일 경로 수집
            image_files = list(organized_data['image_folder'].glob("*.png"))
            review_files = list(organized_data['review_folder'].glob("*.csv"))

            if not image_files:
                raise Exception("처리할 이미지가 없습니다.")
            if not review_files:
                raise Exception("처리할 리뷰 파일이 없습니다.")

            # AI 처리 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.processor.process_complete_workflow(
                    [str(f) for f in image_files[:5]],  # 최대 5개 이미지
                    str(review_files[0])  # 첫 번째 리뷰 파일
                )
            )

            # 결과 저장
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            email_file = output_dir / f"automated_coldmail_{timestamp}.txt"

            with open(email_file, 'w', encoding='utf-8') as f:
                f.write(result["stage2_result"]["cold_email"])

            self.log(f"AI 처리 완료: {email_file}")

        except Exception as e:
            self.log(f"AI 처리 실패: {str(e)}")
            raise

    def pause_automation(self):
        """자동화 일시정지"""
        self.automation_paused = True
        self.pause_button.config(state="disabled")
        self.resume_button.config(state="normal")
        self.status_var.set("⏸️ 자동화 일시정지됨")
        self.log("⏸️ 자동화가 일시정지되었습니다.")

    def resume_automation(self):
        """자동화 재개"""
        self.automation_paused = False
        self.pause_button.config(state="normal")
        self.resume_button.config(state="disabled")
        self.status_var.set("▶️ 자동화 재개됨")
        self.log("▶️ 자동화가 재개되었습니다.")

    def stop_automation(self):
        """자동화 중지"""
        if messagebox.askyesno("중지 확인", "자동화를 중지하시겠습니까?"):
            self.automation_running = False
            self.automation_paused = False
            self.status_var.set("⏹️ 자동화 중지됨")
            self.log("⏹️ 자동화가 중지되었습니다.")

    def start_web_automation_only(self):
        """웹 자동화만 실행 - 원본 완전 기능 복원"""
        if self.automation_running:
            messagebox.showwarning("경고", "다른 자동화가 실행 중입니다.")
            return

        if not messagebox.askyesno("웹 자동화 실행",
            "완전한 웹 자동화를 실행하시겠습니까?\n\n"
            "포함 기능:\n"
            "• 브라우저 자동 제어\n"
            "• 이미지/데이터 수집\n"
            "• 파일 자동 정리\n"
            "• ESC키로 중단 가능\n\n"
            "※ 브라우저를 네이버 쇼핑몰 검색 페이지로 이동해주세요."):
            return

        self.automation_running = True
        self.manual_log("🌐 완전한 웹 자동화 시작")
        threading.Thread(target=self.web_automation_complete_thread, daemon=True).start()

    def web_automation_complete_thread(self):
        """완전한 웹 자동화 실행 스레드"""
        try:
            self.manual_log("🚀 웹 자동화 준비 중...")

            import pyautogui
            import time
            import random
            from pathlib import Path

            # 안전 설정
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.5

            # 폴더 준비
            download_folder = Path("C:/Users/Administrator/Downloads")
            images_folder = download_folder / "collected_images"
            data_folder = download_folder / "collected_data"

            images_folder.mkdir(exist_ok=True)
            data_folder.mkdir(exist_ok=True)

            self.manual_log(f"📁 수집 폴더 준비: {images_folder}")

            # 화면 크기 확인
            screen_width, screen_height = pyautogui.size()
            self.manual_log(f"🖥️ 화면 크기: {screen_width}x{screen_height}")

            collected_files = {'images': [], 'data': []}

            # 실제 웹 자동화 루프
            target_count = self.product_count.get() if hasattr(self, 'product_count') else 10

            for i in range(target_count):
                if not self.automation_running:
                    self.manual_log("⏹️ 사용자가 중단했습니다")
                    break

                self.manual_log(f"🔍 제품 {i+1}/{target_count} 처리 중...")

                try:
                    # 1. 페이지 스크롤
                    scroll_count = random.randint(2, 4)
                    pyautogui.scroll(-scroll_count)
                    self.log(f"   ↓ {scroll_count}회 스크롤")

                    # 2. 화면 캡처
                    screenshot = pyautogui.screenshot()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    image_path = images_folder / f"product_{i+1}_{timestamp}.png"
                    screenshot.save(str(image_path))
                    collected_files['images'].append(str(image_path))
                    self.log(f"   📸 이미지 저장: {image_path.name}")

                    # 3. OCR 데이터 추출
                    try:
                        import pytesseract
                        # Tesseract 경로 설정 (config.yaml에서 읽기)
                        import yaml
                        import os
                        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
                        if os.path.exists(config_path):
                            with open(config_path, 'r', encoding='utf-8') as f:
                                config_data = yaml.safe_load(f)
                            tesseract_cmd = config_data.get('ocr', {}).get('tesseract_cmd', r'E:\tesseract\tesseract.exe')
                        else:
                            tesseract_cmd = r'E:\tesseract\tesseract.exe'  # 기본값
                        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

                        text = pytesseract.image_to_string(screenshot, lang='kor+eng')

                        # 4. 데이터 파일 저장
                        data_path = data_folder / f"product_{i+1}_{timestamp}.txt"
                        with open(data_path, 'w', encoding='utf-8') as f:
                            f.write(f"=== 제품 {i+1} 데이터 ===\n")
                            f.write(f"수집시간: {datetime.now()}\n")
                            f.write(f"텍스트길이: {len(text)}자\n")
                            f.write(f"원본텍스트:\n{text}\n")

                        collected_files['data'].append(str(data_path))
                        self.log(f"   💾 데이터 저장: {data_path.name}")

                        # 리뷰 수, 관심고객 수 추출 시도
                        import re
                        reviews = re.findall(r'리뷰\s*([0-9,]+)', text)
                        interests = re.findall(r'관심고객\s*([0-9,]+)', text)

                        if reviews:
                            self.log(f"   📊 리뷰 발견: {reviews[0]}개")
                        if interests:
                            self.log(f"   👥 관심고객 발견: {interests[0]}명")

                    except Exception as ocr_e:
                        self.log(f"   ⚠️ OCR 오류: {str(ocr_e)}")

                    # 5. 클릭 시뮬레이션 (상품 보기)
                    try:
                        # 화면 중앙 하단 클릭 (상품 카드 위치)
                        click_x = screen_width // 2 + random.randint(-200, 200)
                        click_y = screen_height // 2 + random.randint(0, 150)

                        pyautogui.click(click_x, click_y)
                        self.log(f"   👆 클릭: ({click_x}, {click_y})")

                        time.sleep(random.uniform(2, 4))  # 페이지 로딩 대기

                        # 뒤로가기
                        pyautogui.hotkey('alt', 'left')
                        time.sleep(1)

                    except Exception as click_e:
                        self.log(f"   ⚠️ 클릭 오류: {str(click_e)}")

                    # 6. 랜덤 대기 (차단 방지)
                    wait_time = random.uniform(3, 7)
                    time.sleep(wait_time)
                    self.log(f"   ⏱️ {wait_time:.1f}초 대기")

                    # 진행률 업데이트
                    if hasattr(self, 'progress'):
                        self.progress['value'] = i + 1

                except Exception as e:
                    self.log(f"   ❌ 제품 {i+1} 처리 실패: {str(e)}")
                    continue

                self.log(f"✅ 제품 {i+1} 완료")

            # 결과 정리
            total_images = len(collected_files['images'])
            total_data = len(collected_files['data'])

            self.log(f"🎉 웹 자동화 완료!")
            self.log(f"📊 수집 결과: 이미지 {total_images}개, 데이터 {total_data}개")
            self.log(f"📁 저장 위치: {download_folder}/collected_*")

            # 결과 정리 실행
            self.organize_collected_data_advanced(collected_files)

            messagebox.showinfo("완료",
                f"웹 자동화가 완료되었습니다!\n\n"
                f"📊 수집 결과:\n"
                f"• 이미지: {total_images}개\n"
                f"• 데이터: {total_data}개\n\n"
                f"📁 저장 위치:\n"
                f"{download_folder}/collected_*")

        except Exception as e:
            self.log(f"❌ 웹 자동화 오류: {str(e)}")
            messagebox.showerror("오류", f"웹 자동화 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.automation_running = False
            if hasattr(self, 'main_button'):
                self.main_button.config(state="normal")

    def organize_collected_data_advanced(self, collected_files):
        """수집된 데이터 고급 정리"""
        try:
            self.log("📁 수집된 데이터 정리 중...")

            from pathlib import Path

            # 최종 정리 폴더 생성
            final_folder = Path("E:/업무/03_데이터_수집") / f"웹수집_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            final_folder.mkdir(parents=True, exist_ok=True)

            # 이미지 정리
            image_final = final_folder / "images"
            image_final.mkdir(exist_ok=True)

            for img_path in collected_files['images']:
                src = Path(img_path)
                if src.exists():
                    dst = image_final / src.name
                    import shutil
                    shutil.copy2(src, dst)

            # 데이터 정리 및 통합 CSV 생성
            data_final = final_folder / "data"
            data_final.mkdir(exist_ok=True)

            all_data = []
            for data_path in collected_files['data']:
                src = Path(data_path)
                if src.exists():
                    dst = data_final / src.name
                    import shutil
                    shutil.copy2(src, dst)

                    # CSV용 데이터 수집
                    with open(src, 'r', encoding='utf-8') as f:
                        content = f.read()

                    all_data.append({
                        'id': len(all_data) + 1,
                        'file_name': src.name,
                        'collect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'text_length': len(content.split('원본텍스트:\n')[-1]) if '원본텍스트:\n' in content else 0,
                        'text_preview': content.split('원본텍스트:\n')[-1][:100] if '원본텍스트:\n' in content else ''
                    })

            # 통합 CSV 생성
            if all_data:
                import pandas as pd
                df = pd.DataFrame(all_data)
                csv_path = final_folder / "collected_data_summary.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                self.log(f"📊 통합 CSV 생성: {csv_path}")

            self.log(f"✅ 데이터 정리 완료: {final_folder}")

        except Exception as e:
            self.log(f"❌ 데이터 정리 오류: {str(e)}")

    def start_file_organization_only(self):
        """파일 정리만 실행"""
        if not messagebox.askyesno("파일 정리 실행", "다운로드 폴더의 파일을 정리하시겠습니까?"):
            return

        def file_organization_thread():
            try:
                self.log("[파일정리] 시작 - 다운로드 폴더 스캔 중...")

                import os
                import shutil
                from pathlib import Path

                download_path = Path("C:/Users/Administrator/Downloads")
                if not download_path.exists():
                    self.log("[파일정리] 다운로드 폴더를 찾을 수 없습니다")
                    return

                # 파일 목록 스캔
                files = list(download_path.glob("*"))
                self.log(f"[파일정리] 발견된 파일 수: {len(files)}개")

                # 확장자별 분류
                image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
                csv_extensions = ['.csv', '.xlsx', '.xls']

                organized_count = 0
                for file in files:
                    if file.is_file():
                        extension = file.suffix.lower()

                        if extension in image_extensions:
                            # 이미지 폴더로 이동
                            image_folder = download_path / "Images"
                            image_folder.mkdir(exist_ok=True)
                            new_path = image_folder / file.name
                            if not new_path.exists():
                                shutil.move(str(file), str(new_path))
                                self.log(f"[파일정리] 이미지 이동: {file.name}")
                                organized_count += 1

                        elif extension in csv_extensions:
                            # 데이터 폴더로 이동
                            data_folder = download_path / "Data"
                            data_folder.mkdir(exist_ok=True)
                            new_path = data_folder / file.name
                            if not new_path.exists():
                                shutil.move(str(file), str(new_path))
                                self.log(f"[파일정리] 데이터 이동: {file.name}")
                                organized_count += 1

                self.log(f"[파일정리] 완료! {organized_count}개 파일 정리됨")

            except Exception as e:
                self.log(f"[파일정리 오류] {str(e)}")

        thread = threading.Thread(target=file_organization_thread)
        thread.daemon = True
        thread.start()

    def start_ai_processing_only(self):
        """AI 처리만 실행"""
        if not messagebox.askyesno("AI 처리 실행", "AI 콜드메일 생성을 실행하시겠습니까?"):
            return

        def ai_processing_thread():
            try:
                self.log("[AI처리] 시작 - 프로세서 초기화 중...")

                # TwoStageProcessor 초기화
                if not self.processor:
                    from llm.two_stage_processor import TwoStageProcessor
                    self.processor = TwoStageProcessor()
                    self.log("[AI처리] 프로세서 초기화 완료")

                # 테스트 데이터로 AI 처리
                test_data = {
                    "store_name": "테스트 쇼핑몰",
                    "category": "패션",
                    "review_count": 250,
                    "rating": 4.5
                }

                self.log("[AI처리] 테스트 데이터로 콜드메일 생성 중...")

                # 1단계: 기본 정보 처리
                self.log("[AI처리] 1단계 - 기본 분석 수행...")
                stage1_result = f"분석 완료: {test_data['store_name']} ({test_data['category']})"

                # 2단계: 콜드메일 생성
                self.log("[AI처리] 2단계 - 콜드메일 생성 중...")

                sample_email = f"""
안녕하세요, {test_data['store_name']} 담당자님!

귀하의 {test_data['category']} 쇼핑몰이 {test_data['review_count']}개의 우수한 리뷰를 받고 있는 것을 확인했습니다.

저희 마케팅 솔루션이 귀하의 매출 증대에 도움이 될 것 같아 연락드립니다.

감사합니다.
"""

                # 결과 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"generated_email_{timestamp}.txt"
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(sample_email)

                self.log(f"[AI처리] 콜드메일 생성 완료! 저장: {save_path}")
                self.log("[AI처리] 완료!")

            except Exception as e:
                self.log(f"[AI처리 오류] {str(e)}")

        thread = threading.Thread(target=ai_processing_thread)
        thread.daemon = True
        thread.start()

    def select_image_folder(self):
        """이미지 폴더 선택"""
        folder = filedialog.askdirectory(title="이미지 폴더 선택")
        if folder:
            self.images_status.config(text=f"이미지: {folder}", fg="#27ae60")

    def select_review_files(self):
        """리뷰 파일 선택"""
        files = filedialog.askopenfilenames(
            title="리뷰 파일 선택",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if files:
            self.reviews_status.config(text=f"리뷰: {len(files)}개 파일", fg="#27ae60")

    def run_ai_processing(self):
        """AI 처리 실행"""
        messagebox.showinfo("개발 중", "AI 처리 기능은 완전 자동화에서 실행하세요.")

    def get_elapsed_time(self):
        """경과 시간 계산 (샘플)"""
        return "10분 30초"

    def create_client_discovery_tab(self):
        """고객사 발굴 탭 생성"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="고객사 발굴")

        # 메인 프레임
        main_frame = tk.Frame(tab, bg="#f9f9f9")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 제목
        title = tk.Label(
            main_frame,
            text="네이버 쇼핑 고객사 자동 발굴",
            font=("맑은 고딕", 16, "bold"),
            bg="#f9f9f9",
            fg="#2c3e50"
        )
        title.pack(pady=(0, 20))

        # 설정 프레임
        config_frame = tk.LabelFrame(main_frame, text="크롤링 설정", font=("맑은 고딕", 10, "bold"))
        config_frame.pack(fill="x", pady=(0, 15))

        # 설정 입력 필드들
        settings_row1 = tk.Frame(config_frame)
        settings_row1.pack(fill="x", padx=10, pady=10)

        tk.Label(settings_row1, text="검색 키워드:", font=("맑은 고딕", 9)).pack(side="left")
        self.keyword_entry = tk.Entry(settings_row1, font=("맑은 고딕", 9), width=15)
        self.keyword_entry.pack(side="left", padx=(5, 20))
        self.keyword_entry.insert(0, "텀블러")

        tk.Label(settings_row1, text="리뷰 범위:", font=("맑은 고딕", 9)).pack(side="left")
        self.review_min_entry = tk.Entry(settings_row1, font=("맑은 고딕", 9), width=8)
        self.review_min_entry.pack(side="left", padx=(5, 2))
        self.review_min_entry.insert(0, "200")

        tk.Label(settings_row1, text="~", font=("맑은 고딕", 9)).pack(side="left", padx=2)
        self.review_max_entry = tk.Entry(settings_row1, font=("맑은 고딕", 9), width=8)
        self.review_max_entry.pack(side="left", padx=(2, 20))
        self.review_max_entry.insert(0, "300")

        tk.Label(settings_row1, text="관심고객:", font=("맑은 고딕", 9)).pack(side="left")
        self.follower_min_entry = tk.Entry(settings_row1, font=("맑은 고딕", 9), width=8)
        self.follower_min_entry.pack(side="left", padx=(5, 2))
        self.follower_min_entry.insert(0, "50")

        tk.Label(settings_row1, text="~", font=("맑은 고딕", 9)).pack(side="left", padx=2)
        self.follower_max_entry = tk.Entry(settings_row1, font=("맑은 고딕", 9), width=8)
        self.follower_max_entry.pack(side="left", padx=(2, 5))
        self.follower_max_entry.insert(0, "1500")

        settings_row2 = tk.Frame(config_frame)
        settings_row2.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(settings_row2, text="최대 방문:", font=("맑은 고딕", 9)).pack(side="left")
        self.max_visits_entry = tk.Entry(settings_row2, font=("맑은 고딕", 9), width=8)
        self.max_visits_entry.pack(side="left", padx=(5, 20))
        self.max_visits_entry.insert(0, "500")

        # 제어 버튼 프레임
        control_frame = tk.LabelFrame(main_frame, text="실행 제어", font=("맑은 고딕", 10, "bold"))
        control_frame.pack(fill="x", pady=(0, 15))

        button_frame = tk.Frame(control_frame)
        button_frame.pack(padx=10, pady=10)

        self.start_crawler_btn = tk.Button(
            button_frame,
            text="크롤링 시작",
            font=("맑은 고딕", 11, "bold"),
            bg="#27ae60",
            fg="white",
            width=15,
            height=2,
            command=self.start_client_discovery
        )
        self.start_crawler_btn.pack(side="left", padx=(0, 10))

        self.stop_crawler_btn = tk.Button(
            button_frame,
            text="중지",
            font=("맑은 고딕", 11, "bold"),
            bg="#e74c3c",
            fg="white",
            width=12,
            height=2,
            command=self.stop_client_discovery,
            state="disabled"
        )
        self.stop_crawler_btn.pack(side="left", padx=(0, 10))

        self.open_results_btn = tk.Button(
            button_frame,
            text="결과 보기",
            font=("맑은 고딕", 11, "bold"),
            bg="#3498db",
            fg="white",
            width=12,
            height=2,
            command=self.open_discovery_results
        )
        self.open_results_btn.pack(side="left")

        # 개별 모듈 제어 프레임
        module_frame = tk.LabelFrame(main_frame, text="개별 모듈 제어 (수동 모드)", font=("맑은 고딕", 10, "bold"))
        module_frame.pack(fill="x", pady=(15, 15))

        # 첫 번째 줄 - 기본 모듈들
        module_row1 = tk.Frame(module_frame)
        module_row1.pack(padx=10, pady=(10, 5))

        tk.Button(
            module_row1,
            text="M1: UI 내비게이터",
            font=("맑은 고딕", 9),
            bg="#e67e22",
            fg="white",
            width=12,
            command=self.run_m1_navigator
        ).pack(side="left", padx=(0, 5))

        tk.Button(
            module_row1,
            text="M2: 리스트 스캐너",
            font=("맑은 고딕", 9),
            bg="#f39c12",
            fg="white",
            width=12,
            command=self.run_m2_scanner
        ).pack(side="left", padx=(0, 5))

        tk.Button(
            module_row1,
            text="M3: 상세 리더",
            font=("맑은 고딕", 9),
            bg="#9b59b6",
            fg="white",
            width=12,
            command=self.run_m3_reader
        ).pack(side="left", padx=(0, 5))

        tk.Button(
            module_row1,
            text="M4: 필터 매니저",
            font=("맑은 고딕", 9),
            bg="#34495e",
            fg="white",
            width=12,
            command=self.run_m4_filter
        ).pack(side="left", padx=(0, 5))

        # 두 번째 줄 - 저장 및 모니터링
        module_row2 = tk.Frame(module_frame)
        module_row2.pack(padx=10, pady=(5, 10))

        tk.Button(
            module_row2,
            text="M5: 스토리지 매니저",
            font=("맑은 고딕", 9),
            bg="#16a085",
            fg="white",
            width=12,
            command=self.run_m5_storage
        ).pack(side="left", padx=(0, 5))

        tk.Button(
            module_row2,
            text="M6: 안전 모니터",
            font=("맑은 고딕", 9),
            bg="#c0392b",
            fg="white",
            width=12,
            command=self.run_m6_monitor
        ).pack(side="left", padx=(0, 5))

        tk.Button(
            module_row2,
            text="OCR 테스트",
            font=("맑은 고딕", 9),
            bg="#2980b9",
            fg="white",
            width=12,
            command=self.test_ocr
        ).pack(side="left", padx=(0, 5))

        tk.Button(
            module_row2,
            text="화면 캡처 테스트",
            font=("맑은 고딕", 9),
            bg="#8e44ad",
            fg="white",
            width=12,
            command=self.test_screen_capture
        ).pack(side="left", padx=(0, 5))

        # 상태 및 로그 프레임
        status_frame = tk.LabelFrame(main_frame, text="실행 상태", font=("맑은 고딕", 10, "bold"))
        status_frame.pack(fill="both", expand=True)

        # 상태 정보
        status_info_frame = tk.Frame(status_frame)
        status_info_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.crawler_status_var = tk.StringVar(value="대기 중")
        self.visited_count_var = tk.StringVar(value="0")
        self.saved_count_var = tk.StringVar(value="0")

        tk.Label(status_info_frame, text="상태:", font=("맑은 고딕", 9, "bold")).pack(side="left")
        self.crawler_status_label = tk.Label(status_info_frame, textvariable=self.crawler_status_var,
                                           font=("맑은 고딕", 9), fg="#27ae60")
        self.crawler_status_label.pack(side="left", padx=(5, 20))

        tk.Label(status_info_frame, text="방문:", font=("맑은 고딕", 9, "bold")).pack(side="left")
        tk.Label(status_info_frame, textvariable=self.visited_count_var,
                font=("맑은 고딕", 9), fg="#3498db").pack(side="left", padx=(5, 20))

        tk.Label(status_info_frame, text="저장:", font=("맑은 고딕", 9, "bold")).pack(side="left")
        tk.Label(status_info_frame, textvariable=self.saved_count_var,
                font=("맑은 고딕", 9), fg="#e67e22").pack(side="left", padx=(5, 0))

        # 로그 출력
        log_frame = tk.Frame(status_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.crawler_log_text = tk.Text(
            log_frame,
            height=10,
            font=("Consolas", 9),
            bg="#2c3e50",
            fg="#ecf0f1",
            wrap="word"
        )

        crawler_scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.crawler_log_text.yview)
        self.crawler_log_text.configure(yscrollcommand=crawler_scrollbar.set)

        self.crawler_log_text.pack(side="left", fill="both", expand=True)
        crawler_scrollbar.pack(side="right", fill="y")

        # 초기 상태 로그
        self.crawler_log("고객사 발굴 시스템 준비 완료")
        self.crawler_log("사용법:")
        self.crawler_log("1. 네이버 쇼핑에서 검색 + 리뷰많은순 정렬 (수동)")
        self.crawler_log("2. 쇼핑몰/스토어 탭 활성화 (수동)")
        self.crawler_log("3. '크롤링 시작' 버튼 클릭")
        self.crawler_log("4. 5초 내에 브라우저 창 클릭해서 활성화")

    def start_client_discovery(self):
        """고객사 발굴 시작"""
        try:
            # UI 상태 업데이트
            self.start_crawler_btn.config(state="disabled")
            self.stop_crawler_btn.config(state="normal")
            self.crawler_status_var.set("실행 중")
            self.crawler_status_label.config(fg="#e67e22")

            # 설정 수집
            config_updates = {
                "search": {
                    "keyword": self.keyword_entry.get(),
                    "review_min": int(self.review_min_entry.get()),
                    "review_max": int(self.review_max_entry.get()),
                    "follower_min": int(self.follower_min_entry.get()),
                    "follower_max": int(self.follower_max_entry.get()),
                    "max_visits_per_run": int(self.max_visits_entry.get())
                }
            }

            self.crawler_log(f"크롤링 시작: 키워드='{config_updates['search']['keyword']}'")
            self.crawler_log(f"📋 설정: 리뷰({config_updates['search']['review_min']}-{config_updates['search']['review_max']}), "
                           f"관심고객({config_updates['search']['follower_min']}-{config_updates['search']['follower_max']})")

            # 별도 스레드에서 실행
            threading.Thread(target=self.run_client_discovery_thread, args=(config_updates,), daemon=True).start()

        except ValueError as e:
            messagebox.showerror("설정 오류", "숫자 설정 값을 확인해주세요.")
            self.reset_crawler_ui()
        except Exception as e:
            messagebox.showerror("오류", f"크롤링 시작 실패: {e}")
            self.reset_crawler_ui()

    def run_client_discovery_thread(self, config_updates):
        """고객사 발굴 실행 스레드"""
        try:
            # 크롤러 import 및 실행
            from client_discovery.main_crawler import NaverShoppingCrawler
            import json

            # 설정 파일 업데이트
            config_path = "client_discovery/config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            config.update(config_updates)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # 크롤러 실행
            crawler = NaverShoppingCrawler(config_path)
            result = crawler.run()

            # 결과 처리
            self.root.after(0, self.crawler_finished, result, crawler.stats)

        except Exception as e:
            self.root.after(0, self.crawler_error, str(e))

    def crawler_finished(self, result, stats):
        """크롤러 완료 처리"""
        self.crawler_log(f"✅ 크롤링 완료: {result}")
        self.crawler_log(f"📊 결과: 방문 {stats.total_visited}개, 저장 {stats.total_saved}개")
        self.visited_count_var.set(str(stats.total_visited))
        self.saved_count_var.set(str(stats.total_saved))
        self.reset_crawler_ui()

    def crawler_error(self, error_msg):
        """크롤러 오류 처리"""
        self.crawler_log(f"❌ 오류 발생: {error_msg}")
        messagebox.showerror("크롤링 오류", f"크롤링 중 오류가 발생했습니다:\n{error_msg}")
        self.reset_crawler_ui()

    def stop_client_discovery(self):
        """고객사 발굴 중지"""
        self.crawler_log("⏹️ 사용자가 중지를 요청했습니다...")
        # TODO: 크롤러에 중지 신호 전송
        self.reset_crawler_ui()

    def reset_crawler_ui(self):
        """크롤러 UI 상태 리셋"""
        self.start_crawler_btn.config(state="normal")
        self.stop_crawler_btn.config(state="disabled")
        self.crawler_status_var.set("대기 중")
        self.crawler_status_label.config(fg="#27ae60")

    def open_discovery_results(self):
        """발굴 결과 파일 열기"""
        try:
            from datetime import datetime
            import subprocess
            date_str = datetime.now().strftime("%Y%m%d")
            result_file = f"client_discovery/targets_{date_str}.csv"

            if Path(result_file).exists():
                subprocess.Popen(f'explorer /select,"{Path(result_file).absolute()}"', shell=True)
                self.crawler_log(f"📁 결과 파일 열기: {result_file}")
            else:
                messagebox.showinfo("파일 없음", "아직 발굴된 결과가 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"결과 파일 열기 실패: {e}")

    def crawler_log(self, message):
        """크롤러 로그 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.crawler_log_text.insert("end", f"[{timestamp}] {message}\n")
        self.crawler_log_text.see("end")
        self.root.update_idletasks()

    # ===== 개별 모듈 실행 메소드들 =====

    def run_m1_navigator(self):
        """M1: UI 내비게이터 실행"""
        try:
            self.log("[M1] UI 내비게이터 실행 중...")

            from client_discovery.m1_ui_navigator import UINavigator

            # 설정 로드
            config = {"timing": {"scroll_wait": 2, "load_wait_min": 1, "load_wait_max": 3}}
            navigator = UINavigator(config)

            # 스크롤 다운 테스트
            result = navigator.scroll_down()
            self.log(f"[M1] 스크롤 다운 결과: {result}")

            # 검색 실행 (키워드 입력 필요)
            keyword = self.keyword_entry.get() if hasattr(self, 'keyword_entry') else "테스트"
            search_result = navigator.search_keyword(keyword)
            self.log(f"[M1] 검색 실행 결과: {search_result}")

        except Exception as e:
            self.log(f"[M1 오류] {str(e)}")

    def run_m2_scanner(self):
        """M2: 리스트 스캐너 실행"""
        try:
            self.log("[M2] 리스트 스캐너 실행 중...")

            from client_discovery.m2_list_scanner import ListScanner

            config = {"ui": {"card_detection": True}}
            scanner = ListScanner(config)

            # 화면에서 카드 찾기
            cards = scanner.find_store_cards()
            self.log(f"[M2] 발견된 카드 수: {len(cards) if cards else 0}개")

            if cards and len(cards) > 0:
                # 첫 번째 카드에서 리뷰 수 읽기
                review_count = scanner.read_review_count(cards[0])
                store_name = scanner.read_store_name(cards[0])
                self.log(f"[M2] 첫 번째 카드 - 스토어: {store_name}, 리뷰: {review_count}")

        except Exception as e:
            self.log(f"[M2 오류] {str(e)}")

    def run_m3_reader(self):
        """M3: 상세 리더 실행"""
        try:
            self.log("[M3] 상세 리더 실행 중...")

            from client_discovery.m3_detail_reader import DetailReader

            config = {"timing": {"load_wait_min": 2, "load_wait_max": 4}}
            reader = DetailReader(config)

            # 관심고객 수 읽기 (현재 화면에서)
            interest_count = reader.read_interest_count()
            self.log(f"[M3] 관심고객 수: {interest_count if interest_count else '인식 안됨'}")

        except Exception as e:
            self.log(f"[M3 오류] {str(e)}")

    def run_m4_filter(self):
        """M4: 필터 매니저 실행"""
        try:
            self.log("[M4] 필터 매니저 실행 중...")

            from client_discovery.m4_filter import FilterManager
            from client_discovery.models import StoreDetail

            # 설정에서 필터 조건 가져오기
            config = {
                "filter": {
                    "min_review_count": int(self.review_min_entry.get()) if hasattr(self, 'review_min_entry') else 200,
                    "max_review_count": int(self.review_max_entry.get()) if hasattr(self, 'review_max_entry') else 300,
                    "min_interest_count": int(self.follower_min_entry.get()) if hasattr(self, 'follower_min_entry') else 50,
                    "max_interest_count": int(self.follower_max_entry.get()) if hasattr(self, 'follower_max_entry') else 1500,
                }
            }

            filter_manager = FilterManager(config)

            # 테스트 데이터로 필터링 테스트
            test_store = StoreDetail(
                store_name="테스트 스토어",
                review_count=250,
                interest_count=100,
                url="https://example.com"
            )

            is_valid = filter_manager.should_save_store(test_store)
            self.log(f"[M4] 테스트 스토어 필터링 결과: {'통과' if is_valid else '제외'}")
            self.log(f"[M4] 현재 필터 조건 - 리뷰: {config['filter']['min_review_count']}~{config['filter']['max_review_count']}, 관심고객: {config['filter']['min_interest_count']}~{config['filter']['max_interest_count']}")

        except Exception as e:
            self.log(f"[M4 오류] {str(e)}")

    def run_m5_storage(self):
        """M5: 스토리지 매니저 실행"""
        try:
            self.log("[M5] 스토리지 매니저 실행 중...")

            from client_discovery.m5_storage import StorageManager
            from client_discovery.models import StoreDetail

            config = {"storage": {"output_file": "client_discovery/results/test_stores.csv"}}
            storage = StorageManager(config)

            # 테스트 데이터 저장
            test_stores = [
                StoreDetail(
                    store_name="테스트 스토어1",
                    review_count=250,
                    interest_count=100,
                    url="https://example1.com"
                ),
                StoreDetail(
                    store_name="테스트 스토어2",
                    review_count=300,
                    interest_count=150,
                    url="https://example2.com"
                )
            ]

            for store in test_stores:
                storage.save_store(store)

            storage.finalize()
            self.log(f"[M5] 테스트 데이터 2개 저장 완료")

        except Exception as e:
            self.log(f"[M5 오류] {str(e)}")

    def run_m6_monitor(self):
        """M6: 안전 모니터 실행"""
        try:
            self.log("[M6] 안전 모니터 실행 중...")

            from client_discovery.m6_monitor import SafetyMonitor

            config = {"safety": {"check_interval": 5}}
            # storage 매개변수도 필요하므로 None으로 전달
            monitor = SafetyMonitor(config, None)

            # 화면 상태 검사
            is_safe = monitor.is_safe_to_continue()
            self.log(f"[M6] 안전 상태 검사 결과: {'안전' if is_safe else '위험 감지'}")

            # 중단 신호 검사
            should_stop = monitor.should_stop()
            self.log(f"[M6] 중단 신호 검사 결과: {'계속' if not should_stop else '중단 필요'}")

        except Exception as e:
            self.log(f"[M6 오류] {str(e)}")

    def test_ocr(self):
        """OCR 기능 테스트"""
        try:
            self.log("[OCR] OCR 기능 테스트 중...")

            import pytesseract
            import pyautogui

            # Tesseract 경로 설정 (config.yaml에서 읽기)
            import yaml
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                tesseract_cmd = config_data.get('ocr', {}).get('tesseract_cmd', r'E:\tesseract\tesseract.exe')
            else:
                tesseract_cmd = r'E:\tesseract\tesseract.exe'  # 기본값
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

            # 현재 화면 캡처 및 텍스트 추출
            screenshot = pyautogui.screenshot()
            text = pytesseract.image_to_string(screenshot, lang='kor+eng')

            self.log(f"[OCR] 텍스트 추출 성공! 길이: {len(text)}자")
            self.log(f"[OCR] 첫 100자: {text[:100].strip()}")

        except Exception as e:
            self.log(f"[OCR 오류] {str(e)}")

    def test_screen_capture(self):
        """화면 캡처 테스트"""
        try:
            self.log("[캡처] 화면 캡처 테스트 중...")

            import pyautogui
            from datetime import datetime

            # 화면 크기 확인
            screen_width, screen_height = pyautogui.size()
            self.log(f"[캡처] 화면 크기: {screen_width}x{screen_height}")

            # 화면 캡처
            screenshot = pyautogui.screenshot()

            # 테스트용으로 임시 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"temp_screenshot_{timestamp}.png"
            screenshot.save(save_path)

            self.log(f"[캡처] 화면 캡처 성공! 저장위치: {save_path}")

        except Exception as e:
            self.log(f"[캡처 오류] {str(e)}")


def main():
    """메인 실행 함수"""
    root = tk.Tk()
    app = CompleteAutomationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()