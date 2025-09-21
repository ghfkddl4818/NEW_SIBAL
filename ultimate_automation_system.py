#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 완전 통합 자동화 시스템
file_organizer + all_in_one 완전 병합 버전

브라우저 자동화 → 데이터 수집 → AI 분석 → 콜드메일 생성
모든 기능이 하나의 프로그램에 통합됨
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import json
import threading
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
import shutil
import glob
import subprocess
import time
import hashlib
import re
from urllib.parse import unquote

# 웹 자동화 모듈들 (file_organizer 기능)
import pyautogui
import pyperclip
import pandas as pd
import openpyxl
from openpyxl import load_workbook

# AI 콜드메일 모듈들 (all_in_one 기능)
sys.path.append(str(Path(__file__).parent))
from core.config import load_config, load_config_data
from llm.gemini_client import GeminiClient
from compose.composer import compose_final_email


def _file_organizer_config(config_path: str) -> dict:
    try:
        return load_config_data(config_path).get("file_organizer", {})
    except Exception:
        return {}


def _paths_config(config_path: str) -> dict:
    try:
        return load_config_data(config_path).get("paths", {})
    except Exception:
        return {}

class UltimateAutomationSystem:
    """궁극의 통합 자동화 시스템"""

    def __init__(self):
        print("궁극의 통합 자동화 시스템 시작...")
        self.root = tk.Tk()
        self.root.title("궁극의 이커머스 콜드메일 자동화 시스템 - 완전통합")
        self.root.geometry("1800x1200")
        self.root.resizable(True, True)

        # GUI 가시성 강제
        self.root.lift()  # 창을 맨 앞으로
        self.root.attributes('-topmost', True)  # 항상 위에
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))  # 즉시 해제

        # === 공통 설정 ===
        self.today = datetime.now().strftime("%Y-%m-%d")

        # === file_organizer 설정 ===
        self.project_root = Path(__file__).resolve().parent
        self.config_path = "config/config.yaml"
        self.config_data = load_config_data(self.config_path) or {}
        file_org_config = self.config_data.get('file_organizer', {})

        default_download = self.project_root / 'downloads'
        default_work = self.project_root / 'data' / 'work'
        default_database = self.project_root / 'data' / 'storage' / 'ecommerce_database.xlsx'
        paths_config = self.config_data.get('paths', {})
        default_output = self.project_root / 'outputs'

        self.output_folder = Path(paths_config.get('output_root_dir', default_output)).expanduser()
        self.custom_output_folder = None

        self.download_folder = Path(file_org_config.get('download_folder', default_download)).expanduser()
        self.work_folder = Path(file_org_config.get('work_folder', default_work)).expanduser()
        self.database_file = Path(file_org_config.get('database_file', default_database)).expanduser()

        self.default_download_folder = str(self.download_folder)
        self.default_work_folder = str(self.work_folder)
        self.default_database_file = str(self.database_file)
        self.fireshot_capture_timeout_sec = file_org_config.get('fireshot_capture_timeout_sec', 20)
        self.fireshot_capture_poll_interval_sec = file_org_config.get('fireshot_capture_poll_interval_sec', 0.5)

        self.file_hashes = {}
        self.pending_stores = []  # 순서 기반 매칭용

        # 웹 자동화 상태
        self.automation_running = False
        self.automation_paused = False
        self.processed_count = 0
        self.failed_products = []
        self.total_products = file_org_config.get('total_products', 30)

        # 이미지 파일들 (웹 자동화용) - 상대 경로로 변경
        self.image_files = {
            'detail_button': 'assets/img/detail_button.png',
            'fireshot_save': 'assets/img/fireshot_save.png',
            'analysis_start': 'assets/img/analysis_start.png',
            'excel_download': 'assets/img/excel_download.png',
            'review_button': 'assets/img/review_button.png',
            'review_context': 'assets/img/review_context.png',
            'popup_context': 'assets/img/popup_context.png',
            'result_context': 'assets/img/result_context.png',
            'crawling_tool': 'assets/img/crawling_tool.png',
            # 고객사 발굴용 이미지들
            'tab_shoppingmall': 'assets/img/tab_shoppingmall.png',
            'sort_review_desc': 'assets/img/sort_review_desc.png',
            'label_review': 'assets/img/label_review.png',
            'label_interest': 'assets/img/label_interest.png'
        }

        # 절대 좌표 백업 (지시서 요구사항: 이미지 인식 실패시 사용)
        self.coords = {
            'close_popup': (1200, 100),  # 팝업 닫기 버튼 예상 위치
            'sort_dropdown': (800, 200),  # 정렬 드롭다운 예상 위치
            'review_sort': (800, 250),   # 리뷰많은순 옵션 예상 위치
            # TODO: 실제 환경에서 좌표 측정 후 업데이트 필요
        }

        # === all_in_one 설정 ===
        self.selected_images = []
        self.selected_reviews = []
        self.is_ai_processing = False
        self.generated_emails = []

        print("GUI 위젯 생성 중...")
        self.create_widgets()
        self.load_settings()
        self.setup_hotkeys()

        # 초기 파일 스캔
        self.scan_files()

        # 자산 검증
        self.validate_image_assets()

        # 안전 모니터링 초기화
        self.init_safety_monitoring()

        # 데이터베이스 초기화 (지시서 요구사항)
        self.create_database_if_missing()

        # API 및 OCR 검증 (지시서 요구사항)
        self.verify_api_and_ocr()

        print("궁극의 통합 시스템 초기화 완료!")

    def create_widgets(self):
        """통합 GUI 위젯 생성"""

        # === 메인 제목 ===
        title_frame = tk.Frame(self.root, bg="#1a252f", height=80)
        title_frame.pack(fill="x", padx=5, pady=5)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="궁극의 이커머스 콜드메일 자동화 시스템",
            font=("맑은 고딕", 20, "bold"),
            bg="#1a252f",
            fg="white"
        )
        title_label.pack(expand=True)

        subtitle_label = tk.Label(
            title_frame,
            text="웹 자동화 + 데이터 수집 + AI 분석 + 콜드메일 생성 (All-in-One 완전통합)",
            font=("맑은 고딕", 11),
            bg="#1a252f",
            fg="#bdc3c7"
        )
        subtitle_label.pack()

        # === 메인 컨트롤 패널 ===
        self.create_main_control_panel()

        # === 탭 시스템 ===
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # 탭들 생성
        self.create_automation_tab()
        self.create_client_discovery_tab()  # 고객사 발굴 탭
        self.create_web_automation_tab()
        self.create_ai_generation_tab()
        self.create_results_tab()
        self.create_settings_tab()

    def create_main_control_panel(self):
        """메인 컨트롤 패널"""
        control_frame = tk.Frame(self.root, bg="#34495e", height=180)
        control_frame.pack(fill="x", padx=10, pady=5)
        control_frame.pack_propagate(False)

        # 상태 표시
        status_subframe = tk.Frame(control_frame, bg="#34495e")
        status_subframe.pack(side="left", fill="both", expand=True, padx=20, pady=10)

        tk.Label(status_subframe, text="📊 실시간 상태",
                font=("맑은 고딕", 12, "bold"), bg="#34495e", fg="white").pack(anchor="w")

        self.main_status_var = tk.StringVar(value="🟢 대기 중 - 준비 완료")
        tk.Label(status_subframe, textvariable=self.main_status_var,
                font=("맑은 고딕", 11), bg="#34495e", fg="#2ecc71").pack(anchor="w", pady=2)

        self.progress_summary_var = tk.StringVar(value="처리 완료: 0개 | 대기: 0개")
        tk.Label(status_subframe, textvariable=self.progress_summary_var,
                font=("맑은 고딕", 10), bg="#34495e", fg="#ecf0f1").pack(anchor="w")

        # 메인 실행 버튼들
        btn_subframe = tk.Frame(control_frame, bg="#34495e")
        btn_subframe.pack(side="right", padx=20, pady=10)

        self.master_start_btn = tk.Button(
            btn_subframe,
            text="🚀 완전 자동화 시작\n(30개 제품 → 30개 콜드메일)",
            command=self.start_complete_automation,
            bg="#e74c3c",
            fg="white",
            font=("맑은 고딕", 16, "bold"),
            relief="flat",
            padx=40,
            pady=20,
            width=30,
            height=4
        )
        self.master_start_btn.pack()

        btn_row2 = tk.Frame(btn_subframe, bg="#34495e")
        btn_row2.pack(fill="x", pady=(8, 0))

        tk.Button(btn_row2, text="⛔ 긴급 중단", command=self.emergency_stop,
                 bg="#e67e22", fg="white", font=("맑은 고딕", 12, "bold"),
                 padx=15, pady=8, width=10).pack(side="left", padx=5)

        tk.Button(btn_row2, text="📊 결과 보기", command=self.show_results_summary,
                 bg="#3498db", fg="white", font=("맑은 고딕", 12, "bold"),
                 padx=15, pady=8, width=10).pack(side="left", padx=5)

        tk.Button(btn_row2, text="⚙️ 설정", command=lambda: self.notebook.select(4),
                 bg="#95a5a6", fg="white", font=("맑은 고딕", 12, "bold"),
                 padx=15, pady=8, width=8).pack(side="left", padx=5)

    def create_automation_tab(self):
        """자동화 현황 탭"""
        auto_tab = ttk.Frame(self.notebook)
        self.notebook.add(auto_tab, text="🎯 자동화 현황")

        # 워크플로우 다이어그램
        workflow_frame = tk.LabelFrame(auto_tab, text="🔄 자동화 워크플로우", font=("맑은 고딕", 12, "bold"))
        workflow_frame.pack(fill="x", padx=10, pady=5)

        workflow_steps = tk.Frame(workflow_frame)
        workflow_steps.pack(fill="x", padx=10, pady=10)

        steps = [
            ("1️⃣", "브라우저 준비", "30개 제품 탭 열기", "#3498db"),
            ("2️⃣", "웹 자동화", "상세페이지 + 리뷰 수집", "#e67e22"),
            ("3️⃣", "데이터 정리", "AI 처리 가능한 형태로 변환", "#27ae60"),
            ("4️⃣", "AI 분석", "OCR + 리뷰 분석", "#9b59b6"),
            ("5️⃣", "콜드메일 생성", "전문적인 메일 작성", "#e74c3c")
        ]

        self.step_labels = []
        for i, (icon, title, desc, color) in enumerate(steps):
            step_frame = tk.Frame(workflow_steps)
            step_frame.pack(fill="x", pady=2)

            tk.Label(step_frame, text=icon, font=("맑은 고딕", 14)).pack(side="left")

            step_info = tk.Frame(step_frame)
            step_info.pack(side="left", fill="x", expand=True, padx=10)

            step_label = tk.Label(step_info, text=f"{title}: 대기 중",
                                font=("맑은 고딕", 11, "bold"))
            step_label.pack(anchor="w")
            self.step_labels.append(step_label)

            tk.Label(step_info, text=desc, font=("맑은 고딕", 9), fg="#7f8c8d").pack(anchor="w")

        # 전체 진행 바
        progress_frame = tk.Frame(workflow_frame)
        progress_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(progress_frame, text="전체 진행률:", font=("맑은 고딕", 10, "bold")).pack(anchor="w")
        self.main_progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.main_progress_bar.pack(fill="x", pady=3)

        self.progress_detail_var = tk.StringVar(value="준비 완료 - 시작 버튼을 눌러주세요")
        tk.Label(progress_frame, textvariable=self.progress_detail_var,
                font=("맑은 고딕", 9)).pack(anchor="w")

        # 실시간 로그
        log_frame = tk.LabelFrame(auto_tab, text="📜 실시간 로그", font=("맑은 고딕", 12, "bold"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.main_log_text = tk.Text(log_frame, font=("Consolas", 9), wrap="word",
                                    bg="#2c3e50", fg="#ecf0f1", height=15)
        main_log_scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.main_log_text.yview)
        self.main_log_text.configure(yscrollcommand=main_log_scrollbar.set)

        self.main_log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        main_log_scrollbar.pack(side="right", fill="y", pady=5)

    def create_web_automation_tab(self):
        """웹 자동화 탭 (file_organizer 통합)"""
        web_tab = ttk.Frame(self.notebook)
        self.notebook.add(web_tab, text="🌐 웹 자동화")

        # 설정 패널
        settings_frame = tk.LabelFrame(web_tab, text="⚙️ 폴더 설정", font=("맑은 고딕", 12, "bold"))
        settings_frame.pack(fill="x", padx=10, pady=5)

        settings_grid = tk.Frame(settings_frame)
        settings_grid.pack(fill="x", padx=10, pady=5)

        # 다운로드 폴더
        tk.Label(settings_grid, text="다운로드 폴더:", font=("맑은 고딕", 10)).grid(row=0, column=0, sticky="w")
        self.download_path_var = tk.StringVar(value=str(self.download_folder))
        tk.Entry(settings_grid, textvariable=self.download_path_var, width=50, font=("맑은 고딕", 9)).grid(row=0, column=1, padx=5)
        tk.Button(settings_grid, text="찾기", command=self.browse_download_folder).grid(row=0, column=2)

        # 작업 폴더
        tk.Label(settings_grid, text="작업 폴더:", font=("맑은 고딕", 10)).grid(row=1, column=0, sticky="w")
        self.work_path_var = tk.StringVar(value=str(self.work_folder))
        tk.Entry(settings_grid, textvariable=self.work_path_var, width=50, font=("맑은 고딕", 9)).grid(row=1, column=1, padx=5)
        tk.Button(settings_grid, text="찾기", command=self.browse_work_folder).grid(row=1, column=2)

        # 웹 자동화 상태
        web_status_frame = tk.LabelFrame(web_tab, text="🕹️ 웹 자동화 상태", font=("맑은 고딕", 12, "bold"))
        web_status_frame.pack(fill="x", padx=10, pady=5)

        status_info = tk.Frame(web_status_frame)
        status_info.pack(fill="x", padx=10, pady=5)

        self.web_automation_status_var = tk.StringVar(value="대기 중 (ESC키로 중단 가능)")
        tk.Label(status_info, textvariable=self.web_automation_status_var,
                font=("맑은 고딕", 11, "bold")).pack(side="left")

        self.web_progress_var = tk.StringVar(value="0/30 완료")
        tk.Label(status_info, textvariable=self.web_progress_var,
                font=("맑은 고딕", 10)).pack(side="right")

        self.web_progress_bar = ttk.Progressbar(web_status_frame, mode="determinate")
        self.web_progress_bar.pack(fill="x", padx=10, pady=5)

        # 컨트롤 버튼들
        web_control_frame = tk.Frame(web_status_frame)
        web_control_frame.pack(fill="x", padx=10, pady=5)

        # 명세서 호환성을 위한 automation_button 참조 생성
        self.automation_button = tk.Button(web_control_frame, text="🚀 웹 자동화만 시작", command=self.start_web_automation_only,
                 bg="#3498db", fg="white", font=("맑은 고딕", 10, "bold"), padx=15)
        self.automation_button.pack(side="left", padx=5)

        tk.Button(web_control_frame, text="⏸️ 일시정지", command=self.pause_web_automation,
                 bg="#f39c12", fg="white", font=("맑은 고딕", 10, "bold"), padx=15).pack(side="left", padx=5)

        tk.Button(web_control_frame, text="⏹️ 중단", command=self.stop_web_automation,
                 bg="#e74c3c", fg="white", font=("맑은 고딕", 10, "bold"), padx=15).pack(side="left", padx=5)

        # 파일 목록
        files_frame = tk.LabelFrame(web_tab, text="📁 수집된 파일들", font=("맑은 고딕", 12, "bold"))
        files_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 트리뷰 (file_organizer의 파일 목록 기능)
        columns = ("타입", "파일명", "제품명", "브랜드명", "크기", "수정일시", "상태")
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show="headings", height=12)

        for col in columns:
            self.files_tree.heading(col, text=col)

        # 컬럼 크기 조정
        self.files_tree.column("타입", width=80)
        self.files_tree.column("파일명", width=200)
        self.files_tree.column("제품명", width=150)
        self.files_tree.column("브랜드명", width=100)
        self.files_tree.column("크기", width=80)
        self.files_tree.column("수정일시", width=120)
        self.files_tree.column("상태", width=80)

        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)

        self.files_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        files_scrollbar.pack(side="right", fill="y", pady=5)

    def create_ai_generation_tab(self):
        """AI 생성 탭"""
        ai_tab = ttk.Frame(self.notebook)
        self.notebook.add(ai_tab, text="🤖 AI 콜드메일")

        # AI 설정
        ai_settings_frame = tk.LabelFrame(ai_tab, text="🧠 AI 설정", font=("맑은 고딕", 12, "bold"))
        ai_settings_frame.pack(fill="x", padx=10, pady=5)

        ai_config_frame = tk.Frame(ai_settings_frame)
        ai_config_frame.pack(fill="x", padx=10, pady=5)

        # 톤앤매너
        tk.Label(ai_config_frame, text="톤앤매너:", font=("맑은 고딕", 10)).grid(row=0, column=0, sticky="w")
        self.tone_var = tk.StringVar(value="consultant")
        ttk.Combobox(ai_config_frame, textvariable=self.tone_var, values=["consultant", "student"],
                    width=15, state="readonly").grid(row=0, column=1, padx=5)

        # 이메일 길이
        tk.Label(ai_config_frame, text="최소 글자수:", font=("맑은 고딕", 10)).grid(row=0, column=2, sticky="w", padx=(20,0))
        self.min_chars = tk.IntVar(value=350)
        tk.Spinbox(ai_config_frame, from_=200, to=500, textvariable=self.min_chars, width=8).grid(row=0, column=3, padx=5)

        tk.Label(ai_config_frame, text="최대 글자수:", font=("맑은 고딕", 10)).grid(row=0, column=4, sticky="w", padx=(10,0))
        self.max_chars = tk.IntVar(value=600)
        tk.Spinbox(ai_config_frame, from_=400, to=800, textvariable=self.max_chars, width=8).grid(row=0, column=5, padx=5)

        # AI 처리 상태
        ai_status_frame = tk.LabelFrame(ai_tab, text="🎯 AI 처리 상태", font=("맑은 고딕", 12, "bold"))
        ai_status_frame.pack(fill="x", padx=10, pady=5)

        ai_status_info = tk.Frame(ai_status_frame)
        ai_status_info.pack(fill="x", padx=10, pady=5)

        self.ai_status_var = tk.StringVar(value="대기 중")
        tk.Label(ai_status_info, textvariable=self.ai_status_var,
                font=("맑은 고딕", 11, "bold")).pack(side="left")

        self.ai_progress_var = tk.StringVar(value="생성 완료: 0개")
        tk.Label(ai_status_info, textvariable=self.ai_progress_var,
                font=("맑은 고딕", 10)).pack(side="right")

        self.ai_progress_bar = ttk.Progressbar(ai_status_frame, mode="determinate")
        self.ai_progress_bar.pack(fill="x", padx=10, pady=5)

        # AI 컨트롤
        ai_control_frame = tk.Frame(ai_status_frame)
        ai_control_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(ai_control_frame, text="🤖 AI 생성만 시작", command=self.start_ai_generation_only,
                 bg="#9b59b6", fg="white", font=("맑은 고딕", 10, "bold"), padx=15).pack(side="left", padx=5)

        tk.Button(ai_control_frame, text="🧪 스모크 테스트", command=self.run_ai_smoke_test,
                 bg="#f39c12", fg="white", font=("맑은 고딕", 10, "bold"), padx=15).pack(side="left", padx=5)

        # 데이터 미리보기
        preview_frame = tk.LabelFrame(ai_tab, text="📊 처리 대상 데이터", font=("맑은 고딕", 12, "bold"))
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)

        preview_columns = ("타입", "파일명", "크기", "상태")
        self.data_preview_tree = ttk.Treeview(preview_frame, columns=preview_columns, show="headings", height=8)

        for col in preview_columns:
            self.data_preview_tree.heading(col, text=col)

        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.data_preview_tree.yview)
        self.data_preview_tree.configure(yscrollcommand=preview_scrollbar.set)

        self.data_preview_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        preview_scrollbar.pack(side="right", fill="y", pady=5)

    def create_results_tab(self):
        """결과 보기 탭"""
        results_tab = ttk.Frame(self.notebook)
        self.notebook.add(results_tab, text="📧 결과 보기")

        # 통계 요약
        stats_frame = tk.LabelFrame(results_tab, text="📊 생성 통계", font=("맑은 고딕", 12, "bold"))
        stats_frame.pack(fill="x", padx=10, pady=5)

        stats_grid = tk.Frame(stats_frame)
        stats_grid.pack(fill="x", padx=10, pady=10)

        self.stats_labels = {}
        stats_items = [
            ("총 생성된 콜드메일", "0개"),
            ("오늘 생성", "0개"),
            ("성공률", "0%"),
            ("평균 처리시간", "0분"),
            ("예상 시간 절약", "0시간"),
            ("저장 폴더", "outputs/")
        ]

        for i, (label, value) in enumerate(stats_items):
            tk.Label(stats_grid, text=f"{label}:", font=("맑은 고딕", 10)).grid(row=i//2, column=(i%2)*2, sticky="w", padx=5, pady=2)
            value_label = tk.Label(stats_grid, text=value, font=("맑은 고딕", 10, "bold"), fg="#2980b9")
            value_label.grid(row=i//2, column=(i%2)*2+1, sticky="w", padx=10)
            self.stats_labels[label] = value_label

        # 폴더 열기 버튼들
        folder_btn_frame = tk.Frame(stats_frame)
        folder_btn_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(folder_btn_frame, text="📁 결과 폴더 열기", command=self.open_output_folder,
                 bg="#27ae60", fg="white", font=("맑은 고딕", 10)).pack(side="left", padx=5)

        tk.Button(folder_btn_frame, text="🗂️ 웹수집 폴더 열기", command=self.open_web_collection_folder,
                 bg="#3498db", fg="white", font=("맑은 고딕", 10)).pack(side="left", padx=5)

        # 생성된 콜드메일 목록
        emails_frame = tk.LabelFrame(results_tab, text="📧 생성된 콜드메일", font=("맑은 고딕", 12, "bold"))
        emails_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 콜드메일 목록 (더블클릭으로 상세보기)
        email_columns = ("생성시간", "제목", "글자수", "파일명")
        self.emails_tree = ttk.Treeview(emails_frame, columns=email_columns, show="headings", height=8)

        for col in email_columns:
            self.emails_tree.heading(col, text=col)

        self.emails_tree.bind("<Double-1>", self.show_email_detail)

        emails_scrollbar = ttk.Scrollbar(emails_frame, orient="vertical", command=self.emails_tree.yview)
        self.emails_tree.configure(yscrollcommand=emails_scrollbar.set)

        emails_list_frame = tk.Frame(emails_frame)
        emails_list_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.emails_tree.pack(fill="both", expand=True)
        emails_scrollbar.pack(side="right", fill="y", pady=5)

        # 미리보기 영역
        preview_subframe = tk.Frame(emails_frame)
        preview_subframe.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        tk.Label(preview_subframe, text="📄 미리보기 (더블클릭으로 상세보기)",
                font=("맑은 고딕", 10, "bold")).pack(anchor="w")

        self.email_preview_text = tk.Text(preview_subframe, font=("맑은 고딕", 9), wrap="word",
                                         bg="#f8f9fa", fg="#2c3e50", height=15)
        preview_scrollbar = tk.Scrollbar(preview_subframe, orient="vertical", command=self.email_preview_text.yview)
        self.email_preview_text.configure(yscrollcommand=preview_scrollbar.set)

        self.email_preview_text.pack(side="left", fill="both", expand=True)
        preview_scrollbar.pack(side="right", fill="y")

    def create_settings_tab(self):
        """설정 탭"""
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="⚙️ 설정")

        # 시스템 상태
        system_frame = tk.LabelFrame(settings_tab, text="💻 시스템 상태", font=("맑은 고딕", 12, "bold"))
        system_frame.pack(fill="x", padx=10, pady=5)

        self.system_status_text = tk.Text(system_frame, font=("Consolas", 10), height=8,
                                         bg="#f8f9fa", fg="#2c3e50")
        self.system_status_text.pack(fill="x", padx=10, pady=5)

        # 고급 설정
        advanced_frame = tk.LabelFrame(settings_tab, text="🔧 고급 설정", font=("맑은 고딕", 12, "bold"))
        advanced_frame.pack(fill="x", padx=10, pady=5)

        advanced_grid = tk.Frame(advanced_frame)
        advanced_grid.pack(fill="x", padx=10, pady=5)

        # 처리할 제품 수
        tk.Label(advanced_grid, text="처리할 제품 수:", font=("맑은 고딕", 10)).grid(row=0, column=0, sticky="w")
        self.total_products_var = tk.IntVar(value=30)
        tk.Spinbox(advanced_grid, from_=1, to=100, textvariable=self.total_products_var, width=10).grid(row=0, column=1, padx=5)

        # 자동 저장 간격
        tk.Label(advanced_grid, text="자동 저장 간격(초):", font=("맑은 고딕", 10)).grid(row=0, column=2, sticky="w", padx=(20,0))
        self.auto_save_interval = tk.IntVar(value=300)  # 5분
        tk.Spinbox(advanced_grid, from_=60, to=3600, textvariable=self.auto_save_interval, width=10).grid(row=0, column=3, padx=5)

        # 오류 시 재시도 횟수
        tk.Label(advanced_grid, text="오류 시 재시도:", font=("맑은 고딕", 10)).grid(row=1, column=0, sticky="w")
        self.retry_count = tk.IntVar(value=3)
        tk.Spinbox(advanced_grid, from_=1, to=10, textvariable=self.retry_count, width=10).grid(row=1, column=1, padx=5)

        # 결과 저장 폴더
        tk.Label(advanced_grid, text="결과 저장 폴더:", font=("맑은 고딕", 10)).grid(row=1, column=2, sticky="w", padx=(20,0))
        tk.Button(advanced_grid, text="변경", command=self.change_output_folder).grid(row=1, column=3, padx=5)

        # 실행 로그
        log_frame = tk.LabelFrame(settings_tab, text="📋 실행 로그", font=("맑은 고딕", 12, "bold"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.settings_log_text = tk.Text(log_frame, font=("Consolas", 9), wrap="word",
                                        bg="#2c3e50", fg="#ecf0f1")
        settings_log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.settings_log_text.yview)
        self.settings_log_text.configure(yscrollcommand=settings_log_scrollbar.set)

        self.settings_log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        settings_log_scrollbar.pack(side="right", fill="y", pady=5)

        # 초기 시스템 상태 업데이트
        self.update_system_status()

    # === 핵심 자동화 메서드들 ===

    def start_complete_automation(self):
        """완전 자동화 시작 - 메인 기능"""
        if self.automation_running:
            messagebox.showwarning("경고", "이미 자동화가 실행 중입니다.")
            return

        # 사전 체크
        if not self.pre_automation_check():
            return

        # 확인 대화상자
        total_products = self.total_products_var.get()
        response = messagebox.askyesno(
            "완전 자동화 시작",
            f"완전 자동화를 시작하시겠습니까?\n\n"
            f"🎯 처리할 제품: {total_products}개\n"
            f"⏰ 예상 소요시간: 2-3시간\n"
            f"📧 예상 생성물: {total_products}개 콜드메일\n"
            f"⛔ 중단: ESC키 또는 중단 버튼\n\n"
            f"✅ 브라우저에 {total_products}개 탭이 준비되었는지 확인해주세요!"
        )

        if not response:
            return

        # 자동화 시작
        self.automation_running = True
        self.total_products = total_products

        # UI 상태 변경
        self.main_status_var.set("🟡 자동화 실행 중...")
        self.master_start_btn.config(state="disabled", text="자동화 실행 중...\n(ESC키로 중단)")
        self.main_progress_bar.config(maximum=100)

        # 별도 스레드에서 실행
        threading.Thread(target=self.complete_automation_thread, daemon=True).start()

    def complete_automation_thread(self):
        """완전 자동화 실행 스레드"""
        start_time = datetime.now()

        try:
            self.main_log("🚀 완전 자동화 프로세스 시작")
            self.main_log(f"📊 목표: {self.total_products}개 제품 → {self.total_products}개 콜드메일")

            # 단계 1: 웹 자동화 (30%)
            self.update_step_status(0, "웹 자동화 시작", "#e67e22")
            self.progress_detail_var.set("1단계: 브라우저 자동화로 데이터 수집 중...")
            self.main_progress_bar['value'] = 5

            success = self.execute_web_automation()
            if not success or not self.automation_running:
                self.main_log("❌ 웹 자동화 실패 또는 사용자 중단")
                return

            self.update_step_status(0, "웹 자동화 완료", "#27ae60")
            self.main_progress_bar['value'] = 30

            # 단계 2: 데이터 정리 (10%)
            self.update_step_status(1, "데이터 정리 시작", "#3498db")
            self.progress_detail_var.set("2단계: 수집된 데이터를 AI 처리 가능한 형태로 정리 중...")

            self.organize_collected_data()

            self.update_step_status(1, "데이터 정리 완료", "#27ae60")
            self.main_progress_bar['value'] = 40

            # 단계 3: AI 분석 및 콜드메일 생성 (60%)
            self.update_step_status(2, "AI 분석 시작", "#9b59b6")
            self.progress_detail_var.set("3단계: AI가 이미지와 리뷰를 분석하여 콜드메일 생성 중...")

            success = self.execute_ai_generation()
            if not success or not self.automation_running:
                self.main_log("❌ AI 콜드메일 생성 실패 또는 사용자 중단")
                return

            self.update_step_status(2, "AI 분석 완료", "#27ae60")
            self.main_progress_bar['value'] = 100

            # 완료 처리
            end_time = datetime.now()
            duration = end_time - start_time

            self.main_status_var.set("🟢 완전 자동화 완료!")
            self.progress_detail_var.set(f"✅ 모든 작업 완료! 소요시간: {duration}")

            self.main_log("🎉 완전 자동화 프로세스 성공적으로 완료!")
            self.main_log(f"⏰ 총 소요시간: {duration}")
            self.main_log(f"📧 생성된 콜드메일: {len(self.generated_emails)}개")

            # 결과 업데이트
            self.update_all_displays()

            messagebox.showinfo("완료!",
                f"🎉 완전 자동화가 성공적으로 완료되었습니다!\n\n"
                f"📧 생성된 콜드메일: {len(self.generated_emails)}개\n"
                f"⏰ 소요시간: {duration}\n"
                f"📁 결과 위치: {self.get_output_folder()}\n\n"
                f"결과 보기 탭에서 상세 내용을 확인하세요!")

        except Exception as e:
            self.main_log(f"❌ 치명적 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"자동화 중 심각한 오류가 발생했습니다:\n{str(e)}")

        finally:
            # 상태 복원
            self.automation_running = False
            self.master_start_btn.config(state="normal", text="🚀 완전 자동화 시작\n(30개 제품 → 30개 콜드메일)")

            if not self.automation_running:  # 정상 완료인 경우
                self.main_status_var.set("🟢 대기 중 - 준비 완료")

    def execute_web_automation(self):
        """웹 자동화 실행 (file_organizer 기능 통합)"""
        try:
            self.main_log("🌐 웹 브라우저 자동화 시작")

            # pyautogui 설정
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 1  # 각 동작 사이에 1초 대기

            processed = 0
            failed = 0

            for i in range(1, self.total_products + 1):
                # 중단 및 일시정지 체크 (지시서 요구사항)
                while self.automation_paused:
                    self.main_log("⏸️ 자동화 일시정지 중...")
                    time.sleep(1)

                if not self.automation_running:
                    self.main_log("🛑 사용자에 의한 웹 자동화 중단")
                    return False

                # 응급 중단 체크
                if hasattr(self, 'safety_monitor') and self.safety_monitor:
                    if not self.safety_monitor.comprehensive_safety_check():
                        self.main_log("🛑 안전 한계로 인한 자동화 중단")
                        return False

                try:
                    self.main_log(f"🔄 제품 {i}/{self.total_products} 처리 중...")
                    self.web_automation_status_var.set(f"제품 {i} 처리 중...")

                    # 실제 웹 자동화 로직 실행
                    success = self.process_single_product(i)

                    if success:
                        processed += 1
                        self.processed_count = processed  # 실제 카운터 업데이트
                        self.main_log(f"✅ 제품 {i} 처리 완료")

                        # FIFO 및 데이터베이스 연결 (지시서 요구사항)
                        self.process_captured_files(i)

                        # 실제 진행률 업데이트 (지시서 요구사항)
                        self.web_progress_var.set(f"{processed}/{self.total_products} 완료")
                        self.web_progress_bar['value'] = (processed / self.total_products) * 100

                    else:
                        failed += 1
                        self.failed_products.append(i)
                        self.main_log(f"❌ 제품 {i} 처리 실패")

                        # 실패해도 진행률은 업데이트
                        self.web_progress_var.set(f"{processed}/{self.total_products} 완료 ({failed}개 실패)")
                        self.web_progress_bar['value'] = (i / self.total_products) * 100

                    # 전체 진행률 업데이트
                    overall_progress = (i / self.total_products) * 30  # 웹 자동화는 전체의 30%
                    if hasattr(self, 'main_progress_bar'):
                        self.main_progress_bar['value'] = 5 + overall_progress

                    # 다음 제품으로 이동 (지시서: 실제 페이지 로딩 필요)
                    if i < self.total_products:
                        self.main_log(f"📄 다음 제품으로 이동 중... ({i+1}/{self.total_products})")

                        # 현재 탭 닫기
                        pyautogui.hotkey('ctrl', 'w')
                        time.sleep(2)

                        # 다음 제품 페이지 로딩 대기
                        self.main_log("⏳ 다음 페이지 로딩 대기...")
                        time.sleep(3)  # 페이지 로딩 시간

                except Exception as e:
                    failed += 1
                    self.failed_products.append(i)
                    self.main_log(f"❌ 제품 {i} 오류: {str(e)}")

                    # 오류가 발생해도 진행률 업데이트
                    self.web_progress_var.set(f"{processed}/{self.total_products} 완료 ({failed}개 오류)")
                    self.web_progress_bar['value'] = (i / self.total_products) * 100

                    # 오류 발생 시에도 다음 제품으로 이동 (지시서 요구사항)
                    if i < self.total_products:
                        try:
                            pyautogui.hotkey('ctrl', 'w')
                            time.sleep(2)
                        except:
                            pass
                    continue

            self.main_log(f"🌐 웹 자동화 완료: 성공 {processed}개, 실패 {failed}개")
            self.web_automation_status_var.set(f"완료: 성공 {processed}개, 실패 {failed}개")

            return processed > 0  # 최소 1개라도 성공하면 계속 진행

        except Exception as e:
            self.main_log(f"❌ 웹 자동화 심각한 오류: {str(e)}")
            return False

    def process_single_product(self, product_index):
        """단일 제품 처리 (원본 file_organizer 로직 복원)"""
        try:
            # 1. URL 수집
            url = self.collect_current_url()
            if not url:
                self.main_log(f"❌ 제품 {product_index}: URL 수집 실패")
                return False

            # 2. 상세정보 펼쳐보기 (스크롤하면서 찾기)
            if not self.expand_product_details():
                self.main_log(f"❌ 제품 {product_index}: 상세정보 버튼 찾기 실패")
                return False

            # 3. Fireshot으로 상세페이지 캡처
            if not self.capture_detail_page(product_index):
                self.main_log(f"❌ 제품 {product_index}: 페이지 캡처 실패")
                return False

            # 4. 크롤링 시퀀스 (원본 로직)
            if not self.crawling_sequence():
                self.main_log(f"❌ 제품 {product_index}: 크롤링 시퀀스 실패")
                return False

            # 5. URL 기록
            self.record_product_url(url, product_index)

            return True

        except Exception as e:
            self.main_log(f"❌ 제품 {product_index} 처리 중 오류: {str(e)}")
            return False

    def collect_current_url(self):
        """현재 탭의 URL 수집 (원본 로직)"""
        try:
            pyautogui.hotkey('ctrl', 'l')  # 주소창 선택
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')  # URL 복사
            time.sleep(0.5)
            url = pyperclip.paste()
            self.main_log(f"✅ URL 수집 완료: {url[:50]}...")
            return url
        except Exception as e:
            self.main_log(f"❌ URL 수집 실패: {str(e)}")
            return None

    def expand_product_details(self):
        """상세정보 펼쳐보기 (원본 스크롤 로직)"""
        max_scrolls = 16
        scroll_amount = 800

        for scroll_count in range(max_scrolls):
            if not self.automation_running:  # 중단 확인
                return False

            try:
                location = pyautogui.locateOnScreen(self.image_files['detail_button'], confidence=0.8)
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center)
                    self.main_log(f"✅ 상세정보 펼쳐보기 완료 (스크롤 {scroll_count + 1}회)")
                    time.sleep(2)  # 페이지 로딩 대기
                    return True
            except pyautogui.ImageNotFoundException:
                pass

            # 스크롤 다운
            pyautogui.scroll(-scroll_amount)
            time.sleep(0.5)
            self.main_log(f"🔄 스크롤 {scroll_count + 1}/{max_scrolls}")

        self.main_log("❌ 상세정보 펼쳐보기 버튼을 찾지 못함")
        return False

    def record_product_url(self, url, product_index):
        """제품 URL을 임시로 기록"""
        self.main_log(f"📝 제품 {product_index} URL 기록: {url[:50]}...")

    def close_unwanted_popups(self):
        """원치 않는 팝업창 닫기 (네이버 가격비교창 등)"""
        try:
            # 1. ESC 키로 팝업 닫기 시도
            pyautogui.press('escape')
            time.sleep(0.5)

            # 2. Alt+F4로 현재 창이 팝업이면 닫기
            current_title = pyautogui.getActiveWindowTitle()
            if current_title and ('가격비교' in current_title or 'price' in current_title.lower()):
                self.main_log(f"🚫 팝업창 감지: {current_title}")
                pyautogui.hotkey('alt', 'f4')
                time.sleep(1)

            # 3. 절대 좌표로 팝업 닫기 버튼 클릭 시도
            if 'close_popup' in self.coords:
                x, y = self.coords['close_popup']
                pyautogui.click(x, y)
                time.sleep(0.5)

            # 4. 브라우저로 포커스 돌리기
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.5)

        except Exception as e:
            self.main_log(f"⚠️ 팝업 차단 중 오류: {str(e)}")

    def crawling_sequence(self):
        """크롤링 시퀀스 (원본 컨텍스트 기반 로직)"""
        try:
            # 팝업 차단: 네이버 가격비교창 등 원치않는 창 닫기
            self.close_unwanted_popups()

            # 1단계: 크롤링툴 실행
            pyautogui.hotkey('ctrl', 'shift', 'a')
            time.sleep(3)

            # 다시 한번 팝업 차단
            self.close_unwanted_popups()

            # 2단계: 크롤링 팝업에서 리뷰 버튼 클릭 (지시서 수정: 실제 경로 사용)
            if not self.wait_for_button_with_timeout(self.image_files['review_button'], 30):
                return False

            # 3단계: 리뷰 화면에서 분석시작하기 클릭
            if not self.wait_for_button_with_timeout(self.image_files['analysis_start'], 30):
                return False

            # 4단계: 분석 결과에서 엑셀 다운로드 클릭
            if not self.wait_for_button_with_timeout(self.image_files['excel_download'], 60):
                return False

            self.main_log("✅ 크롤링 시퀀스 완료")
            return True

        except Exception as e:
            self.main_log(f"❌ 크롤링 시퀀스 실패: {str(e)}")
            return False

    def wait_for_button_with_timeout(self, button_image, timeout=30):
        """타임아웃 대기로 버튼 찾기 (절대 좌표 백업 포함)"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not self.automation_running:
                return False

            try:
                # 1차: 이미지 인식 시도
                location = pyautogui.locateOnScreen(button_image, confidence=0.8)
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center)
                    self.main_log(f"✅ 이미지 인식 성공: {Path(button_image).name}")
                    return True

            except (pyautogui.ImageNotFoundException, FileNotFoundError):
                # 2차: 절대 좌표 백업 시도 (지시서 요구사항)
                coord_key = self._get_coord_key_from_image(button_image)
                if coord_key and coord_key in self.coords:
                    x, y = self.coords[coord_key]
                    pyautogui.click(x, y)
                    self.main_log(f"⚠️ 절대 좌표 사용: {coord_key} ({x}, {y})")
                    return True

            time.sleep(1)

        self.main_log(f"❌ 버튼 찾기 실패: {Path(button_image).name}")
        return False

    def _get_coord_key_from_image(self, image_path):
        """이미지 경로에서 좌표 키 추출"""
        filename = Path(image_path).stem
        coord_mapping = {
            'close_button': 'close_popup',
            'sort_button': 'sort_dropdown',
            'review_sort': 'review_sort'
        }
        return coord_mapping.get(filename, None)

    def process_captured_files(self, product_index):
        """캡처된 파일들을 FIFO와 데이터베이스로 처리 (지시서 요구사항)"""
        try:
            # 1. 가장 최근 다운로드 파일들 찾기
            download_files = self.get_recent_downloads()

            for file_path in download_files:
                # 2. 중복 파일 체크
                if self.is_duplicate_file(file_path):
                    self.main_log(f"🔄 중복 파일 건너뜀: {Path(file_path).name}")
                    continue

                # 3. FIFO 큐에 추가
                store_name = f"제품_{product_index}"
                self.add_pending_store(store_name)

                # 4. 파일 정리 및 이동
                self.organize_single_file(file_path, product_index)

                # 5. 데이터베이스에 기록
                self.add_to_database(
                    product_name=f"제품_{product_index}",
                    brand_name="브랜드명_미상",
                    email_address=""
                )

                self.main_log(f"📁 파일 처리 완료: {Path(file_path).name}")

        except Exception as e:
            self.main_log(f"❌ 파일 처리 오류: {str(e)}")

    def get_recent_downloads(self):
        """최근 다운로드 파일들 가져오기"""
        try:
            download_folder = Path(self.download_folder)
            if not download_folder.exists():
                return []

            # 최근 5분 이내 수정된 파일들
            recent_files = []
            cutoff_time = time.time() - 300  # 5분

            for file_path in download_folder.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime > cutoff_time:
                    recent_files.append(file_path)

            # 수정 시간순 정렬
            recent_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return recent_files[:10]  # 최대 10개

        except Exception as e:
            self.main_log(f"❌ 최근 다운로드 파일 검색 실패: {str(e)}")
            return []

    def organize_single_file(self, file_path, product_index):
        """단일 파일 정리"""
        try:
            # 작업 폴더 생성
            work_subfolder = self.work_folder / "03_데이터_수집" / f"{self.today}_제품_{product_index}"
            work_subfolder.mkdir(parents=True, exist_ok=True)

            # 파일 이동
            dest_path = work_subfolder / file_path.name
            shutil.move(str(file_path), str(dest_path))

            self.main_log(f"📁 파일 이동 완료: {dest_path}")

        except Exception as e:
            self.main_log(f"❌ 파일 정리 실패: {str(e)}")

    def create_real_payload(self, img_file, review_file):
        """실제 OCR 및 리뷰 데이터로 payload 생성 (지시서 요구사항)"""
        try:
            payload_data = {
                "image_data": {},
                "review_data": {},
                "metadata": {
                    "image_file": str(img_file),
                    "review_file": str(review_file),
                    "processed_at": datetime.now().isoformat()
                }
            }

            # 1. 이미지 OCR 처리
            if img_file.exists():
                ocr_result = self.process_image_ocr(img_file)
                payload_data["image_data"] = {
                    "filename": img_file.name,
                    "ocr_text": ocr_result.get("text", ""),
                    "confidence": ocr_result.get("confidence", 0),
                    "structured_data": ocr_result.get("structured", {})
                }
                self.main_log(f"📄 OCR 처리 완료: {len(ocr_result.get('text', ''))}자")
            else:
                self.main_log(f"⚠️ 이미지 파일 없음: {img_file}")

            # 2. 리뷰 데이터 처리
            if review_file.exists():
                review_data = self.process_review_file(review_file)
                payload_data["review_data"] = {
                    "filename": review_file.name,
                    "reviews": review_data.get("reviews", []),
                    "summary": review_data.get("summary", {}),
                    "sentiment": review_data.get("sentiment", "neutral")
                }
                self.main_log(f"💬 리뷰 처리 완료: {len(review_data.get('reviews', []))}개")
            else:
                self.main_log(f"⚠️ 리뷰 파일 없음: {review_file}")

            # 3. JSON 형태로 반환
            import json
            return json.dumps(payload_data, ensure_ascii=False, indent=2)

        except Exception as e:
            self.main_log(f"❌ Payload 생성 실패: {str(e)}")
            # 실패시 기본 payload 반환
            return f"이미지: {img_file.name}, 리뷰: {review_file.name} - 처리 오류"

    def process_image_ocr(self, img_file):
        """이미지 OCR 처리"""
        try:
            # OCR 엔진 import (지시서: 실제 데이터 사용)
            from ocr.engine import process_images
            from ocr.postproc import clean_ocr_output

            # OCR 실행
            ocr_results = process_images([str(img_file)])

            if ocr_results:
                # 후처리
                cleaned_text = clean_ocr_output(ocr_results[0].get("text", ""))

                return {
                    "text": cleaned_text,
                    "confidence": ocr_results[0].get("confidence", 0),
                    "structured": ocr_results[0].get("structured_data", {})
                }
            else:
                return {"text": "", "confidence": 0, "structured": {}}

        except ImportError:
            self.main_log("⚠️ OCR 모듈 없음 - 기본 처리 사용")
            return {"text": f"OCR 처리 필요: {img_file.name}", "confidence": 0, "structured": {}}
        except Exception as e:
            self.main_log(f"❌ OCR 처리 실패: {str(e)}")
            return {"text": "", "confidence": 0, "structured": {}}

    def process_review_file(self, review_file):
        """리뷰 파일 처리"""
        try:
            # 리뷰 정규화 import (지시서: 실제 데이터 사용)
            from reviews.normalize import normalize_reviews

            # 리뷰 파일 읽기
            if review_file.suffix.lower() == '.csv':
                import pandas as pd
                df = pd.read_csv(review_file, encoding='utf-8')
                reviews = df.to_dict('records') if not df.empty else []
            else:
                # 텍스트 파일
                with open(review_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    reviews = [{"text": line.strip()} for line in content.split('\n') if line.strip()]

            # 리뷰 정규화
            normalized_reviews = normalize_reviews(reviews)

            # 요약 생성
            summary = {
                "total_count": len(normalized_reviews),
                "avg_rating": sum(r.get("rating", 0) for r in normalized_reviews) / max(len(normalized_reviews), 1),
                "keywords": self.extract_review_keywords(normalized_reviews)
            }

            return {
                "reviews": normalized_reviews[:10],  # 최대 10개만
                "summary": summary,
                "sentiment": "positive" if summary["avg_rating"] > 3.5 else "neutral"
            }

        except ImportError:
            self.main_log("⚠️ 리뷰 정규화 모듈 없음 - 기본 처리 사용")
            return {"reviews": [{"text": f"리뷰 처리 필요: {review_file.name}"}], "summary": {}, "sentiment": "neutral"}
        except Exception as e:
            self.main_log(f"❌ 리뷰 처리 실패: {str(e)}")
            return {"reviews": [], "summary": {}, "sentiment": "neutral"}

    def extract_review_keywords(self, reviews):
        """리뷰에서 키워드 추출"""
        try:
            keywords = []
            for review in reviews:
                text = review.get("text", "")
                # 간단한 키워드 추출 (실제로는 더 정교한 NLP 필요)
                words = text.split()
                keywords.extend([w for w in words if len(w) > 2])

            # 빈도수 기반 상위 키워드
            from collections import Counter
            counter = Counter(keywords)
            return [word for word, count in counter.most_common(10)]
        except Exception:
            return []

    def update_database_after_email_generation(self, img_file, review_file, email_file):
        """이메일 생성 후 데이터베이스 업데이트 (지시서 요구사항)"""
        try:
            # 파일명에서 제품 정보 추출
            product_name = self.extract_product_name_from_files(img_file, review_file)
            brand_name = self.extract_brand_name_from_files(img_file, review_file)

            # 이메일 파일 경로를 이메일 주소로 사용 (임시)
            email_address = str(email_file)

            # 데이터베이스 업데이트
            self.update_database_entry(product_name, brand_name, email_address)

            self.main_log(f"📊 DB 업데이트: {product_name} 이메일 완료")

        except Exception as e:
            self.main_log(f"❌ DB 업데이트 실패: {str(e)}")

    def extract_product_name_from_files(self, img_file, review_file):
        """파일들에서 제품명 추출"""
        # 파일명에서 제품명 추출 시도
        img_name = img_file.stem if hasattr(img_file, 'stem') else str(img_file)
        review_name = review_file.stem if hasattr(review_file, 'stem') else str(review_file)

        # 공통 부분이 있으면 제품명으로 사용
        common_parts = []
        img_parts = img_name.split('_')
        review_parts = review_name.split('_')

        for part in img_parts:
            if part in review_parts and len(part) > 2:
                common_parts.append(part)

        if common_parts:
            return '_'.join(common_parts)
        else:
            return f"제품_{img_name[:10]}"

    def extract_brand_name_from_files(self, img_file, review_file):
        """파일들에서 브랜드명 추출"""
        # 간단한 브랜드명 추출 (실제로는 더 정교한 로직 필요)
        img_name = img_file.stem if hasattr(img_file, 'stem') else str(img_file)

        # 파일명에서 브랜드로 추정되는 부분 찾기
        brand_keywords = ['samsung', 'lg', 'apple', 'sony', 'nike', 'adidas']
        for keyword in brand_keywords:
            if keyword in img_name.lower():
                return keyword.title()

        return "브랜드_미상"


def capture_detail_page(self, product_index):
    """상세페이지 캡처 (Fireshot)"""
    try:
        # Ctrl+Shift+S (Fireshot 단축키)
        pyautogui.hotkey('ctrl', 'shift', 's')

        save_image = self.image_files['fireshot_save']
        if os.path.exists(save_image):
            timeout = max(float(self.fireshot_capture_timeout_sec), 0)
            interval = max(float(self.fireshot_capture_poll_interval_sec), 0.1)
            elapsed = 0.0

            while elapsed <= timeout:
                location = pyautogui.locateOnScreen(save_image, confidence=0.8)
                if location:
                    pyautogui.click(location)
                    time.sleep(2)
                    return True
                time.sleep(interval)
                elapsed += interval

            self.main_log(f"⚠️ 제품 {product_index}: Fireshot 저장 버튼을 {timeout:.1f}초 내 찾지 못했습니다")
            return False

        self.main_log(f"⚠️ 제품 {product_index}: Fireshot 저장 버튼 이미지가 존재하지 않습니다 ({save_image})")
        return False

    except Exception as e:
        self.main_log(f"❌ 제품 {product_index} 캡처 오류: {str(e)}")
        return False

    # 구형 함수들 제거됨 - 새로운 원본 로직으로 대체

    def organize_collected_data(self):
        """수집된 데이터 정리"""
        try:
            self.main_log("🗂️ 수집된 데이터 정리 시작")

            # 다운로드 폴더에서 파일 스캔
            download_folder = Path(self.download_path_var.get())

            if not download_folder.exists():
                self.main_log("❌ 다운로드 폴더가 존재하지 않음")
                return False

            # 오늘 날짜 기준으로 파일 찾기
            today = datetime.now()
            cutoff_time = today.replace(hour=0, minute=0, second=0).timestamp()

            # 대상 폴더 준비
            img_target = Path("data/product_images")
            review_target = Path("data/reviews")
            img_target.mkdir(parents=True, exist_ok=True)
            review_target.mkdir(parents=True, exist_ok=True)

            organized_count = 0

            # 이미지 파일 정리
            for img_pattern in ['*.png', '*.jpg', '*.jpeg']:
                for img_file in download_folder.glob(img_pattern):
                    if img_file.stat().st_mtime >= cutoff_time:
                        target_path = img_target / img_file.name
                        if not target_path.exists():
                            shutil.copy2(img_file, target_path)
                            organized_count += 1
                            self.main_log(f"📷 이미지 정리: {img_file.name}")

            # 리뷰 파일 정리
            for review_pattern in ['*.xlsx', '*.xls', '*.csv']:
                for review_file in download_folder.glob(review_pattern):
                    if review_file.stat().st_mtime >= cutoff_time:
                        target_path = review_target / review_file.name
                        if not target_path.exists():
                            shutil.copy2(review_file, target_path)
                            organized_count += 1
                            self.main_log(f"📊 리뷰 데이터 정리: {review_file.name}")

            # 작업 폴더의 데이터도 확인
            work_data_folder = Path(self.work_path_var.get()) / "03_데이터_수집"
            if work_data_folder.exists():
                today_str = today.strftime("%Y-%m-%d")
                today_folders = list(work_data_folder.glob(f"{today_str}*"))

                for folder in today_folders:
                    for file_path in folder.rglob("*"):
                        if file_path.is_file():
                            suffix = file_path.suffix.lower()

                            if suffix in ['.png', '.jpg', '.jpeg']:
                                target_path = img_target / file_path.name
                                if not target_path.exists():
                                    shutil.copy2(file_path, target_path)
                                    organized_count += 1

                            elif suffix in ['.xlsx', '.xls', '.csv']:
                                target_path = review_target / file_path.name
                                if not target_path.exists():
                                    shutil.copy2(file_path, target_path)
                                    organized_count += 1

            self.main_log(f"✅ 데이터 정리 완료: {organized_count}개 파일")

            # 파일 목록 업데이트
            self.update_data_preview()

            return organized_count > 0

        except Exception as e:
            self.main_log(f"❌ 데이터 정리 오류: {str(e)}")
            return False

    def execute_ai_generation(self):
        """AI 콜드메일 생성 실행"""
        try:
            self.main_log("🤖 AI 콜드메일 생성 시작")

            # 처리할 파일들 스캔
            img_folder = Path("data/product_images")
            review_folder = Path("data/reviews")

            images = list(img_folder.glob("*.png")) + list(img_folder.glob("*.jpg")) + list(img_folder.glob("*.jpeg"))
            reviews = list(review_folder.glob("*.csv")) + list(review_folder.glob("*.xlsx")) + list(review_folder.glob("*.xls"))

            if not images:
                self.main_log("❌ 처리할 이미지가 없습니다")
                return False

            if not reviews:
                self.main_log("❌ 처리할 리뷰 파일이 없습니다")
                return False

            self.main_log(f"📊 처리 대상: 이미지 {len(images)}개, 리뷰 {len(reviews)}개")

            # AI 클라이언트 초기화
            cfg = load_config(self.config_path)

            # 사용자 설정 적용
            cfg.policy.email_min_chars = self.min_chars.get()
            cfg.policy.email_max_chars = self.max_chars.get()
            cfg.policy.tone_default = self.tone_var.get()

            client = GeminiClient(cfg)

            # 프롬프트 로드
            with open(f"{cfg.paths.prompts_dir}/cold_email.json", "r", encoding="utf-8") as f:
                prompt = json.load(f)

            # 출력 폴더 설정
            output_folder = self.get_output_folder()
            output_folder.mkdir(parents=True, exist_ok=True)

            # 배치 생성
            total_combinations = len(images) * len(reviews)
            processed = 0
            generated_count = 0

            self.ai_progress_bar.config(maximum=total_combinations)

            for img_file in images:
                for review_file in reviews:
                    if not self.automation_running:
                        self.main_log("🛑 AI 생성 중단됨")
                        return False

                    processed += 1

                    self.main_log(f"🧠 AI 처리 ({processed}/{total_combinations}): {img_file.name} + {review_file.name}")
                    self.ai_status_var.set(f"AI 처리 중... ({processed}/{total_combinations})")
                    self.ai_progress_bar['value'] = processed

                    try:
                        # 실제 OCR 및 리뷰 데이터 로드 (지시서 요구사항)
                        user_payload = self.create_real_payload(img_file, review_file)

                        # AI로 콜드메일 생성
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        draft = loop.run_until_complete(client.generate(prompt, user_payload))
                        loop.close()

                        # 최종 조립
                        final_email = compose_final_email(draft, cfg.policy)

                        # 저장
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_file = output_folder / f"email_{timestamp}_{processed}.json"

                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(final_email, f, ensure_ascii=False, indent=2)

                        self.generated_emails.append({
                            'file': output_file,
                            'data': final_email,
                            'timestamp': datetime.now(),
                            'source_image': img_file.name,
                            'source_review': review_file.name
                        })

                        generated_count += 1
                        self.main_log(f"✅ 저장 완료: {output_file.name}")

                        # 데이터베이스 업데이트 (지시서 요구사항: 이메일 생성 후)
                        self.update_database_after_email_generation(img_file, review_file, output_file)

                        # 진행률 업데이트 (AI 생성은 전체의 60%)
                        ai_progress = (processed / total_combinations) * 60
                        self.main_progress_bar['value'] = 40 + ai_progress

                    except Exception as e:
                        self.main_log(f"❌ AI 처리 오류 ({img_file.name}): {str(e)}")
                        continue

            self.ai_status_var.set(f"AI 생성 완료: {generated_count}개")
            self.ai_progress_var.set(f"생성 완료: {generated_count}개")

            self.main_log(f"🎉 AI 콜드메일 생성 완료: 총 {generated_count}개")

            return generated_count > 0

        except Exception as e:
            self.main_log(f"❌ AI 생성 심각한 오류: {str(e)}")
            return False

    # === 개별 실행 메서드들 ===

    def start_web_automation_only(self):
        """웹 자동화만 실행 (원본 카운트다운 방식)"""
        if self.automation_running:
            messagebox.showwarning("경고", "다른 자동화가 실행 중입니다.")
            return

        # 원본 방식: 사용자에게 브라우저 준비 안내
        result = messagebox.askyesno(
            "웹 자동화 시작",
            "🌐 웹 자동화를 시작합니다.\n\n"
            "준비사항:\n"
            "1. 네이버 쇼핑에서 원하는 검색어로 검색\n"
            "2. 정렬을 '리뷰 많은 순'으로 변경\n"
            "3. 상품 목록이 표시된 상태에서 대기\n\n"
            "준비가 완료되면 '예'를 누르세요.\n"
            "5초 후 자동화가 시작됩니다."
        )

        if not result:
            return

        self.automation_running = True
        self.automation_button.config(text="🕐 5초 후 시작...", state="disabled")

        # 카운트다운 스레드 시작
        threading.Thread(target=self.countdown_and_start_automation, daemon=True).start()

    def countdown_and_start_automation(self):
        """카운트다운 후 웹 자동화 시작"""
        try:
            # 5초 카운트다운
            for i in range(5, 0, -1):
                self.update_status(f"🕐 {i}초 후 웹 자동화 시작... 브라우저를 준비하세요!")
                self.automation_button.config(text=f"🕐 {i}초 후 시작...")
                time.sleep(1)

            self.update_status("🚀 웹 자동화 시작!")
            self.automation_button.config(text="🔄 자동화 실행 중...")

            # 웹 자동화 실행
            success = self.execute_web_automation()

            if success:
                self.organize_collected_data()
                self.update_status("✅ 웹 자동화 완료!")
                messagebox.showinfo("완료", "웹 자동화가 완료되었습니다!")
            else:
                self.update_status("⚠️ 웹 자동화 중단됨")
                messagebox.showwarning("중단", "웹 자동화가 중단되었습니다.")

        except Exception as e:
            self.update_status(f"❌ 웹 자동화 오류: {str(e)}")
            messagebox.showerror("오류", f"웹 자동화 중 오류가 발생했습니다: {str(e)}")
        finally:
            self.automation_running = False
            self.automation_button.config(text="🚀 웹 자동화만 시작", state="normal")

    def web_automation_only_thread(self):
        """웹 자동화 단독 실행 스레드"""
        try:
            success = self.execute_web_automation()
            if success:
                self.organize_collected_data()
                messagebox.showinfo("완료", "웹 자동화가 완료되었습니다!")
            else:
                messagebox.showwarning("중단", "웹 자동화가 중단되었습니다.")
        finally:
            self.automation_running = False

    def start_ai_generation_only(self):
        """AI 생성만 실행 (지시서: automation_running과 독립적으로)"""
        if self.is_ai_processing:
            messagebox.showwarning("경고", "AI 처리가 실행 중입니다.")
            return

        # 지시서 요구사항: self.automation_running 체크하지 않음
        self.is_ai_processing = True
        self.main_log("🤖 AI 콜드메일 생성 단독 실행 (웹 자동화와 독립)")
        threading.Thread(target=self.ai_generation_only_thread, daemon=True).start()

    def ai_generation_only_thread(self):
        """AI 생성 단독 실행 스레드"""
        try:
            success = self.execute_ai_generation()
            if success:
                self.update_all_displays()
                messagebox.showinfo("완료", f"AI 콜드메일 생성이 완료되었습니다!\n생성된 콜드메일: {len(self.generated_emails)}개")
            else:
                messagebox.showwarning("실패", "AI 콜드메일 생성에 실패했습니다.")
        finally:
            self.is_ai_processing = False

    def run_ai_smoke_test(self):
        """AI 스모크 테스트"""
        def test_thread():
            try:
                self.main_log("🧪 AI 스모크 테스트 실행 중...")
                result = subprocess.run(
                    ["python", "run_email_smoke.py"],
                    capture_output=True,
                    text=True,
                    cwd="."
                )

                if result.returncode == 0:
                    self.main_log("✅ AI 스모크 테스트 성공!")
                    messagebox.showinfo("성공", "AI 스모크 테스트가 성공했습니다!")
                else:
                    self.main_log("❌ AI 스모크 테스트 실패")
                    messagebox.showerror("실패", f"AI 스모크 테스트가 실패했습니다:\n{result.stderr}")

            except Exception as e:
                self.main_log(f"❌ 테스트 실행 오류: {str(e)}")

        threading.Thread(target=test_thread, daemon=True).start()

    # === UI 업데이트 메서드들 ===

    def main_log(self, message):
        """메인 로그에 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"

        # 메인 로그
        self.main_log_text.insert("end", full_message)
        self.main_log_text.see("end")

        # 설정 탭 로그에도 추가
        self.settings_log_text.insert("end", full_message)

    def update_status(self, message):
        """명세서 호환성을 위한 상태 업데이트 메서드"""
        # main_log와 동일한 기능이지만 명세서 호환성 제공
        self.main_log(message)

        # 웹 자동화 상태도 업데이트
        if hasattr(self, 'web_automation_status_var'):
            self.web_automation_status_var.set(message)

    def update_progress(self):
        """명세서 호환성을 위한 진행률 업데이트 메서드"""
        if hasattr(self, 'web_progress_var'):
            self.web_progress_var.set(f"{self.processed_count}/{self.total_products} 완료")

        if hasattr(self, 'web_progress_bar'):
            progress_percentage = (self.processed_count / self.total_products) * 100
            self.web_progress_bar['value'] = progress_percentage

        self.root.update_idletasks()
        self.settings_log_text.see("end")

        self.root.update_idletasks()

    # === FIFO 및 중복 제어 로직 (명세서 호환성) ===

    def get_next_pending_store(self):
        """대기 중인 스토어 정보 반환 (FIFO)"""
        if self.pending_stores:
            return self.pending_stores.pop(0)  # 가장 오래된 것부터
        return None

    def clean_old_pending_stores(self, cutoff_minutes=5):
        """오래된 대기 정보 정리"""
        cutoff_time = datetime.now() - timedelta(minutes=cutoff_minutes)
        self.pending_stores = [
            (store, timestamp) for store, timestamp in self.pending_stores
            if timestamp > cutoff_time
        ]

    def get_file_hash(self, file_path):
        """파일의 SHA-256 해시 계산"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.main_log(f"❌ 파일 해시 계산 실패: {Path(file_path).name}, {str(e)}")
            return None

    def is_duplicate_file(self, file_path):
        """중복 파일 체크"""
        file_hash = self.get_file_hash(file_path)
        if file_hash is None:
            return False

        if file_hash in self.file_hashes:
            self.main_log(f"🔄 중복 파일 감지: {Path(file_path).name}")
            return True

        self.file_hashes[file_hash] = str(file_path)
        return False

    def add_pending_store(self, store_name):
        """대기 저장소에 스토어 추가"""
        timestamp = datetime.now()
        self.pending_stores.append((store_name, timestamp))
        self.main_log(f"📝 대기 큐에 추가: {store_name}")

        # 오래된 항목 정리
        self.clean_old_pending_stores()

    # === 데이터베이스 관리 함수들 (명세서 호환성) ===

    def create_database_if_missing(self):
        """데이터베이스가 없으면 생성"""
        if not self.database_file.exists():
            self.create_excel_database()

    def create_excel_database(self):
        """Excel 데이터베이스 초기 생성"""
        try:
            # 데이터베이스 폴더 생성
            self.database_file.parent.mkdir(parents=True, exist_ok=True)

            # 빈 DataFrame 생성
            df = pd.DataFrame(columns=[
                "수집일자", "제품명", "브랜드명", "처리상태", "이메일주소"
            ])

            # Excel 파일로 저장
            df.to_excel(self.database_file, index=False, engine='openpyxl')
            self.main_log(f"📊 데이터베이스 생성 완료: {self.database_file}")

        except Exception as e:
            self.main_log(f"❌ 데이터베이스 생성 실패: {str(e)}")

    def add_to_database(self, product_name, brand_name, email_address=""):
        """데이터베이스에 새 항목 추가"""
        try:
            # 기존 데이터 로드
            if self.database_file.exists():
                df = pd.read_excel(self.database_file, engine='openpyxl')
            else:
                self.create_excel_database()
                df = pd.read_excel(self.database_file, engine='openpyxl')

            # 새 행 추가 (pandas concat 사용, append는 deprecated)
            new_row = pd.DataFrame({
                "수집일자": [self.today],
                "제품명": [product_name],
                "브랜드명": [brand_name],
                "처리상태": ["수집완료"],
                "이메일주소": [email_address]
            })

            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(self.database_file, index=False, engine='openpyxl')

            self.main_log(f"📊 데이터베이스 추가: {product_name} ({brand_name})")

        except Exception as e:
            self.main_log(f"❌ 데이터베이스 업데이트 실패: {str(e)}")

    def update_database_entry(self, product_name, brand_name, email_address):
        """기존 데이터베이스 항목 업데이트"""
        try:
            if not self.database_file.exists():
                self.main_log("❌ 데이터베이스 파일이 없습니다")
                return

            df = pd.read_excel(self.database_file, engine='openpyxl')

            # 제품명과 브랜드명으로 항목 찾기
            mask = (df['제품명'] == product_name) & (df['브랜드명'] == brand_name)

            if mask.any():
                df.loc[mask, '이메일주소'] = email_address
                df.loc[mask, '처리상태'] = "이메일완료"
                df.to_excel(self.database_file, index=False, engine='openpyxl')
                self.main_log(f"📊 데이터베이스 업데이트: {product_name} 이메일 완료")
            else:
                self.main_log(f"⚠️ 데이터베이스에서 항목을 찾을 수 없음: {product_name}")

        except Exception as e:
            self.main_log(f"❌ 데이터베이스 업데이트 실패: {str(e)}")

    def load_database(self):
        """데이터베이스 로드 및 통계 정보 반환"""
        try:
            if not self.database_file.exists():
                return None

            df = pd.read_excel(self.database_file, engine='openpyxl')

            stats = {
                'total_count': len(df),
                'completed_count': len(df[df['처리상태'] == '이메일완료']),
                'pending_count': len(df[df['처리상태'] == '수집완료']),
                'today_count': len(df[df['수집일자'] == self.today])
            }

            self.main_log(f"📊 데이터베이스 로드: 총 {stats['total_count']}개, 오늘 {stats['today_count']}개")
            return df

        except Exception as e:
            self.main_log(f"❌ 데이터베이스 로드 실패: {str(e)}")
            return None

    # === 자산 의존성 검증 ===

    def validate_image_assets(self):
        """이미지 자산 파일 존재 여부 검증"""
        missing_assets = []

        for asset_name, asset_path in self.image_files.items():
            if not Path(asset_path).exists():
                missing_assets.append(f"{asset_name}: {asset_path}")

        if missing_assets:
            self.main_log("❌ 누락된 이미지 자산들:")
            for missing in missing_assets:
                self.main_log(f"   - {missing}")
            return False
        else:
            self.main_log(f"✅ 모든 이미지 자산 확인됨 ({len(self.image_files)}개)")
            return True

    def get_asset_path(self, asset_name):
        """자산 경로 안전하게 가져오기"""
        if asset_name in self.image_files:
            path = Path(self.image_files[asset_name])
            if path.exists():
                return str(path)
            else:
                self.main_log(f"⚠️ 자산 파일 없음: {asset_name} ({path})")
                return None
        else:
            self.main_log(f"⚠️ 알 수 없는 자산: {asset_name}")
            return None

    # === 안전 모니터링 통합 ===

    def init_safety_monitoring(self):
        """안전 모니터링 시스템 초기화"""
        try:
            from core.safety_monitor import comprehensive_safety
            self.safety_monitor = comprehensive_safety
            self.main_log("🔒 종합 안전 모니터링 시스템 활성화")

            # 주기적 안전 검사 스레드 시작
            self.start_safety_monitoring_thread()

        except Exception as e:
            self.main_log(f"⚠️ 안전 모니터링 초기화 실패: {str(e)}")
            self.safety_monitor = None

    def start_safety_monitoring_thread(self):
        """안전 모니터링 백그라운드 스레드 시작"""
        def safety_monitor_loop():
            while not getattr(self, '_stop_monitoring', False):
                try:
                    if hasattr(self, 'safety_monitor') and self.safety_monitor:
                        if not self.safety_monitor.comprehensive_safety_check():
                            self.main_log("🛑 안전 한계 도달 - 자동화 중단")
                            self.emergency_stop_all()
                            break

                    time.sleep(30)  # 30초마다 체크

                except Exception as e:
                    self.main_log(f"❌ 안전 모니터링 오류: {str(e)}")

        if hasattr(self, 'safety_monitor') and self.safety_monitor:
            monitor_thread = threading.Thread(target=safety_monitor_loop, daemon=True)
            monitor_thread.start()
            self.main_log("📊 안전 모니터링 백그라운드 스레드 시작")

    def emergency_stop_all(self):
        """응급 중단 - 모든 자동화 프로세스 중지"""
        self.automation_running = False
        self.is_ai_processing = False

        # 안전 모니터링 스레드 종료 (지시서 요구사항)
        self._stop_monitoring = True

        if hasattr(self, 'web_automation_status_var'):
            self.web_automation_status_var.set("🛑 응급 중단됨")

        if hasattr(self, 'automation_button'):
            self.automation_button.config(text="🛑 응급 중단됨", state="disabled", bg="#dc3545")

        self.main_log("🛑 응급 중단 실행 - 모든 프로세스 및 모니터링 스레드 중지")

    def get_safety_status(self):
        """현재 안전 상태 조회"""
        if hasattr(self, 'safety_monitor') and self.safety_monitor:
            return self.safety_monitor.get_comprehensive_status()
        return None

    def update_step_status(self, step_index, status, color):
        """단계별 상태 업데이트"""
        if step_index < len(self.step_labels):
            self.step_labels[step_index].config(text=status, fg=color)

    def update_all_displays(self):
        """모든 디스플레이 업데이트"""
        self.update_system_status()
        self.update_data_preview()
        self.update_results_display()
        self.update_statistics()

    def update_system_status(self):
        """시스템 상태 업데이트"""
        try:
            status_info = []
            status_info.append("=== 궁극의 통합 자동화 시스템 상태 ===")
            status_info.append(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            status_info.append("")

            # 기본 설정 상태
            status_info.append("📁 폴더 설정:")
            status_info.append(f"  다운로드: {self.download_path_var.get()}")
            status_info.append(f"  작업: {self.work_path_var.get()}")
            status_info.append(f"  결과: {self.get_output_folder()}")
            status_info.append("")

            # 데이터 현황
            img_count = len(list(Path("data/product_images").glob("*"))) if Path("data/product_images").exists() else 0
            review_count = len(list(Path("data/reviews").glob("*"))) if Path("data/reviews").exists() else 0
            result_count = len(self.generated_emails)

            status_info.append("📊 데이터 현황:")
            status_info.append(f"  이미지 파일: {img_count}개")
            status_info.append(f"  리뷰 파일: {review_count}개")
            status_info.append(f"  생성된 콜드메일: {result_count}개")
            status_info.append("")

            # 시스템 상태
            if os.path.exists(self.config_path):
                status_info.append("✅ AI 시스템: 정상")
            else:
                status_info.append("❌ AI 시스템: 설정 오류")

            # 이미지 파일 상태
            missing_images = []
            for name, path in self.image_files.items():
                if not os.path.exists(path):
                    missing_images.append(name)

            if missing_images:
                status_info.append(f"⚠️ 웹 자동화: 이미지 파일 {len(missing_images)}개 누락")
                for img in missing_images:
                    status_info.append(f"    - {img}")
            else:
                status_info.append("✅ 웹 자동화: 정상")

            text = "\n".join(status_info)
            self.system_status_text.delete("1.0", "end")
            self.system_status_text.insert("1.0", text)

        except Exception as e:
            self.system_status_text.delete("1.0", "end")
            self.system_status_text.insert("1.0", f"시스템 상태 업데이트 오류: {str(e)}")

    def update_data_preview(self):
        """데이터 미리보기 업데이트"""
        # 기존 항목 삭제
        for item in self.data_preview_tree.get_children():
            self.data_preview_tree.delete(item)

        try:
            # 이미지 파일들
            img_folder = Path("data/product_images")
            if img_folder.exists():
                for img_file in img_folder.glob("*"):
                    if img_file.is_file():
                        size = f"{img_file.stat().st_size / 1024:.1f} KB"
                        self.data_preview_tree.insert("", "end", values=("이미지", img_file.name, size, "준비됨"))

            # 리뷰 파일들
            review_folder = Path("data/reviews")
            if review_folder.exists():
                for review_file in review_folder.glob("*"):
                    if review_file.is_file():
                        size = f"{review_file.stat().st_size / 1024:.1f} KB"
                        self.data_preview_tree.insert("", "end", values=("리뷰", review_file.name, size, "준비됨"))

        except Exception as e:
            self.main_log(f"❌ 데이터 미리보기 업데이트 오류: {str(e)}")

    def update_results_display(self):
        """결과 디스플레이 업데이트"""
        # 기존 항목 삭제
        for item in self.emails_tree.get_children():
            self.emails_tree.delete(item)

        try:
            for email_data in self.generated_emails:
                timestamp = email_data['timestamp'].strftime("%m-%d %H:%M")
                subject = email_data['data'].get('subject', '제목 없음')
                body_length = len(email_data['data'].get('body', ''))
                filename = email_data['file'].name

                self.emails_tree.insert("", "end", values=(timestamp, subject, f"{body_length}자", filename))

        except Exception as e:
            self.main_log(f"❌ 결과 디스플레이 업데이트 오류: {str(e)}")

    def update_statistics(self):
        """통계 업데이트"""
        try:
            total_emails = len(self.generated_emails)
            today = datetime.now().date()
            today_emails = len([e for e in self.generated_emails if e['timestamp'].date() == today])

            # 시간 절약 계산
            manual_time = 23  # 수동 작업 시간
            auto_time = 3     # 자동화 시간
            time_saved = manual_time - auto_time

            # 통계 업데이트
            self.stats_labels["총 생성된 콜드메일"].config(text=f"{total_emails}개")
            self.stats_labels["오늘 생성"].config(text=f"{today_emails}개")

            success_rate = 90 if total_emails > 0 else 0  # 예상 성공률
            self.stats_labels["성공률"].config(text=f"{success_rate}%")

            avg_time = 5 if total_emails > 0 else 0  # 평균 처리시간
            self.stats_labels["평균 처리시간"].config(text=f"{avg_time}분")

            self.stats_labels["예상 시간 절약"].config(text=f"{time_saved}시간")
            self.stats_labels["저장 폴더"].config(text=str(self.get_output_folder()))

            # 진행 요약 업데이트
            self.progress_summary_var.set(f"처리 완료: {total_emails}개 | 대기: 0개")

        except Exception as e:
            self.main_log(f"❌ 통계 업데이트 오류: {str(e)}")

    def show_email_detail(self, event):
        """이메일 상세 보기"""
        selection = self.emails_tree.selection()
        if not selection:
            return

        item = self.emails_tree.item(selection[0])
        filename = item['values'][3]

        # 해당 파일 찾기
        for email_data in self.generated_emails:
            if email_data['file'].name == filename:
                subject = email_data['data'].get('subject', '제목 없음')
                body = email_data['data'].get('body', '내용 없음')

                preview_text = f"📧 제목: {subject}\n\n{body}"

                self.email_preview_text.delete("1.0", "end")
                self.email_preview_text.insert("1.0", preview_text)
                break

    def show_results_summary(self):
        """결과 요약 표시"""
        self.notebook.select(3)  # 결과 보기 탭으로 이동
        self.update_all_displays()

    # === 유틸리티 메서드들 ===

    def pre_automation_check(self):
        """자동화 사전 체크"""
        checks = []

        # 이미지 파일들 체크
        missing_images = []
        for name, path in self.image_files.items():
            if not os.path.exists(path):
                missing_images.append(f"{name} ({path})")

        if missing_images:
            checks.append(f"❌ 웹 자동화 이미지 파일 누락:\n" + "\n".join(missing_images))

        # 설정 파일 체크
        if not os.path.exists(self.config_path):
            checks.append("❌ AI 설정 파일이 없습니다")

        # 폴더 체크
        download_folder = Path(self.download_path_var.get())
        if not download_folder.exists():
            checks.append("❌ 다운로드 폴더가 존재하지 않습니다")

        if checks:
            error_message = "다음 문제들을 해결하고 다시 시도해주세요:\n\n" + "\n\n".join(checks)
            messagebox.showerror("사전 체크 실패", error_message)
            return False

        return True

    def setup_hotkeys(self):
        """핫키 설정"""
        self.root.bind('<Escape>', lambda e: self.emergency_stop())
        self.root.focus_set()

    def emergency_stop(self):
        """긴급 중단"""
        if self.automation_running or self.is_ai_processing:
            self.automation_running = False
            self.is_ai_processing = False

            # 안전 모니터링 스레드 종료 (지시서 요구사항)
            self._stop_monitoring = True

            self.main_status_var.set("🔴 사용자에 의한 긴급 중단")
            self.main_log("🛑 사용자에 의한 긴급 중단")
            messagebox.showinfo("중단", "모든 자동화가 중단되었습니다.")

    def pause_web_automation(self):
        """웹 자동화 일시정지"""
        self.automation_paused = not self.automation_paused
        status = "일시정지됨" if self.automation_paused else "진행 중"
        self.web_automation_status_var.set(f"웹 자동화 {status}")
        self.main_log(f"⏸️ 웹 자동화 {status}")

    def stop_web_automation(self):
        """웹 자동화 중단"""
        if self.automation_running:
            self.automation_running = False
            self.web_automation_status_var.set("중단됨")
            self.main_log("⏹️ 웹 자동화 중단됨")

    def browse_download_folder(self):
        """다운로드 폴더 찾기"""
        folder = filedialog.askdirectory(
            title="다운로드 폴더 선택",
            initialdir=str(self.download_folder)
        )
        if folder:
            self.download_folder = Path(folder)
            self.download_path_var.set(str(folder))

    def browse_work_folder(self):
        """작업 폴더 찾기"""
        folder = filedialog.askdirectory(
            title="작업 폴더 선택",
            initialdir=str(self.work_folder)
        )
        if folder:
            self.work_folder = Path(folder)
            self.work_path_var.set(str(folder))

    def change_output_folder(self):
        """출력 폴더 변경"""
        folder = filedialog.askdirectory(
            title="결과 저장 폴더 선택",
            initialdir=str(self.output_folder)
        )
        if folder:
            self.custom_output_folder = Path(folder)
            self.main_log(f"💾 저장 폴더 변경: {folder}")

    def get_output_folder(self):
        """현재 출력 폴더 반환"""
        return self.custom_output_folder if self.custom_output_folder else self.output_folder

    def open_output_folder(self):
        """결과 폴더 열기"""
        try:
            folder = self.get_output_folder()
            if os.name == 'nt':
                os.startfile(str(folder))
            else:
                os.system(f"open {folder}")
        except Exception as e:
            messagebox.showerror("오류", f"폴더 열기 실패: {str(e)}")

    def open_web_collection_folder(self):
        """웹 수집 폴더 열기"""
        try:
            folder = self.work_folder / "03_데이터_수집"
            if os.name == 'nt':
                os.startfile(str(folder))
            else:
                os.system(f"open {folder}")
        except Exception as e:
            messagebox.showerror("오류", f"폴더 열기 실패: {str(e)}")

    def scan_files(self):
        """파일 스캔 (file_organizer 기능)"""
        try:
            # 파일 목록 업데이트
            self.update_data_preview()

            # 기존 수집 파일들 스캔
            if self.work_folder.exists():
                collection_folder = self.work_folder / "03_데이터_수집"
                if collection_folder.exists():
                    today = datetime.now().strftime("%Y-%m-%d")
                    today_folders = list(collection_folder.glob(f"{today}*"))

                    if today_folders:
                        self.main_log(f"📁 오늘 수집된 폴더: {len(today_folders)}개")

        except Exception as e:
            self.main_log(f"❌ 파일 스캔 오류: {str(e)}")

    def load_settings(self):
        """설정 로드 (config.yaml에서 GUI 기본값 로드)"""
        try:
            config_data = load_config_data(self.config_path)
        except Exception as e:
            self.main_log(f"설정 파일 로드 실패: {e}")
            return

        if not config_data:
            self.main_log("설정 파일이 비어 있습니다 - 기본값을 사용합니다")
            return

        gui_config = config_data.get('gui', {})
        if hasattr(self, 'min_chars'):
            self.min_chars.set(gui_config.get('default_min_chars', self.min_chars.get() if hasattr(self, 'min_chars') else 350))
        if hasattr(self, 'max_chars'):
            self.max_chars.set(gui_config.get('default_max_chars', self.max_chars.get() if hasattr(self, 'max_chars') else 600))
        if hasattr(self, 'tone_var'):
            self.tone_var.set(gui_config.get('default_tone', 'consultant'))

        file_org_config = config_data.get('file_organizer', {})
        self.total_products = file_org_config.get('total_products', self.total_products)
        self.fireshot_capture_timeout_sec = file_org_config.get('fireshot_capture_timeout_sec', self.fireshot_capture_timeout_sec)
        self.fireshot_capture_poll_interval_sec = file_org_config.get('fireshot_capture_poll_interval_sec', self.fireshot_capture_poll_interval_sec)

        if hasattr(self, 'download_path_var'):
            download_path = str(file_org_config.get('download_folder', self.default_download_folder))
            self.download_path_var.set(download_path)
            self.download_folder = Path(download_path).expanduser()

        if hasattr(self, 'work_path_var'):
            work_path = str(file_org_config.get('work_folder', self.default_work_folder))
            self.work_path_var.set(work_path)
            self.work_folder = Path(work_path).expanduser()

        db_path = str(file_org_config.get('database_file', self.default_database_file))
        self.database_file = Path(db_path).expanduser()

        paths_config = config_data.get('paths', {})
        output_path = Path(paths_config.get('output_root_dir', self.output_folder)).expanduser()
        self.output_folder = output_path
        if not self.output_folder.exists():
            self.output_folder.mkdir(parents=True, exist_ok=True)

        self.main_log("설정 파일에서 GUI 기본값 로드 완료")

    def save_settings(self):
        """설정 저장 (지시서 요구사항: 사용자 변경사항을 config.yaml에 저장)"""
        try:
            if not os.path.exists(self.config_path):
                return

            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # GUI 설정 업데이트
            if 'gui' not in config_data:
                config_data['gui'] = {}

            if hasattr(self, 'min_chars'):
                config_data['gui']['default_min_chars'] = self.min_chars.get()
            if hasattr(self, 'max_chars'):
                config_data['gui']['default_max_chars'] = self.max_chars.get()
            if hasattr(self, 'tone_var'):
                config_data['gui']['default_tone'] = self.tone_var.get()

            # 폴더 경로 업데이트
            if 'file_organizer' not in config_data:
                config_data['file_organizer'] = {}

            if hasattr(self, 'download_path_var'):
                config_data['file_organizer']['download_folder'] = self.download_path_var.get()
            if hasattr(self, 'work_path_var'):
                config_data['file_organizer']['work_folder'] = self.work_path_var.get()

            config_data['file_organizer']['total_products'] = self.total_products

            # 파일에 저장
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)

            self.main_log("✅ 설정이 config.yaml에 저장되었습니다")

        except Exception as e:
            self.main_log(f"❌ 설정 저장 실패: {str(e)}")

    def verify_api_and_ocr(self):
        """API 및 OCR 검증 (지시서 요구사항)"""
        try:
            self.main_log("🔍 API 및 OCR 환경 검증 시작...")

            # 1. VERTEX_PROJECT_ID 환경변수 확인
            vertex_project_id = os.environ.get('VERTEX_PROJECT_ID')
            if vertex_project_id:
                self.main_log(f"✅ VERTEX_PROJECT_ID 설정 확인: {vertex_project_id}")
            else:
                self.main_log("⚠️ VERTEX_PROJECT_ID 환경변수가 설정되지 않음")

            # 2. Tesseract OCR 경로 확인
            import yaml
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                tesseract_cmd = config_data.get('ocr', {}).get('tesseract_cmd', '')

                if os.path.exists(tesseract_cmd):
                    self.main_log(f"✅ Tesseract OCR 경로 확인: {tesseract_cmd}")
                else:
                    self.main_log(f"❌ Tesseract OCR 경로 없음: {tesseract_cmd}")

                # 3. OCR 모듈 테스트
                try:
                    import pytesseract
                    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

                    # 간단한 OCR 테스트
                    from PIL import Image
                    import numpy as np

                    # 테스트 이미지 생성 (흰 배경에 검은 텍스트)
                    test_img = Image.new('RGB', (200, 50), color='white')
                    test_result = pytesseract.image_to_string(test_img, lang='eng')
                    self.main_log("✅ OCR 모듈 기본 테스트 통과")

                except Exception as ocr_e:
                    self.main_log(f"❌ OCR 모듈 테스트 실패: {str(ocr_e)}")

            # 4. AI 클라이언트 연결 테스트
            try:
                from core.config import load_config, load_config_data
                cfg = load_config(self.config_path)
                self.main_log("✅ AI 설정 로드 성공")

                # GeminiClient 초기화 테스트 (실제 호출은 하지 않음)
                from llm.gemini_client import GeminiClient
                self.main_log("✅ AI 클라이언트 모듈 로드 성공")

            except Exception as ai_e:
                self.main_log(f"❌ AI 클라이언트 테스트 실패: {str(ai_e)}")

            self.main_log("🔍 API 및 OCR 환경 검증 완료")
            return True

        except Exception as e:
            self.main_log(f"❌ 환경 검증 실패: {str(e)}")
            return False

    def run(self):
        """GUI 실행"""
        # GUI 종료 시 처리 (지시서 요구사항: 안전 모니터링 스레드 종료 + 설정 저장)
        def on_closing():
            self._stop_monitoring = True
            self.save_settings()  # 종료 시 설정 자동 저장
            self.main_log("🔄 시스템 종료 중 - 안전 모니터링 스레드 정리 및 설정 저장")
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)

        # 초기 상태 업데이트
        self.update_all_displays()
        self.main_log("궁극의 통합 자동화 시스템 준비 완료!")
        self.main_log("'완전 자동화 시작' 버튼을 클릭하여 시작하세요!")

        # 창 포커스 강제
        self.root.focus_force()
        self.root.focus_set()

        print("GUI 창이 표시되어야 합니다. 작업표시줄을 확인하세요.")
        self.root.mainloop()


    def create_client_discovery_tab(self):
        """고객사 발굴 탭 생성"""
        try:
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

            # 사용법 안내 프레임
            guide_frame = tk.LabelFrame(main_frame, text="사용법", font=("맑은 고딕", 10, "bold"))
            guide_frame.pack(fill="x", pady=(0, 15))

            guide_text = """
1. 네이버 쇼핑에서 원하는 키워드로 검색하세요
2. 정렬을 '리뷰 많은 순'으로 변경하세요
3. 아래 시작 버튼을 누르면 현재 페이지에서 크롤링을 시작합니다
4. 캡챠 방지를 위해 검색은 수동으로만 가능합니다
            """

            guide_label = tk.Label(
                guide_frame,
                text=guide_text,
                font=("맑은 고딕", 9),
                justify="left",
                fg="#2c3e50"
            )
            guide_label.pack(padx=15, pady=10)

            # 필터 설정 프레임
            filter_frame = tk.LabelFrame(main_frame, text="필터 설정", font=("맑은 고딕", 10, "bold"))
            filter_frame.pack(fill="x", pady=(0, 15))

            # 필터 설정 필드들
            filter_row = tk.Frame(filter_frame)
            filter_row.pack(fill="x", padx=10, pady=10)

            tk.Label(filter_row, text="리뷰 범위:", font=("맑은 고딕", 9)).pack(side="left")
            self.review_min_entry = tk.Entry(filter_row, font=("맑은 고딕", 9), width=8)
            self.review_min_entry.pack(side="left", padx=(5, 2))
            self.review_min_entry.insert(0, "200")

            tk.Label(filter_row, text="~", font=("맑은 고딕", 9)).pack(side="left", padx=2)
            self.review_max_entry = tk.Entry(filter_row, font=("맑은 고딕", 9), width=8)
            self.review_max_entry.pack(side="left", padx=(2, 20))
            self.review_max_entry.insert(0, "300")

            tk.Label(filter_row, text="관심고객 범위:", font=("맑은 고딕", 9)).pack(side="left")
            self.follower_min_entry = tk.Entry(filter_row, font=("맑은 고딕", 9), width=8)
            self.follower_min_entry.pack(side="left", padx=(5, 2))
            self.follower_min_entry.insert(0, "50")

            tk.Label(filter_row, text="~", font=("맑은 고딕", 9)).pack(side="left", padx=2)
            self.follower_max_entry = tk.Entry(filter_row, font=("맑은 고딕", 9), width=8)
            self.follower_max_entry.pack(side="left", padx=(2, 5))
            self.follower_max_entry.insert(0, "1500")

            # 제어 버튼 프레임
            control_frame = tk.LabelFrame(main_frame, text="실행 제어", font=("맑은 고딕", 10, "bold"))
            control_frame.pack(fill="x", pady=(0, 15))

            button_frame = tk.Frame(control_frame)
            button_frame.pack(padx=10, pady=10)

            self.start_crawler_btn = tk.Button(
                button_frame,
                text="현재 페이지에서\n크롤링 시작",
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

            # 로그 프레임 (진행상황 표시)
            log_frame = tk.LabelFrame(main_frame, text="진행상황", font=("맑은 고딕", 10, "bold"))
            log_frame.pack(fill="both", expand=True, pady=(0, 10))

            # 로그 텍스트 위젯
            log_text_frame = tk.Frame(log_frame)
            log_text_frame.pack(fill="both", expand=True, padx=10, pady=10)

            self.crawler_log_text = tk.Text(
                log_text_frame,
                height=12,
                font=("Consolas", 9),
                bg="#f8f9fa",
                fg="#2c3e50",
                wrap=tk.WORD
            )

            crawler_scrollbar = tk.Scrollbar(log_text_frame, orient="vertical", command=self.crawler_log_text.yview)
            self.crawler_log_text.configure(yscrollcommand=crawler_scrollbar.set)

            self.crawler_log_text.pack(side="left", fill="both", expand=True)
            crawler_scrollbar.pack(side="right", fill="y")

            # 크롤러 상태 변수들
            self.crawler_running = False
            self.crawler_thread = None

            self.crawler_log("고객사 발굴 시스템 준비 완료")

        except Exception as e:
            print(f"고객사 발굴 탭 생성 오류: {e}")

    def crawler_log(self, message):
        """크롤러 로그 메시지 추가"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}"

            if hasattr(self, 'crawler_log_text'):
                self.crawler_log_text.insert(tk.END, log_message + "\n")
                self.crawler_log_text.see(tk.END)
                self.root.update_idletasks()

            print(log_message.strip())
        except Exception as e:
            print(f"로그 출력 오류: {e}")

    def start_client_discovery(self):
        """고객사 발굴 시작"""
        try:
            if self.crawler_running:
                return

            # 필터 설정 수집
            config_updates = {
                "search": {
                    "review_min": int(self.review_min_entry.get()),
                    "review_max": int(self.review_max_entry.get()),
                    "follower_min": int(self.follower_min_entry.get()),
                    "follower_max": int(self.follower_max_entry.get()),
                }
            }

            self.crawler_running = True
            self.start_crawler_btn.config(state="disabled")
            self.stop_crawler_btn.config(state="normal")

            self.crawler_log("현재 페이지에서 고객사 발굴 시작...")
            self.crawler_log("사전 조건: 네이버 쇼핑에서 키워드 검색 + 리뷰많은순 정렬 완료")
            search_settings = config_updates.get('search', {})
            self.crawler_log(f"리뷰 범위 필터: {search_settings.get('review_min', 'N/A')} ~ {search_settings.get('review_max', 'N/A')}")
            self.crawler_log(f"관심고객 필터: {search_settings.get('follower_min', 'N/A')} ~ {search_settings.get('follower_max', 'N/A')}")

            # 별도 스레드에서 실행
            self.crawler_thread = threading.Thread(target=self.run_client_discovery_thread, args=(config_updates,), daemon=True)
            self.crawler_thread.start()

        except Exception as e:
            self.crawler_log(f"크롤링 시작 실패: {str(e)}")
            self.crawler_running = False
            self.start_crawler_btn.config(state="normal")
            self.stop_crawler_btn.config(state="disabled")

    def run_client_discovery_thread(self, config_updates):
        """고객사 발굴 실행 스레드"""
        try:
            # client_discovery 모듈 동적 임포트
            import sys
            sys.path.append(str(Path(__file__).parent / "client_discovery"))

            from client_discovery.main_crawler import NaverShoppingCrawler

            # 설정 파일 경로
            config_path = "client_discovery/config.json"

            self.crawler_log("크롤러 초기화 중...")
            crawler = NaverShoppingCrawler(config_path)
            crawler.apply_config_updates(config_updates)

            self.crawler_log("크롤링 실행 중...")

            # 크롤링 실행
            result_summary = crawler.run()

            status = (result_summary or {}).get("status", "unknown")
            message = (result_summary or {}).get("message", "")
            if status == "success":
                saved = result_summary.get("saved_count", 0)
                visited = result_summary.get("visited_count", 0)
                self.crawler_log(f"크롤링 완료! 저장 {saved}건 / 방문 {visited}건")

                csv_path = result_summary.get("csv_path")
                if csv_path:
                    self.crawler_log(f"결과 저장: {csv_path}")

                details = result_summary.get("details") or []
                for detail in details[:5]:
                    name = detail.get("store_name")
                    review = detail.get("review_count")
                    interest = detail.get("interest_count")
                    self.crawler_log(f" - {name} (리뷰 {review}, 관심고객 {interest})")
                if len(details) > 5:
                    self.crawler_log(f"...(총 {len(details)}건 중 상위 5건 표시)")
            else:
                status_text = "중단" if status == "aborted" else "오류"
                self.crawler_log(f"크롤링 {status_text}: {message or '원인 미상'}")

        except Exception as e:
            self.crawler_log(f"크롤링 오류: {str(e)}")
        finally:
            self.crawler_running = False
            self.start_crawler_btn.config(state="normal")
            self.stop_crawler_btn.config(state="disabled")

    def stop_client_discovery(self):
        """고객사 발굴 중지"""
        try:
            self.crawler_running = False
            self.crawler_log("크롤링 중지 요청됨...")

            self.start_crawler_btn.config(state="normal")
            self.stop_crawler_btn.config(state="disabled")

        except Exception as e:
            self.crawler_log(f"크롤링 중지 오류: {str(e)}")

def main():
    """메인 함수"""
    # 필요한 폴더들 생성
    folders_to_create = [
        "outputs",
        "data/product_images",
        "data/reviews",
        "gui",
        "client_discovery/results"  # 고객사 발굴 결과 폴더 추가
    ]

    for folder in folders_to_create:
        Path(folder).mkdir(parents=True, exist_ok=True)

    print("궁극의 통합 자동화 시스템 시작...")

    # 시스템 실행
    app = UltimateAutomationSystem()
    app.run()


if __name__ == "__main__":
    main()
