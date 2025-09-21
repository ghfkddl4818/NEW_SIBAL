#!/usr/bin/env python3
"""
통합 AI 콜드메일 시스템 GUI
모든 기능을 하나로 통합한 인터페이스
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
from typing import List

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config
from llm.two_stage_processor import TwoStageProcessor


class UnifiedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 AI 콜드메일 통합 시스템")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # 설정 및 프로세서 로드
        self.config = None
        self.processor = None
        self.selected_images = []
        self.selected_reviews = ""

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
            text="🎯 AI 콜드메일 통합 시스템",
            font=("맑은 고딕", 18, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        title_label.pack(pady=(0, 10))

        # 탭 노트북
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # 탭들 생성
        self.create_two_stage_tab()
        self.create_quick_process_tab()
        self.create_settings_tab()

        # 하단 상태바
        status_frame = tk.Frame(main_frame, bg="#f0f0f0")
        status_frame.pack(fill="x", pady=(10, 0))

        self.status_var = tk.StringVar(value="시스템 준비 중...")
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("맑은 고딕", 9),
            bg="#f0f0f0",
            fg="#34495e"
        )
        status_label.pack(side="left")

        # 변수 초기화
        self.stage1_result = None

    def create_two_stage_tab(self):
        """2단계 분리 처리 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎯 2단계 처리 (추천)")

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

        # 설명
        desc_frame = tk.Frame(scrollable_frame, bg="#e8f4fd", relief="solid", bd=1)
        desc_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(
            desc_frame,
            text="✨ 사용자 실제 워크플로우에 맞춘 2단계 분리 처리",
            font=("맑은 고딕", 12, "bold"),
            bg="#e8f4fd",
            fg="#2980b9"
        ).pack(pady=5)

        tk.Label(
            desc_frame,
            text="Stage 1: 이미지 → OCR/데이터추출 (온도 0.3) → Stage 2: 텍스트+리뷰 → 콜드메일 (온도 0.3)",
            font=("맑은 고딕", 10),
            bg="#e8f4fd",
            fg="#34495e"
        ).pack(pady=5)

        # === Stage 1 섹션 ===
        stage1_frame = tk.LabelFrame(
            scrollable_frame,
            text="📊 Stage 1: OCR 및 데이터 추출",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa",
            fg="#e67e22"
        )
        stage1_frame.pack(fill="x", padx=20, pady=10)

        # 이미지 선택
        img_frame = tk.Frame(stage1_frame, bg="#f8f9fa")
        img_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(
            img_frame,
            text="상품 이미지:",
            font=("맑은 고딕", 11),
            bg="#f8f9fa"
        ).pack(side="left")

        self.img_button = tk.Button(
            img_frame,
            text="📁 이미지 선택",
            command=self.select_images,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 10),
            padx=20,
            pady=5
        )
        self.img_button.pack(side="left", padx=(15, 0))

        self.img_label = tk.Label(
            img_frame,
            text="선택된 이미지 없음",
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        self.img_label.pack(side="left", padx=(15, 0))

        # Stage 1 실행 버튼
        self.stage1_button = tk.Button(
            stage1_frame,
            text="🔍 Stage 1 실행 (OCR 처리)",
            command=self.run_stage1,
            bg="#e67e22",
            fg="white",
            font=("맑은 고딕", 11, "bold"),
            height=2,
            padx=30,
            pady=5
        )
        self.stage1_button.pack(pady=15)

        # === Stage 2 섹션 ===
        stage2_frame = tk.LabelFrame(
            scrollable_frame,
            text="📧 Stage 2: 콜드메일 생성",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa",
            fg="#27ae60"
        )
        stage2_frame.pack(fill="x", padx=20, pady=10)

        # 리뷰 선택
        review_frame = tk.Frame(stage2_frame, bg="#f8f9fa")
        review_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(
            review_frame,
            text="리뷰 데이터:",
            font=("맑은 고딕", 11),
            bg="#f8f9fa"
        ).pack(side="left")

        self.review_button = tk.Button(
            review_frame,
            text="📊 CSV 파일 선택",
            command=self.select_reviews,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 10),
            padx=20,
            pady=5
        )
        self.review_button.pack(side="left", padx=(15, 0))

        self.review_label = tk.Label(
            review_frame,
            text="선택된 리뷰 파일 없음",
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        self.review_label.pack(side="left", padx=(15, 0))

        # Stage 2 실행 버튼
        self.stage2_button = tk.Button(
            stage2_frame,
            text="📧 Stage 2 실행 (콜드메일 생성)",
            command=self.run_stage2,
            bg="#27ae60",
            fg="white",
            font=("맑은 고딕", 11, "bold"),
            height=2,
            padx=30,
            pady=5,
            state="disabled"
        )
        self.stage2_button.pack(pady=15)

        # === 통합 실행 섹션 ===
        complete_frame = tk.LabelFrame(
            scrollable_frame,
            text="🚀 완전한 2단계 워크플로우 (원클릭)",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa",
            fg="#8e44ad"
        )
        complete_frame.pack(fill="x", padx=20, pady=10)

        self.complete_button = tk.Button(
            complete_frame,
            text="🚀 완전한 워크플로우 실행\n(Stage 1 + Stage 2 통합 처리)",
            command=self.run_complete_workflow,
            bg="#8e44ad",
            fg="white",
            font=("맑은 고딕", 13, "bold"),
            height=3,
            padx=40,
            pady=10
        )
        self.complete_button.pack(pady=20)

        # 레이아웃 설정
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_quick_process_tab(self):
        """빠른 처리 탭 (기존 1단계 통합)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚡ 빠른 처리")

        frame = tk.Frame(tab, bg="#f8f9fa")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 설명
        tk.Label(
            frame,
            text="⚡ 빠른 1단계 통합 처리",
            font=("맑은 고딕", 16, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        ).pack(pady=20)

        tk.Label(
            frame,
            text="이미지와 리뷰를 한 번에 처리하여 콜드메일 생성 (기존 방식)",
            font=("맑은 고딕", 11),
            bg="#f8f9fa",
            fg="#7f8c8d"
        ).pack(pady=10)

        # 파일 선택 프레임
        file_frame = tk.Frame(frame, bg="#f8f9fa")
        file_frame.pack(fill="x", pady=30)

        # 이미지 선택
        img_quick_frame = tk.Frame(file_frame, bg="#f8f9fa")
        img_quick_frame.pack(fill="x", pady=10)

        self.img_quick_button = tk.Button(
            img_quick_frame,
            text="📁 이미지 파일 선택",
            command=self.select_images,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 11),
            padx=30,
            pady=10
        )
        self.img_quick_button.pack(side="left")

        self.img_quick_label = tk.Label(
            img_quick_frame,
            text="이미지를 선택해주세요",
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        self.img_quick_label.pack(side="left", padx=(20, 0))

        # 리뷰 선택
        review_quick_frame = tk.Frame(file_frame, bg="#f8f9fa")
        review_quick_frame.pack(fill="x", pady=10)

        self.review_quick_button = tk.Button(
            review_quick_frame,
            text="📊 리뷰 CSV 선택",
            command=self.select_reviews,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 11),
            padx=30,
            pady=10
        )
        self.review_quick_button.pack(side="left")

        self.review_quick_label = tk.Label(
            review_quick_frame,
            text="리뷰 파일을 선택해주세요",
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        self.review_quick_label.pack(side="left", padx=(20, 0))

        # 빠른 실행 버튼
        self.quick_button = tk.Button(
            frame,
            text="⚡ 빠른 콜드메일 생성\n(1단계 통합 처리)",
            command=self.run_complete_workflow,
            bg="#e74c3c",
            fg="white",
            font=("맑은 고딕", 14, "bold"),
            height=3,
            padx=50,
            pady=15
        )
        self.quick_button.pack(pady=40)

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

        # 설정 정보 표시
        settings_frame = tk.LabelFrame(
            frame,
            text="현재 설정",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        settings_frame.pack(fill="x", pady=20)

        settings_text = """
• 모델: Gemini 2.5 Pro (Vertex AI)
• 온도값: 0.3 (Google AI Studio 방식)
• 최대 출력 토큰: 1024
• 인증: Google Cloud ADC
• 프로젝트: ${VERTEX_PROJECT_ID}

• Stage 1: OCR 및 데이터 추출
• Stage 2: 콜드메일 생성 (리뷰 300개 샘플링)
        """

        tk.Label(
            settings_frame,
            text=settings_text,
            font=("맑은 고딕", 10),
            bg="#f8f9fa",
            fg="#2c3e50",
            justify="left"
        ).pack(padx=20, pady=15)

        # 폴더 바로가기
        folders_frame = tk.LabelFrame(
            frame,
            text="폴더 바로가기",
            font=("맑은 고딕", 12, "bold"),
            bg="#f8f9fa"
        )
        folders_frame.pack(fill="x", pady=20)

        folder_buttons_frame = tk.Frame(folders_frame, bg="#f8f9fa")
        folder_buttons_frame.pack(pady=10)

        tk.Button(
            folder_buttons_frame,
            text="📁 이미지 폴더 열기",
            command=lambda: os.startfile("data/product_images"),
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 10),
            padx=20,
            pady=5
        ).pack(side="left", padx=10)

        tk.Button(
            folder_buttons_frame,
            text="📊 리뷰 폴더 열기",
            command=lambda: os.startfile("data/reviews"),
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 10),
            padx=20,
            pady=5
        ).pack(side="left", padx=10)

        tk.Button(
            folder_buttons_frame,
            text="📄 결과 폴더 열기",
            command=lambda: os.startfile("outputs"),
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 10),
            padx=20,
            pady=5
        ).pack(side="left", padx=10)

    def load_system(self):
        """시스템 초기화"""
        try:
            self.config = load_config()
            self.processor = TwoStageProcessor(self.config)
            self.status_var.set("✅ 시스템 준비 완료 - 2단계 분리 처리 시스템 활성화")
            self.log("🎯 AI 콜드메일 통합 시스템이 준비되었습니다.")
        except Exception as e:
            self.status_var.set("❌ 시스템 로드 실패")
            messagebox.showerror("오류", f"시스템 로드 실패: {str(e)}")

    def select_images(self):
        """이미지 파일 선택"""
        files = filedialog.askopenfilenames(
            title="상품 이미지 선택",
            filetypes=[
                ("이미지 파일", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("모든 파일", "*.*")
            ]
        )
        if files:
            self.selected_images = list(files)
            message = f"{len(files)}개 이미지 선택됨"
            self.img_label.config(text=message)
            if hasattr(self, 'img_quick_label'):
                self.img_quick_label.config(text=message)

    def select_reviews(self):
        """리뷰 CSV 파일 선택"""
        file = filedialog.askopenfilename(
            title="리뷰 데이터 선택",
            filetypes=[
                ("CSV 파일", "*.csv"),
                ("모든 파일", "*.*")
            ]
        )
        if file:
            self.selected_reviews = file
            message = f"선택됨: {Path(file).name}"
            self.review_label.config(text=message)
            if hasattr(self, 'review_quick_label'):
                self.review_quick_label.config(text=message)

    def log(self, message):
        """로그 출력 (현재는 상태바에만 표시)"""
        print(message)  # 콘솔 출력

    def run_stage1(self):
        """Stage 1 실행"""
        if not self.selected_images:
            messagebox.showerror("오류", "이미지를 먼저 선택해주세요.")
            return

        def async_stage1():
            try:
                self.stage1_button.config(state="disabled")
                self.status_var.set("🔍 Stage 1 처리 중...")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                result = loop.run_until_complete(
                    self.processor.stage1_ocr_extraction(self.selected_images)
                )

                self.stage1_result = result
                self.status_var.set("✅ Stage 1 완료")
                self.stage2_button.config(state="normal")
                messagebox.showinfo("완료", f"Stage 1 완료: {result['total_images']}개 이미지 처리")

            except Exception as e:
                self.status_var.set("❌ Stage 1 실패")
                messagebox.showerror("오류", f"Stage 1 실패: {str(e)}")
            finally:
                self.stage1_button.config(state="normal")

        threading.Thread(target=async_stage1, daemon=True).start()

    def run_stage2(self):
        """Stage 2 실행"""
        if not self.stage1_result:
            messagebox.showerror("오류", "Stage 1을 먼저 실행해주세요.")
            return

        if not self.selected_reviews:
            messagebox.showerror("오류", "리뷰 파일을 선택해주세요.")
            return

        def async_stage2():
            try:
                self.stage2_button.config(state="disabled")
                self.status_var.set("📧 Stage 2 처리 중...")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                cold_email = loop.run_until_complete(
                    self.processor.stage2_coldmail_generation(
                        self.stage1_result,
                        self.selected_reviews
                    )
                )

                # 결과 저장
                output_dir = Path(self.config.paths.output_root_dir)
                output_dir.mkdir(exist_ok=True)
                output_file = output_dir / "generated_coldmail.txt"

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(cold_email)

                self.status_var.set("✅ Stage 2 완료 - 콜드메일 생성됨")
                messagebox.showinfo("완료", f"콜드메일이 생성되었습니다!\n저장 위치: {output_file}")

            except Exception as e:
                self.status_var.set("❌ Stage 2 실패")
                messagebox.showerror("오류", f"Stage 2 실패: {str(e)}")
            finally:
                self.stage2_button.config(state="normal")

        threading.Thread(target=async_stage2, daemon=True).start()

    def run_complete_workflow(self):
        """완전한 워크플로우 실행"""
        if not self.selected_images:
            messagebox.showerror("오류", "이미지를 먼저 선택해주세요.")
            return

        if not self.selected_reviews:
            messagebox.showerror("오류", "리뷰 파일을 선택해주세요.")
            return

        def async_complete():
            try:
                self.complete_button.config(state="disabled")
                if hasattr(self, 'quick_button'):
                    self.quick_button.config(state="disabled")

                self.status_var.set("🚀 완전한 워크플로우 실행 중...")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                result = loop.run_until_complete(
                    self.processor.process_complete_workflow(
                        self.selected_images,
                        self.selected_reviews
                    )
                )

                # 결과 저장
                output_dir = Path(self.config.paths.output_root_dir)
                output_dir.mkdir(exist_ok=True)

                # 최종 콜드메일 저장
                email_file = output_dir / "final_coldmail.txt"
                with open(email_file, 'w', encoding='utf-8') as f:
                    f.write(result["stage2_result"]["cold_email"])

                # 전체 결과 저장
                result_file = output_dir / "complete_result.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                self.status_var.set("✅ 완전한 워크플로우 완료!")

                # 성공 메시지와 함께 결과 표시
                messagebox.showinfo(
                    "🎉 완료!",
                    f"콜드메일이 성공적으로 생성되었습니다!\n\n"
                    f"• 처리된 이미지: {result['summary']['images_processed']}개\n"
                    f"• 온도값: 0.3 (Google AI Studio 방식)\n"
                    f"• 저장 위치: {email_file}\n\n"
                    f"결과 파일을 확인해보세요!"
                )

                # 결과 폴더 열기 옵션
                if messagebox.askyesno("폴더 열기", "결과 폴더를 지금 여시겠습니까?"):
                    os.startfile(str(output_dir))

            except Exception as e:
                self.status_var.set("❌ 워크플로우 실패")
                messagebox.showerror("오류", f"워크플로우 실패: {str(e)}")
            finally:
                self.complete_button.config(state="normal")
                if hasattr(self, 'quick_button'):
                    self.quick_button.config(state="normal")

        threading.Thread(target=async_complete, daemon=True).start()


def main():
    """메인 실행 함수"""
    root = tk.Tk()
    app = UnifiedGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()