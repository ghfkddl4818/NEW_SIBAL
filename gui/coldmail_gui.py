#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 콜드메일 자동생성 시스템 GUI
Tkinter 기반 간단하고 실용적인 인터페이스
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

# 상위 디렉토리를 Python 경로에 추가 (모듈 import용)
sys.path.append(str(Path(__file__).parent.parent))

from core.config import load_config
from llm.gemini_client import GeminiClient
from compose.composer import compose_final_email

class ColdMailGeneratorGUI:
    def __init__(self):
        print("AI 콜드메일 GUI 시작...")
        self.root = tk.Tk()
        self.root.title("AI 콜드메일 자동생성 시스템 v1.0")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        # 기본 설정
        self.config_path = "config/config.yaml"
        self.output_folder = Path("outputs")
        self.selected_images = []
        self.selected_reviews = []
        self.is_processing = False

        # 결과 저장용
        self.generated_emails = []

        print("GUI 위젯 생성 중...")
        self.create_widgets()
        self.load_settings()

        print("GUI 초기화 완료!")

    def create_widgets(self):
        """GUI 위젯들을 생성"""

        # 메인 제목
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill="x", padx=5, pady=5)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🤖 AI 콜드메일 자동생성 시스템",
            font=("맑은 고딕", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)

        # 메인 컨테이너
        main_frame = tk.Frame(self.root)
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

        self.review_count_label = tk.Label(review_btn_frame, text="선택된 파일: 0개", font=("맑은 고딕", 9))
        self.review_count_label.pack(side="left", padx=(10, 0))

        # 선택된 리뷰 파일 목록
        self.review_listbox = tk.Listbox(review_frame, height=4, font=("맑은 고딕", 9))
        self.review_listbox.pack(fill="x", pady=5)

        # 설정 옵션
        settings_frame = tk.LabelFrame(left_frame, text="⚙️ 설정", font=("맑은 고딕", 10, "bold"))
        settings_frame.pack(fill="x", padx=10, pady=5)

        # 톤앤매너 선택
        tone_frame = tk.Frame(settings_frame)
        tone_frame.pack(fill="x", padx=5, pady=3)

        tk.Label(tone_frame, text="톤앤매너:", font=("맑은 고딕", 9)).pack(side="left")
        self.tone_var = tk.StringVar(value="consultant")
        tone_combo = ttk.Combobox(tone_frame, textvariable=self.tone_var,
                                 values=["consultant", "student"], width=15, state="readonly")
        tone_combo.pack(side="left", padx=(5, 0))

        # 이메일 길이 설정
        length_frame = tk.Frame(settings_frame)
        length_frame.pack(fill="x", padx=5, pady=3)

        tk.Label(length_frame, text="글자수:", font=("맑은 고딕", 9)).pack(side="left")
        self.min_chars = tk.IntVar(value=350)
        self.max_chars = tk.IntVar(value=600)

        tk.Label(length_frame, text="최소", font=("맑은 고딕", 8)).pack(side="left", padx=(10, 2))
        tk.Spinbox(length_frame, from_=200, to=500, textvariable=self.min_chars, width=6).pack(side="left")
        tk.Label(length_frame, text="최대", font=("맑은 고딕", 8)).pack(side="left", padx=(5, 2))
        tk.Spinbox(length_frame, from_=400, to=800, textvariable=self.max_chars, width=6).pack(side="left")

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

    def generate_emails_thread(self):
        """별도 스레드에서 콜드메일 생성 (실제 로직)"""
        try:
            self.log_message("🚀 콜드메일 생성 시작")

            # 설정 로드
            self.log_message("⚙️ 설정 파일 로드 중...")
            cfg = load_config(self.config_path)

            # AI 클라이언트 초기화
            self.log_message("🤖 AI 모델 연결 중...")
            client = GeminiClient(cfg)

            # 프롬프트 로드
            self.log_message("📝 프롬프트 로드 중...")
            with open(f"{cfg.paths.prompts_dir}/cold_email.json", "r", encoding="utf-8") as f:
                prompt = json.load(f)

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

                    # 결과 저장
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = self.output_folder / f"email_{timestamp}_{processed}.json"

                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(final_email, f, ensure_ascii=False, indent=2)

                    self.generated_emails.append(final_email)
                    self.log_message(f"✅ 생성 완료: {output_file.name}")

            self.log_message(f"🎉 전체 완료! 총 {len(self.generated_emails)}개 생성됨")

        except Exception as e:
            self.log_message(f"❌ 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"콜드메일 생성 중 오류가 발생했습니다:\n{str(e)}")

        finally:
            # UI 상태 복원
            self.is_processing = False
            self.generate_btn.config(state="normal", text="✨ 콜드메일 생성 시작")
            self.progress_bar.stop()
            self.progress_var.set("완료")

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

    def open_output_folder(self):
        """결과 폴더 열기"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(self.output_folder))
            else:  # macOS, Linux
                os.system(f"open {self.output_folder}")
            self.log_message("📁 결과 폴더 열림")
        except Exception as e:
            self.log_message(f"❌ 폴더 열기 실패: {str(e)}")

    def run(self):
        """GUI 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    # outputs 폴더가 없으면 생성
    Path("outputs").mkdir(exist_ok=True)
    Path("gui").mkdir(exist_ok=True)

    # GUI 실행
    app = ColdMailGeneratorGUI()
    app.run()


if __name__ == "__main__":
    main()