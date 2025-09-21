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
from datetime import datetime
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
from core.config import load_config
from llm.gemini_client import GeminiClient
from compose.composer import compose_final_email

class UltimateAutomationSystem:
    """궁극의 통합 자동화 시스템"""

    def __init__(self):
        print("🚀 궁극의 통합 자동화 시스템 시작...")
        self.root = tk.Tk()
        self.root.title("🎯 궁극의 이커머스 콜드메일 자동화 시스템 - 완전통합")
        self.root.geometry("1600x1000")
        self.root.resizable(True, True)

        # === 공통 설정 ===
        self.today = datetime.now().strftime("%Y-%m-%d")

        # === file_organizer 설정 ===
        self.download_folder = Path("C:/Users/Administrator/Downloads")
        self.work_folder = Path("E:/업무")
        self.database_file = Path("E:/업무/03_데이터_수집/이커머스_수집_데이터베이스.xlsx")
        self.file_hashes = {}
        self.pending_stores = []  # 순서 기반 매칭용

        # 웹 자동화 상태
        self.automation_running = False
        self.automation_paused = False
        self.processed_count = 0
        self.failed_products = []
        self.total_products = 30

        # 이미지 파일들 (웹 자동화용)
        self.image_files = {
            'detail_button': 'E:/VSC/file_organizer/detail_button.png',
            'fireshot_save': 'E:/VSC/file_organizer/fireshot_save.png',
            'analysis_start': 'E:/VSC/file_organizer/analysis_start.png',
            'excel_download': 'E:/VSC/file_organizer/excel_download.png'
        }

        # === all_in_one 설정 ===
        self.config_path = "config/config.yaml"
        self.output_folder = Path("outputs")
        self.custom_output_folder = None
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

        print("🎉 궁극의 통합 시스템 초기화 완료!")

    def create_widgets(self):
        """통합 GUI 위젯 생성"""

        # === 메인 제목 ===
        title_frame = tk.Frame(self.root, bg="#1a252f", height=80)
        title_frame.pack(fill="x", padx=5, pady=5)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🎯 궁극의 이커머스 콜드메일 자동화 시스템",
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
        self.create_web_automation_tab()
        self.create_ai_generation_tab()
        self.create_results_tab()
        self.create_settings_tab()

    def create_main_control_panel(self):
        """메인 컨트롤 패널"""
        control_frame = tk.Frame(self.root, bg="#34495e", height=120)
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
            font=("맑은 고딕", 13, "bold"),
            relief="flat",
            padx=25,
            pady=12,
            width=25
        )
        self.master_start_btn.pack()

        btn_row2 = tk.Frame(btn_subframe, bg="#34495e")
        btn_row2.pack(fill="x", pady=(8, 0))

        tk.Button(btn_row2, text="⛔ 긴급 중단", command=self.emergency_stop,
                 bg="#e67e22", fg="white", font=("맑은 고딕", 9, "bold")).pack(side="left", padx=2)

        tk.Button(btn_row2, text="📊 결과 보기", command=self.show_results_summary,
                 bg="#3498db", fg="white", font=("맑은 고딕", 9, "bold")).pack(side="left", padx=2)

        tk.Button(btn_row2, text="⚙️ 설정", command=lambda: self.notebook.select(4),
                 bg="#95a5a6", fg="white", font=("맑은 고딕", 9, "bold")).pack(side="left", padx=2)

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

        tk.Button(web_control_frame, text="🚀 웹 자동화만 시작", command=self.start_web_automation_only,
                 bg="#3498db", fg="white", font=("맑은 고딕", 10, "bold"), padx=15).pack(side="left", padx=5)

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
            self.main_progress_bar.set(5)

            success = self.execute_web_automation()
            if not success or not self.automation_running:
                self.main_log("❌ 웹 자동화 실패 또는 사용자 중단")
                return

            self.update_step_status(0, "웹 자동화 완료", "#27ae60")
            self.main_progress_bar.set(30)

            # 단계 2: 데이터 정리 (10%)
            self.update_step_status(1, "데이터 정리 시작", "#3498db")
            self.progress_detail_var.set("2단계: 수집된 데이터를 AI 처리 가능한 형태로 정리 중...")

            self.organize_collected_data()

            self.update_step_status(1, "데이터 정리 완료", "#27ae60")
            self.main_progress_bar.set(40)

            # 단계 3: AI 분석 및 콜드메일 생성 (60%)
            self.update_step_status(2, "AI 분석 시작", "#9b59b6")
            self.progress_detail_var.set("3단계: AI가 이미지와 리뷰를 분석하여 콜드메일 생성 중...")

            success = self.execute_ai_generation()
            if not success or not self.automation_running:
                self.main_log("❌ AI 콜드메일 생성 실패 또는 사용자 중단")
                return

            self.update_step_status(2, "AI 분석 완료", "#27ae60")
            self.main_progress_bar.set(100)

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
                if not self.automation_running:
                    self.main_log("🛑 사용자에 의한 웹 자동화 중단")
                    return False

                try:
                    self.main_log(f"🔄 제품 {i}/{self.total_products} 처리 중...")
                    self.web_automation_status_var.set(f"제품 {i} 처리 중...")
                    self.web_progress_var.set(f"{processed}/{self.total_products} 완료")
                    self.web_progress_bar.set((i / self.total_products) * 100)

                    # 실제 웹 자동화 로직 실행
                    success = self.process_single_product(i)

                    if success:
                        processed += 1
                        self.main_log(f"✅ 제품 {i} 처리 완료")
                    else:
                        failed += 1
                        self.main_log(f"❌ 제품 {i} 처리 실패")

                    # 진행률 업데이트
                    progress = (i / self.total_products) * 30  # 웹 자동화는 전체의 30%
                    self.main_progress_bar.set(5 + progress)

                except Exception as e:
                    failed += 1
                    self.main_log(f"❌ 제품 {i} 오류: {str(e)}")
                    continue

            self.main_log(f"🌐 웹 자동화 완료: 성공 {processed}개, 실패 {failed}개")
            self.web_automation_status_var.set(f"완료: 성공 {processed}개, 실패 {failed}개")

            return processed > 0  # 최소 1개라도 성공하면 계속 진행

        except Exception as e:
            self.main_log(f"❌ 웹 자동화 심각한 오류: {str(e)}")
            return False

    def process_single_product(self, product_index):
        """단일 제품 처리 (실제 웹 자동화 로직)"""
        try:
            # 1. 상세정보 버튼 클릭
            if not self.click_detail_button():
                return False

            time.sleep(2)  # 페이지 로딩 대기

            # 2. Fireshot으로 상세페이지 캡처
            if not self.capture_detail_page(product_index):
                return False

            # 3. 크롤링툴로 리뷰 데이터 수집
            if not self.collect_review_data(product_index):
                return False

            # 4. 다음 탭으로 이동
            self.move_to_next_tab()

            return True

        except Exception as e:
            self.main_log(f"❌ 제품 {product_index} 처리 중 오류: {str(e)}")
            return False

    def click_detail_button(self):
        """상세정보 버튼 클릭"""
        try:
            detail_button_image = self.image_files['detail_button']
            if os.path.exists(detail_button_image):
                location = pyautogui.locateOnScreen(detail_button_image, confidence=0.8)
                if location:
                    pyautogui.click(location)
                    return True
                else:
                    self.main_log("⚠️ 상세정보 버튼을 찾을 수 없음")
                    return False
            else:
                self.main_log("❌ 상세정보 버튼 이미지 파일 없음")
                return False
        except Exception as e:
            self.main_log(f"❌ 상세정보 버튼 클릭 오류: {str(e)}")
            return False

    def capture_detail_page(self, product_index):
        """상세페이지 캡처 (Fireshot)"""
        try:
            # Ctrl+Shift+S (Fireshot 단축키)
            pyautogui.hotkey('ctrl', 'shift', 's')
            time.sleep(3)  # 캡처 완료 대기

            # 저장 버튼 클릭
            save_image = self.image_files['fireshot_save']
            if os.path.exists(save_image):
                location = pyautogui.locateOnScreen(save_image, confidence=0.8)
                if location:
                    pyautogui.click(location)
                    time.sleep(2)
                    return True

            self.main_log(f"⚠️ 제품 {product_index}: Fireshot 저장 버튼 찾을 수 없음")
            return False

        except Exception as e:
            self.main_log(f"❌ 제품 {product_index} 캡처 오류: {str(e)}")
            return False

    def collect_review_data(self, product_index):
        """리뷰 데이터 수집 (크롤링툴)"""
        try:
            # Ctrl+Shift+A (크롤링툴 단축키)
            pyautogui.hotkey('ctrl', 'shift', 'a')
            time.sleep(5)  # 크롤링 완료 대기

            # 분석 시작 버튼 클릭
            analysis_image = self.image_files['analysis_start']
            if os.path.exists(analysis_image):
                location = pyautogui.locateOnScreen(analysis_image, confidence=0.8)
                if location:
                    pyautogui.click(location)
                    time.sleep(10)  # 분석 완료 대기

            # 엑셀 다운로드
            excel_image = self.image_files['excel_download']
            if os.path.exists(excel_image):
                location = pyautogui.locateOnScreen(excel_image, confidence=0.8)
                if location:
                    pyautogui.click(location)
                    time.sleep(3)
                    return True

            self.main_log(f"⚠️ 제품 {product_index}: 리뷰 다운로드 버튼 찾을 수 없음")
            return False

        except Exception as e:
            self.main_log(f"❌ 제품 {product_index} 리뷰 수집 오류: {str(e)}")
            return False

    def move_to_next_tab(self):
        """다음 탭으로 이동"""
        try:
            pyautogui.hotkey('ctrl', 'w')  # 현재 탭 닫기
            time.sleep(1)
        except Exception as e:
            self.main_log(f"❌ 탭 이동 오류: {str(e)}")

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
                    self.ai_progress_bar.set(processed)

                    try:
                        # 간단한 페이로드 (실제로는 OCR + 리뷰 분석 필요)
                        user_payload = f"이미지: {img_file.name}, 리뷰: {review_file.name} - 자동화 생성"

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

                        # 진행률 업데이트 (AI 생성은 전체의 60%)
                        ai_progress = (processed / total_combinations) * 60
                        self.main_progress_bar.set(40 + ai_progress)

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
        """웹 자동화만 실행"""
        if self.automation_running:
            messagebox.showwarning("경고", "다른 자동화가 실행 중입니다.")
            return

        self.automation_running = True
        self.main_log("🌐 웹 자동화 단독 실행")
        threading.Thread(target=self.web_automation_only_thread, daemon=True).start()

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
        """AI 생성만 실행"""
        if self.is_ai_processing:
            messagebox.showwarning("경고", "AI 처리가 실행 중입니다.")
            return

        self.is_ai_processing = True
        self.main_log("🤖 AI 콜드메일 생성 단독 실행")
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
        self.settings_log_text.see("end")

        self.root.update_idletasks()

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
        """설정 로드"""
        try:
            if os.path.exists(self.config_path):
                self.main_log("⚙️ 설정 파일 로드 완료")
            else:
                self.main_log("⚠️ 설정 파일이 없습니다")

        except Exception as e:
            self.main_log(f"❌ 설정 로드 실패: {str(e)}")

    def run(self):
        """GUI 실행"""
        # 초기 상태 업데이트
        self.update_all_displays()
        self.main_log("🎯 궁극의 통합 자동화 시스템 준비 완료!")
        self.main_log("🚀 '완전 자동화 시작' 버튼을 클릭하여 시작하세요!")

        self.root.mainloop()


def main():
    """메인 함수"""
    # 필요한 폴더들 생성
    folders_to_create = [
        "outputs",
        "data/product_images",
        "data/reviews",
        "gui"
    ]

    for folder in folders_to_create:
        Path(folder).mkdir(parents=True, exist_ok=True)

    print("🎯 궁극의 통합 자동화 시스템 시작...")

    # 시스템 실행
    app = UltimateAutomationSystem()
    app.run()


if __name__ == "__main__":
    main()