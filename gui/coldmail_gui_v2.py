#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 콜드메일 자동생성 시스템 GUI v2.0
- 저장 폴더 변경 기능 추가
- 파일 정리 기능 추가
- 기존 GUI 자동화 연동 기능 추가
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import threading
import asyncio
from datetime import datetime
from pathlib import Path
import sys
import shutil
import glob

# 상위 디렉토리를 Python 경로에 추가 (모듈 import용)
sys.path.append(str(Path(__file__).parent.parent))

from core.config import load_config
from llm.gemini_client import GeminiClient
from compose.composer import compose_final_email

class ColdMailGeneratorGUI:
    def __init__(self):
        print("AI 콜드메일 GUI v2.0 시작...")
        self.root = tk.Tk()
        self.root.title("AI 콜드메일 자동생성 시스템 v2.0 - 고급 기능")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        # 기본 설정
        self.config_path = "config/config.yaml"
        self.output_folder = Path("outputs")
        self.custom_output_folder = None  # 사용자 지정 저장 폴더
        self.selected_images = []
        self.selected_reviews = []
        self.is_processing = False

        # 결과 저장용
        self.generated_emails = []

        # 파일 정리 설정
        self.auto_organize = tk.BooleanVar(value=False)
        self.source_folder = Path("C:/Users/Administrator/Downloads")  # 기본 다운로드 폴더

        print("GUI 위젯 생성 중...")
        self.create_widgets()
        self.load_settings()

        print("GUI v2.0 초기화 완료!")

    def create_widgets(self):
        """GUI 위젯들을 생성"""

        # 메인 제목
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill="x", padx=5, pady=5)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🤖 AI 콜드메일 자동생성 시스템 v2.0",
            font=("맑은 고딕", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)

        # 탭 컨테이너 생성
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # 탭 1: 콜드메일 생성
        self.create_main_tab()

        # 탭 2: 파일 관리
        self.create_file_management_tab()

        # 탭 3: 설정
        self.create_settings_tab()

    def create_main_tab(self):
        """메인 콜드메일 생성 탭"""
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="🚀 콜드메일 생성")

        # 메인 컨테이너
        main_frame = tk.Frame(main_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 좌측 패널 (파일 선택)
        left_frame = tk.LabelFrame(main_frame, text="📁 파일 선택", font=("맑은 고딕", 12, "bold"))
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # 상품 이미지 선택
        img_frame = tk.Frame(left_frame)
        img_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(img_frame, text="상품 상세페이지 이미지:", font=("맑은 고딕", 10, "bold")).pack(anchor="w")

        img_btn_frame = tk.Frame(img_frame)
        img_btn_frame.pack(fill="x", pady=5)

        self.img_select_btn = tk.Button(
            img_btn_frame,
            text="📷 이미지 파일 선택",
            command=self.select_images,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 9, "bold"),
            relief="flat",
            padx=20
        )
        self.img_select_btn.pack(side="left")

        # 폴더에서 자동 스캔 버튼 추가
        self.img_scan_btn = tk.Button(
            img_btn_frame,
            text="🔍 폴더 스캔",
            command=self.scan_images_folder,
            bg="#9b59b6",
            fg="white",
            font=("맑은 고딕", 9, "bold"),
            relief="flat"
        )
        self.img_scan_btn.pack(side="left", padx=(5, 0))

        self.img_count_label = tk.Label(img_btn_frame, text="선택된 이미지: 0개", font=("맑은 고딕", 9))
        self.img_count_label.pack(side="left", padx=(10, 0))

        # 선택된 이미지 목록
        self.img_listbox = tk.Listbox(img_frame, height=4, font=("맑은 고딕", 9))
        self.img_listbox.pack(fill="x", pady=5)

        # 리뷰 파일 선택
        review_frame = tk.Frame(left_frame)
        review_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(review_frame, text="고객 리뷰 파일:", font=("맑은 고딕", 10, "bold")).pack(anchor="w")

        review_btn_frame = tk.Frame(review_frame)
        review_btn_frame.pack(fill="x", pady=5)

        self.review_select_btn = tk.Button(
            review_btn_frame,
            text="📊 CSV/Excel 파일 선택",
            command=self.select_reviews,
            bg="#27ae60",
            fg="white",
            font=("맑은 고딕", 9, "bold"),
            relief="flat",
            padx=20
        )
        self.review_select_btn.pack(side="left")

        # 리뷰 폴더 스캔 버튼
        self.review_scan_btn = tk.Button(
            review_btn_frame,
            text="🔍 폴더 스캔",
            command=self.scan_reviews_folder,
            bg="#9b59b6",
            fg="white",
            font=("맑은 고딕", 9, "bold"),
            relief="flat"
        )
        self.review_scan_btn.pack(side="left", padx=(5, 0))

        self.review_count_label = tk.Label(review_btn_frame, text="선택된 파일: 0개", font=("맑은 고딕", 9))
        self.review_count_label.pack(side="left", padx=(10, 0))

        # 선택된 리뷰 파일 목록
        self.review_listbox = tk.Listbox(review_frame, height=4, font=("맑은 고딕", 9))
        self.review_listbox.pack(fill="x", pady=5)

        # 저장 설정
        save_frame = tk.LabelFrame(left_frame, text="💾 저장 설정", font=("맑은 고딕", 10, "bold"))
        save_frame.pack(fill="x", padx=10, pady=5)

        save_btn_frame = tk.Frame(save_frame)
        save_btn_frame.pack(fill="x", padx=5, pady=3)

        tk.Label(save_btn_frame, text="저장 폴더:", font=("맑은 고딕", 9)).pack(side="left")

        self.change_output_btn = tk.Button(
            save_btn_frame,
            text="📁 폴더 변경",
            command=self.change_output_folder,
            bg="#f39c12",
            fg="white",
            font=("맑은 고딕", 8),
            relief="flat"
        )
        self.change_output_btn.pack(side="right")

        self.output_path_label = tk.Label(save_frame, text=f"현재: {self.output_folder}",
                                        font=("맑은 고딕", 8), fg="#7f8c8d", wraplength=300)
        self.output_path_label.pack(anchor="w", padx=5)

        # 우측 패널 (실행 및 결과)
        right_frame = tk.LabelFrame(main_frame, text="🚀 실행 및 결과", font=("맑은 고딕", 12, "bold"))
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # 실행 버튼
        exec_frame = tk.Frame(right_frame)
        exec_frame.pack(fill="x", padx=10, pady=10)

        self.generate_btn = tk.Button(
            exec_frame,
            text="✨ 콜드메일 생성 시작",
            command=self.start_generation,
            bg="#e74c3c",
            fg="white",
            font=("맑은 고딕", 12, "bold"),
            relief="flat",
            padx=30,
            pady=10
        )
        self.generate_btn.pack()

        # 진행상황
        progress_frame = tk.Frame(right_frame)
        progress_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(progress_frame, text="진행상황:", font=("맑은 고딕", 10, "bold")).pack(anchor="w")

        self.progress_var = tk.StringVar(value="대기 중...")
        self.progress_label = tk.Label(progress_frame, textvariable=self.progress_var,
                                     font=("맑은 고딕", 9), fg="#7f8c8d")
        self.progress_label.pack(anchor="w")

        self.progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=5)

        # 로그 출력
        log_frame = tk.Frame(right_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(log_frame, text="실행 로그:", font=("맑은 고딕", 10, "bold")).pack(anchor="w")

        # 스크롤바가 있는 텍스트 위젯
        log_scroll_frame = tk.Frame(log_frame)
        log_scroll_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_scroll_frame, font=("Consolas", 9), wrap="word",
                               bg="#f8f9fa", fg="#2c3e50")
        log_scrollbar = tk.Scrollbar(log_scroll_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")

        # 하단 버튼들
        bottom_frame = tk.Frame(right_frame)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        self.open_output_btn = tk.Button(
            bottom_frame,
            text="📁 결과 폴더 열기",
            command=self.open_output_folder,
            bg="#95a5a6",
            fg="white",
            font=("맑은 고딕", 9),
            relief="flat"
        )
        self.open_output_btn.pack(side="left")

        self.clear_log_btn = tk.Button(
            bottom_frame,
            text="🗑️ 로그 지우기",
            command=self.clear_log,
            bg="#95a5a6",
            fg="white",
            font=("맑은 고딕", 9),
            relief="flat"
        )
        self.clear_log_btn.pack(side="left", padx=(5, 0))

        self.test_btn = tk.Button(
            bottom_frame,
            text="🧪 스모크 테스트",
            command=self.run_smoke_test,
            bg="#f39c12",
            fg="white",
            font=("맑은 고딕", 9),
            relief="flat"
        )
        self.test_btn.pack(side="right")

    def create_file_management_tab(self):
        """파일 관리 탭"""
        file_tab = ttk.Frame(self.notebook)
        self.notebook.add(file_tab, text="📂 파일 관리")

        # 파일 정리 섹션
        organize_frame = tk.LabelFrame(file_tab, text="🗂️ 파일 자동 정리", font=("맑은 고딕", 12, "bold"))
        organize_frame.pack(fill="x", padx=10, pady=5)

        # 소스 폴더 설정
        source_frame = tk.Frame(organize_frame)
        source_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(source_frame, text="정리할 폴더:", font=("맑은 고딕", 10, "bold")).pack(anchor="w")

        source_btn_frame = tk.Frame(source_frame)
        source_btn_frame.pack(fill="x", pady=3)

        self.source_path_var = tk.StringVar(value=str(self.source_folder))
        source_entry = tk.Entry(source_btn_frame, textvariable=self.source_path_var, font=("맑은 고딕", 9))
        source_entry.pack(side="left", fill="x", expand=True)

        source_browse_btn = tk.Button(
            source_btn_frame,
            text="찾아보기",
            command=self.browse_source_folder,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 8),
            relief="flat"
        )
        source_browse_btn.pack(side="right", padx=(5, 0))

        # 정리 옵션들
        options_frame = tk.Frame(organize_frame)
        options_frame.pack(fill="x", padx=10, pady=5)

        self.auto_organize = tk.BooleanVar()
        auto_check = tk.Checkbutton(
            options_frame,
            text="파일 선택 시 자동으로 정리된 파일 찾기",
            variable=self.auto_organize,
            font=("맑은 고딕", 9)
        )
        auto_check.pack(anchor="w")

        # 정리 실행 버튼들
        organize_btn_frame = tk.Frame(organize_frame)
        organize_btn_frame.pack(fill="x", padx=10, pady=5)

        self.scan_files_btn = tk.Button(
            organize_btn_frame,
            text="🔍 파일 스캔",
            command=self.scan_source_files,
            bg="#27ae60",
            fg="white",
            font=("맑은 고딕", 10, "bold"),
            relief="flat",
            padx=20
        )
        self.scan_files_btn.pack(side="left")

        self.organize_files_btn = tk.Button(
            organize_btn_frame,
            text="🗂️ 파일 정리 실행",
            command=self.organize_files,
            bg="#e67e22",
            fg="white",
            font=("맑은 고딕", 10, "bold"),
            relief="flat",
            padx=20
        )
        self.organize_files_btn.pack(side="left", padx=(10, 0))

        # 파일 목록 표시
        files_frame = tk.LabelFrame(file_tab, text="📋 발견된 파일들", font=("맑은 고딕", 12, "bold"))
        files_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 트리뷰로 파일 목록 표시
        self.files_tree = ttk.Treeview(files_frame, columns=("type", "name", "size", "date"), show="headings")
        self.files_tree.heading("type", text="유형")
        self.files_tree.heading("name", text="파일명")
        self.files_tree.heading("size", text="크기")
        self.files_tree.heading("date", text="수정일")

        self.files_tree.column("type", width=80)
        self.files_tree.column("name", width=300)
        self.files_tree.column("size", width=80)
        self.files_tree.column("date", width=120)

        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scrollbar.set)

        self.files_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        files_scrollbar.pack(side="right", fill="y", pady=5)

    def create_settings_tab(self):
        """설정 탭"""
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="⚙️ 설정")

        # AI 설정
        ai_frame = tk.LabelFrame(settings_tab, text="🤖 AI 설정", font=("맑은 고딕", 12, "bold"))
        ai_frame.pack(fill="x", padx=10, pady=5)

        # 톤앤매너 선택
        tone_frame = tk.Frame(ai_frame)
        tone_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(tone_frame, text="톤앤매너:", font=("맑은 고딕", 10)).pack(side="left")
        self.tone_var = tk.StringVar(value="consultant")
        tone_combo = ttk.Combobox(tone_frame, textvariable=self.tone_var,
                                 values=["consultant", "student"], width=15, state="readonly")
        tone_combo.pack(side="left", padx=(5, 0))

        # 이메일 길이 설정
        length_frame = tk.Frame(ai_frame)
        length_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(length_frame, text="이메일 길이:", font=("맑은 고딕", 10)).pack(anchor="w")

        length_input_frame = tk.Frame(length_frame)
        length_input_frame.pack(fill="x", pady=3)

        tk.Label(length_input_frame, text="최소 글자수:", font=("맑은 고딕", 9)).pack(side="left")
        self.min_chars = tk.IntVar(value=350)
        tk.Spinbox(length_input_frame, from_=200, to=500, textvariable=self.min_chars, width=8).pack(side="left", padx=(5, 20))

        tk.Label(length_input_frame, text="최대 글자수:", font=("맑은 고딕", 9)).pack(side="left")
        self.max_chars = tk.IntVar(value=600)
        tk.Spinbox(length_input_frame, from_=400, to=800, textvariable=self.max_chars, width=8).pack(side="left", padx=(5, 0))

        # 기존 GUI 자동화 연동
        integration_frame = tk.LabelFrame(settings_tab, text="🔗 기존 시스템 연동", font=("맑은 고딕", 12, "bold"))
        integration_frame.pack(fill="x", padx=10, pady=5)

        gui_auto_frame = tk.Frame(integration_frame)
        gui_auto_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(gui_auto_frame, text="GUI 자동화 프로그램:", font=("맑은 고딕", 10)).pack(anchor="w")

        gui_auto_btn_frame = tk.Frame(gui_auto_frame)
        gui_auto_btn_frame.pack(fill="x", pady=3)

        self.launch_gui_auto_btn = tk.Button(
            gui_auto_btn_frame,
            text="🕹️ GUI 자동화 실행",
            command=self.launch_gui_automation,
            bg="#9b59b6",
            fg="white",
            font=("맑은 고딕", 10, "bold"),
            relief="flat",
            padx=20
        )
        self.launch_gui_auto_btn.pack(side="left")

        self.sync_files_btn = tk.Button(
            gui_auto_btn_frame,
            text="🔄 파일 동기화",
            command=self.sync_with_gui_automation,
            bg="#1abc9c",
            fg="white",
            font=("맑은 고딕", 10, "bold"),
            relief="flat",
            padx=20
        )
        self.sync_files_btn.pack(side="left", padx=(10, 0))

        # 상태 정보
        status_frame = tk.LabelFrame(settings_tab, text="📊 상태 정보", font=("맑은 고딕", 12, "bold"))
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.status_text = tk.Text(status_frame, font=("Consolas", 9), bg="#f8f9fa", fg="#2c3e50")
        status_scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)

        self.status_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        status_scrollbar.pack(side="right", fill="y", pady=5)

        # 초기 상태 정보 표시
        self.update_status_info()

    # ==== 새로 추가된 기능들 ====

    def change_output_folder(self):
        """저장 폴더 변경"""
        folder = filedialog.askdirectory(
            title="결과 저장 폴더 선택",
            initialdir=str(self.output_folder)
        )

        if folder:
            self.custom_output_folder = Path(folder)
            self.output_path_label.config(text=f"현재: {self.custom_output_folder}")
            self.log_message(f"저장 폴더 변경됨: {self.custom_output_folder}")

    def get_output_folder(self):
        """현재 설정된 출력 폴더 반환"""
        return self.custom_output_folder if self.custom_output_folder else self.output_folder

    def scan_images_folder(self):
        """이미지 폴더에서 자동으로 파일 스캔"""
        folder = filedialog.askdirectory(
            title="이미지 폴더 선택",
            initialdir="./data/product_images"
        )

        if folder:
            image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']
            found_images = []

            for ext in image_extensions:
                found_images.extend(glob.glob(os.path.join(folder, ext)))
                found_images.extend(glob.glob(os.path.join(folder, ext.upper())))

            if found_images:
                self.selected_images = found_images
                self.img_count_label.config(text=f"선택된 이미지: {len(found_images)}개")

                self.img_listbox.delete(0, "end")
                for img in found_images:
                    filename = os.path.basename(img)
                    self.img_listbox.insert("end", filename)

                self.log_message(f"폴더 스캔 완료: {len(found_images)}개 이미지 발견")
            else:
                messagebox.showinfo("정보", "선택한 폴더에 이미지 파일이 없습니다.")

    def scan_reviews_folder(self):
        """리뷰 폴더에서 자동으로 파일 스캔"""
        folder = filedialog.askdirectory(
            title="리뷰 파일 폴더 선택",
            initialdir="./data/reviews"
        )

        if folder:
            review_extensions = ['*.csv', '*.xlsx', '*.xls']
            found_reviews = []

            for ext in review_extensions:
                found_reviews.extend(glob.glob(os.path.join(folder, ext)))
                found_reviews.extend(glob.glob(os.path.join(folder, ext.upper())))

            if found_reviews:
                self.selected_reviews = found_reviews
                self.review_count_label.config(text=f"선택된 파일: {len(found_reviews)}개")

                self.review_listbox.delete(0, "end")
                for review in found_reviews:
                    filename = os.path.basename(review)
                    self.review_listbox.insert("end", filename)

                self.log_message(f"폴더 스캔 완료: {len(found_reviews)}개 리뷰 파일 발견")
            else:
                messagebox.showinfo("정보", "선택한 폴더에 리뷰 파일이 없습니다.")

    def browse_source_folder(self):
        """파일 정리용 소스 폴더 선택"""
        folder = filedialog.askdirectory(
            title="정리할 파일이 있는 폴더 선택",
            initialdir=str(self.source_folder)
        )

        if folder:
            self.source_folder = Path(folder)
            self.source_path_var.set(str(folder))
            self.log_message(f"소스 폴더 설정: {folder}")

    def scan_source_files(self):
        """소스 폴더에서 파일 스캔"""
        try:
            source_path = Path(self.source_path_var.get())
            if not source_path.exists():
                messagebox.showerror("오류", "지정된 폴더가 존재하지 않습니다.")
                return

            # 트리뷰 초기화
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)

            # 파일 스캔
            file_count = 0
            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    file_stat = file_path.stat()
                    file_size = f"{file_stat.st_size / 1024:.1f} KB"
                    file_date = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                    # 파일 타입 구분
                    suffix = file_path.suffix.lower()
                    if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                        file_type = "이미지"
                    elif suffix in ['.csv', '.xlsx', '.xls']:
                        file_type = "리뷰"
                    else:
                        file_type = "기타"

                    self.files_tree.insert("", "end", values=(file_type, file_path.name, file_size, file_date))
                    file_count += 1

            self.log_message(f"파일 스캔 완료: {file_count}개 파일 발견")

        except Exception as e:
            messagebox.showerror("오류", f"파일 스캔 중 오류 발생:\n{str(e)}")

    def organize_files(self):
        """파일들을 자동으로 정리"""
        try:
            source_path = Path(self.source_path_var.get())
            if not source_path.exists():
                messagebox.showerror("오류", "소스 폴더가 존재하지 않습니다.")
                return

            # 대상 폴더들 생성
            img_target = Path("data/product_images")
            review_target = Path("data/reviews")
            img_target.mkdir(parents=True, exist_ok=True)
            review_target.mkdir(parents=True, exist_ok=True)

            moved_count = 0

            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    suffix = file_path.suffix.lower()

                    if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                        # 이미지 파일 이동
                        target_path = img_target / file_path.name
                        if not target_path.exists():
                            shutil.copy2(file_path, target_path)
                            moved_count += 1
                            self.log_message(f"이미지 복사: {file_path.name} → data/product_images/")

                    elif suffix in ['.csv', '.xlsx', '.xls']:
                        # 리뷰 파일 이동
                        target_path = review_target / file_path.name
                        if not target_path.exists():
                            shutil.copy2(file_path, target_path)
                            moved_count += 1
                            self.log_message(f"리뷰 파일 복사: {file_path.name} → data/reviews/")

            messagebox.showinfo("완료", f"파일 정리 완료!\n총 {moved_count}개 파일이 정리되었습니다.")

            # 정리 후 다시 스캔
            self.scan_source_files()

        except Exception as e:
            messagebox.showerror("오류", f"파일 정리 중 오류 발생:\n{str(e)}")

    def launch_gui_automation(self):
        """기존 GUI 자동화 프로그램 실행"""
        try:
            gui_auto_path = Path("E:/VSC/file_organizer/FileOrganizerGUI_new.py")
            if gui_auto_path.exists():
                import subprocess
                subprocess.Popen(["python", str(gui_auto_path)], cwd=gui_auto_path.parent)
                self.log_message("GUI 자동화 프로그램 실행됨")
            else:
                messagebox.showerror("오류", "GUI 자동화 프로그램을 찾을 수 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"GUI 자동화 실행 실패:\n{str(e)}")

    def sync_with_gui_automation(self):
        """GUI 자동화 결과와 동기화"""
        try:
            # GUI 자동화의 결과 폴더 경로
            gui_result_path = Path("E:/업무/03_데이터_수집")

            if not gui_result_path.exists():
                messagebox.showwarning("경고", "GUI 자동화 결과 폴더가 없습니다.")
                return

            # 오늘 날짜 폴더들 찾기
            today = datetime.now().strftime("%Y-%m-%d")
            today_folders = list(gui_result_path.glob(f"{today}*"))

            if not today_folders:
                messagebox.showinfo("정보", "오늘 날짜의 데이터 폴더가 없습니다.")
                return

            sync_count = 0
            for folder in today_folders:
                # 해당 폴더의 파일들을 data 폴더로 복사
                for file_path in folder.rglob("*"):
                    if file_path.is_file():
                        suffix = file_path.suffix.lower()

                        if suffix in ['.png', '.jpg', '.jpeg']:
                            target = Path("data/product_images") / file_path.name
                            if not target.exists():
                                shutil.copy2(file_path, target)
                                sync_count += 1
                        elif suffix in ['.xlsx', '.xls', '.csv']:
                            target = Path("data/reviews") / file_path.name
                            if not target.exists():
                                shutil.copy2(file_path, target)
                                sync_count += 1

            self.log_message(f"동기화 완료: {sync_count}개 파일")
            messagebox.showinfo("완료", f"동기화 완료!\n{sync_count}개 파일이 동기화되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"동기화 실패:\n{str(e)}")

    def update_status_info(self):
        """상태 정보 업데이트"""
        try:
            status_info = []
            status_info.append("=== AI 콜드메일 시스템 상태 ===")
            status_info.append(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            status_info.append("")

            # 설정 파일 상태
            if os.path.exists(self.config_path):
                status_info.append("✅ 설정 파일: 정상")
            else:
                status_info.append("❌ 설정 파일: 없음")

            # 데이터 폴더 상태
            img_count = len(list(Path("data/product_images").glob("*"))) if Path("data/product_images").exists() else 0
            review_count = len(list(Path("data/reviews").glob("*"))) if Path("data/reviews").exists() else 0

            status_info.append(f"📷 이미지 파일: {img_count}개")
            status_info.append(f"📊 리뷰 파일: {review_count}개")
            status_info.append("")

            # 결과 폴더 상태
            output_folder = self.get_output_folder()
            result_count = len(list(output_folder.glob("*.json"))) if output_folder.exists() else 0
            status_info.append(f"📁 생성된 결과: {result_count}개")
            status_info.append(f"💾 저장 폴더: {output_folder}")
            status_info.append("")

            # GUI 자동화 연동 상태
            gui_auto_path = Path("E:/VSC/file_organizer/FileOrganizerGUI_new.py")
            if gui_auto_path.exists():
                status_info.append("✅ GUI 자동화: 연동 가능")
            else:
                status_info.append("⚠️ GUI 자동화: 경로 확인 필요")

            status_text = "\n".join(status_info)
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", status_text)

        except Exception as e:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"상태 정보 로드 실패: {str(e)}")

    # ==== 기존 메서드들 (수정됨) ====

    def generate_emails_thread(self):
        """별도 스레드에서 콜드메일 생성 (수정된 버전)"""
        try:
            self.log_message("🚀 콜드메일 생성 시작")

            # 설정 로드
            self.log_message("⚙️ 설정 파일 로드 중...")
            cfg = load_config(self.config_path)

            # 사용자가 변경한 설정 적용
            cfg.policy.email_min_chars = self.min_chars.get()
            cfg.policy.email_max_chars = self.max_chars.get()
            cfg.policy.tone_default = self.tone_var.get()

            # AI 클라이언트 초기화
            self.log_message("🤖 AI 모델 연결 중...")
            client = GeminiClient(cfg)

            # 프롬프트 로드
            self.log_message("📝 프롬프트 로드 중...")
            with open(f"{cfg.paths.prompts_dir}/cold_email.json", "r", encoding="utf-8") as f:
                prompt = json.load(f)

            # 출력 폴더 설정
            output_folder = self.get_output_folder()
            output_folder.mkdir(parents=True, exist_ok=True)

            # 각 이미지+리뷰 조합에 대해 콜드메일 생성
            total_combinations = len(self.selected_images) * len(self.selected_reviews)
            processed = 0

            for img_file in self.selected_images:
                for review_file in self.selected_reviews:
                    processed += 1
                    img_name = os.path.basename(img_file)
                    review_name = os.path.basename(review_file)

                    self.log_message(f"📊 처리 중 ({processed}/{total_combinations}): {img_name} + {review_name}")

                    # 실제로는 이미지 OCR + 리뷰 분석을 해야 하지만,
                    # 지금은 테스트용으로 간단히 처리
                    user_payload = f"이미지: {img_name}, 리뷰: {review_name} - 테스트 케이스"

                    # AI로 콜드메일 생성 (비동기 호출을 동기로 실행)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    draft = loop.run_until_complete(client.generate(prompt, user_payload))
                    loop.close()

                    # 최종 조립
                    final_email = compose_final_email(draft, cfg.policy)

                    # 결과 저장 (사용자가 지정한 폴더에)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = output_folder / f"email_{timestamp}_{processed}.json"

                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(final_email, f, ensure_ascii=False, indent=2)

                    self.generated_emails.append(final_email)
                    self.log_message(f"✅ 생성 완료: {output_file.name}")

            self.log_message(f"🎉 전체 완료! 총 {len(self.generated_emails)}개 생성됨")
            self.log_message(f"💾 저장 위치: {output_folder}")

        except Exception as e:
            self.log_message(f"❌ 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"콜드메일 생성 중 오류가 발생했습니다:\n{str(e)}")

        finally:
            # UI 상태 복원
            self.is_processing = False
            self.generate_btn.config(state="normal", text="✨ 콜드메일 생성 시작")
            self.progress_bar.stop()
            self.progress_var.set("완료")

    def open_output_folder(self):
        """결과 폴더 열기 (수정된 버전)"""
        try:
            output_folder = self.get_output_folder()
            if os.name == 'nt':  # Windows
                os.startfile(str(output_folder))
            else:  # macOS, Linux
                os.system(f"open {output_folder}")
            self.log_message(f"📁 결과 폴더 열림: {output_folder}")
        except Exception as e:
            self.log_message(f"❌ 폴더 열기 실패: {str(e)}")

    # ==== 기존 메서드들 (그대로 유지) ====

    def log_message(self, message):
        """로그 메시지를 텍스트 위젯에 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"

        self.log_text.insert("end", full_message)
        self.log_text.see("end")
        self.root.update_idletasks()

    def clear_log(self):
        """로그 텍스트 지우기"""
        self.log_text.delete("1.0", "end")

    def select_images(self):
        """이미지 파일 선택"""
        file_types = [
            ("이미지 파일", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("모든 파일", "*.*")
        ]

        files = filedialog.askopenfilenames(
            title="상품 상세페이지 이미지 선택",
            filetypes=file_types,
            initialdir="./data/product_images"
        )

        if files:
            self.selected_images = list(files)
            self.img_count_label.config(text=f"선택된 이미지: {len(files)}개")

            # 리스트박스 업데이트
            self.img_listbox.delete(0, "end")
            for file in files:
                filename = os.path.basename(file)
                self.img_listbox.insert("end", filename)

            self.log_message(f"이미지 {len(files)}개 선택됨")

    def select_reviews(self):
        """리뷰 파일 선택"""
        file_types = [
            ("CSV 파일", "*.csv"),
            ("Excel 파일", "*.xlsx *.xls"),
            ("모든 파일", "*.*")
        ]

        files = filedialog.askopenfilenames(
            title="고객 리뷰 파일 선택",
            filetypes=file_types,
            initialdir="./data/reviews"
        )

        if files:
            self.selected_reviews = list(files)
            self.review_count_label.config(text=f"선택된 파일: {len(files)}개")

            # 리스트박스 업데이트
            self.review_listbox.delete(0, "end")
            for file in files:
                filename = os.path.basename(file)
                self.review_listbox.insert("end", filename)

            self.log_message(f"리뷰 파일 {len(files)}개 선택됨")

    def load_settings(self):
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_path):
                self.log_message("설정 파일 로드 완료")
            else:
                self.log_message("⚠️ 설정 파일이 없습니다")
        except Exception as e:
            self.log_message(f"❌ 설정 로드 실패: {str(e)}")

    def start_generation(self):
        """콜드메일 생성 시작"""
        if self.is_processing:
            messagebox.showwarning("경고", "이미 처리 중입니다.")
            return

        # 입력 검증
        if not self.selected_images:
            messagebox.showerror("오류", "상품 이미지를 선택해주세요.")
            return

        if not self.selected_reviews:
            messagebox.showerror("오류", "리뷰 파일을 선택해주세요.")
            return

        # 별도 스레드에서 실행
        self.is_processing = True
        self.generate_btn.config(state="disabled", text="생성 중...")
        self.progress_bar.start(10)
        self.progress_var.set("콜드메일 생성 중...")

        threading.Thread(target=self.generate_emails_thread, daemon=True).start()

    def run_smoke_test(self):
        """스모크 테스트 실행"""
        if self.is_processing:
            messagebox.showwarning("경고", "다른 작업이 진행 중입니다.")
            return

        self.log_message("🧪 스모크 테스트 시작")

        def test_thread():
            try:
                import subprocess
                result = subprocess.run(
                    ["python", "run_email_smoke.py"],
                    capture_output=True,
                    text=True,
                    cwd="."
                )

                if result.returncode == 0:
                    self.log_message("✅ 스모크 테스트 성공!")
                    self.log_message(result.stdout)
                else:
                    self.log_message("❌ 스모크 테스트 실패")
                    self.log_message(result.stderr)
            except Exception as e:
                self.log_message(f"❌ 테스트 실행 오류: {str(e)}")

        threading.Thread(target=test_thread, daemon=True).start()

    def run(self):
        """GUI 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    # 필요한 폴더들 생성
    Path("outputs").mkdir(exist_ok=True)
    Path("gui").mkdir(exist_ok=True)
    Path("data/product_images").mkdir(parents=True, exist_ok=True)
    Path("data/reviews").mkdir(parents=True, exist_ok=True)

    # GUI 실행
    app = ColdMailGeneratorGUI()
    app.run()


if __name__ == "__main__":
    main()