#!/usr/bin/env python3
"""
2단계 분리 처리 GUI
사용자 실제 워크플로우에 맞춘 GUI 인터페이스
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


class TwoStageGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 AI 콜드메일 2단계 분리 처리 시스템")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")

        # 설정 및 프로세서 로드
        self.config = None
        self.processor = None
        self.selected_images = []
        self.selected_reviews = ""

        self.setup_ui()
        self.load_system()

    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 제목
        title_label = tk.Label(
            main_frame,
            text="🎯 AI 콜드메일 2단계 분리 처리 시스템",
            font=("맑은 고딕", 16, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        title_label.pack(pady=(0, 20))

        # 설명
        desc_label = tk.Label(
            main_frame,
            text="실제 워크플로우: Stage 1 (OCR/데이터추출) → Stage 2 (콜드메일생성)\n온도값 0.3, Google AI Studio 방식",
            font=("맑은 고딕", 10),
            bg="#f0f0f0",
            fg="#7f8c8d"
        )
        desc_label.pack(pady=(0, 20))

        # === Stage 1 섹션 ===
        stage1_frame = tk.LabelFrame(
            main_frame,
            text="📊 Stage 1: OCR 및 데이터 추출",
            font=("맑은 고딕", 12, "bold"),
            bg="#f0f0f0",
            fg="#e67e22"
        )
        stage1_frame.pack(fill="x", pady=(0, 15))

        # 이미지 선택
        img_frame = tk.Frame(stage1_frame, bg="#f0f0f0")
        img_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(
            img_frame,
            text="상품 이미지:",
            font=("맑은 고딕", 10),
            bg="#f0f0f0"
        ).pack(side="left")

        self.img_button = tk.Button(
            img_frame,
            text="이미지 선택",
            command=self.select_images,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 9)
        )
        self.img_button.pack(side="left", padx=(10, 0))

        self.img_label = tk.Label(
            img_frame,
            text="선택된 이미지 없음",
            font=("맑은 고딕", 9),
            bg="#f0f0f0",
            fg="#7f8c8d"
        )
        self.img_label.pack(side="left", padx=(10, 0))

        # Stage 1 실행
        self.stage1_button = tk.Button(
            stage1_frame,
            text="🔍 Stage 1 실행 (OCR 처리)",
            command=self.run_stage1,
            bg="#e67e22",
            fg="white",
            font=("맑은 고딕", 10, "bold"),
            height=2
        )
        self.stage1_button.pack(pady=10)

        # === Stage 2 섹션 ===
        stage2_frame = tk.LabelFrame(
            main_frame,
            text="📧 Stage 2: 콜드메일 생성",
            font=("맑은 고딕", 12, "bold"),
            bg="#f0f0f0",
            fg="#27ae60"
        )
        stage2_frame.pack(fill="x", pady=(0, 15))

        # 리뷰 선택
        review_frame = tk.Frame(stage2_frame, bg="#f0f0f0")
        review_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(
            review_frame,
            text="리뷰 데이터:",
            font=("맑은 고딕", 10),
            bg="#f0f0f0"
        ).pack(side="left")

        self.review_button = tk.Button(
            review_frame,
            text="CSV 파일 선택",
            command=self.select_reviews,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 9)
        )
        self.review_button.pack(side="left", padx=(10, 0))

        self.review_label = tk.Label(
            review_frame,
            text="선택된 리뷰 파일 없음",
            font=("맑은 고딕", 9),
            bg="#f0f0f0",
            fg="#7f8c8d"
        )
        self.review_label.pack(side="left", padx=(10, 0))

        # Stage 2 실행
        self.stage2_button = tk.Button(
            stage2_frame,
            text="📧 Stage 2 실행 (콜드메일 생성)",
            command=self.run_stage2,
            bg="#27ae60",
            fg="white",
            font=("맑은 고딕", 10, "bold"),
            height=2,
            state="disabled"
        )
        self.stage2_button.pack(pady=10)

        # === 통합 실행 섹션 ===
        complete_frame = tk.LabelFrame(
            main_frame,
            text="🚀 완전한 2단계 워크플로우",
            font=("맑은 고딕", 12, "bold"),
            bg="#f0f0f0",
            fg="#8e44ad"
        )
        complete_frame.pack(fill="x", pady=(0, 15))

        self.complete_button = tk.Button(
            complete_frame,
            text="🚀 완전한 워크플로우 실행\n(Stage 1 + Stage 2 통합)",
            command=self.run_complete_workflow,
            bg="#8e44ad",
            fg="white",
            font=("맑은 고딕", 11, "bold"),
            height=3
        )
        self.complete_button.pack(pady=15)

        # === 결과 표시 ===
        result_frame = tk.LabelFrame(
            main_frame,
            text="📋 처리 결과",
            font=("맑은 고딕", 12, "bold"),
            bg="#f0f0f0"
        )
        result_frame.pack(fill="both", expand=True, pady=(0, 10))

        # 스크롤 가능한 텍스트 영역
        text_frame = tk.Frame(result_frame, bg="#f0f0f0")
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.result_text = tk.Text(
            text_frame,
            wrap="word",
            font=("맑은 고딕", 9),
            bg="white",
            fg="#2c3e50"
        )

        scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 상태 표시
        self.status_var = tk.StringVar(value="시스템 준비 중...")
        status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("맑은 고딕", 9),
            bg="#f0f0f0",
            fg="#34495e"
        )
        status_label.pack(pady=(10, 0))

        # 변수 초기화
        self.stage1_result = None

    def load_system(self):
        """시스템 초기화"""
        try:
            self.config = load_config()
            self.processor = TwoStageProcessor(self.config)
            self.status_var.set("✅ 시스템 준비 완료")
            self.log("🎯 2단계 분리 처리 시스템이 준비되었습니다.")
            self.log("- 온도값: 0.3 (Google AI Studio 방식)")
            self.log("- Stage 1: OCR 및 데이터 추출")
            self.log("- Stage 2: 콜드메일 생성")
        except Exception as e:
            self.status_var.set("❌ 시스템 로드 실패")
            self.log(f"❌ 시스템 로드 실패: {str(e)}")

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
            self.img_label.config(text=f"{len(files)}개 이미지 선택됨")
            self.log(f"📸 {len(files)}개 이미지 선택: {', '.join([Path(f).name for f in files])}")

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
            self.review_label.config(text=f"선택됨: {Path(file).name}")
            self.log(f"📊 리뷰 데이터 선택: {Path(file).name}")

    def log(self, message):
        """결과 로그 추가"""
        self.result_text.insert("end", f"{message}\n")
        self.result_text.see("end")
        self.root.update_idletasks()

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

                self.log("🔍 Stage 1 시작: OCR 및 데이터 추출")
                result = loop.run_until_complete(
                    self.processor.stage1_ocr_extraction(self.selected_images)
                )

                self.stage1_result = result
                self.log(f"✅ Stage 1 완료: {result['total_images']}개 이미지 처리")

                # 결과 저장
                output_dir = Path(self.config.paths.output_root_dir)
                output_dir.mkdir(exist_ok=True)

                output_file = output_dir / "stage1_result.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                self.log(f"📁 결과 저장: {output_file}")
                self.status_var.set("✅ Stage 1 완료")
                self.stage2_button.config(state="normal")

            except Exception as e:
                self.log(f"❌ Stage 1 실패: {str(e)}")
                self.status_var.set("❌ Stage 1 실패")
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

                self.log("📧 Stage 2 시작: 콜드메일 생성")
                cold_email = loop.run_until_complete(
                    self.processor.stage2_coldmail_generation(
                        self.stage1_result,
                        self.selected_reviews
                    )
                )

                self.log("✅ Stage 2 완료: 콜드메일 생성")

                # 결과 저장 및 표시
                output_dir = Path(self.config.paths.output_root_dir)
                output_file = output_dir / "stage2_coldmail.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(cold_email)

                self.log(f"📁 콜드메일 저장: {output_file}")
                self.log("=" * 50)
                self.log("📧 생성된 콜드메일:")
                self.log("=" * 50)
                self.log(cold_email)
                self.log("=" * 50)

                self.status_var.set("✅ Stage 2 완료")

            except Exception as e:
                self.log(f"❌ Stage 2 실패: {str(e)}")
                self.status_var.set("❌ Stage 2 실패")
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
                self.status_var.set("🚀 완전한 워크플로우 실행 중...")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                self.log("🚀 완전한 2단계 워크플로우 시작")
                result = loop.run_until_complete(
                    self.processor.process_complete_workflow(
                        self.selected_images,
                        self.selected_reviews
                    )
                )

                self.log("✅ 완전한 워크플로우 완료")
                self.log(f"- 처리된 이미지: {result['summary']['images_processed']}개")
                self.log("- 온도값: 0.3 (Google AI Studio 방식)")

                # 결과 저장
                output_dir = Path(self.config.paths.output_root_dir)
                output_file = output_dir / "complete_workflow_result.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                # 콜드메일 별도 저장
                email_file = output_dir / "final_coldmail.txt"
                with open(email_file, 'w', encoding='utf-8') as f:
                    f.write(result["stage2_result"]["cold_email"])

                self.log(f"📁 전체 결과 저장: {output_file}")
                self.log(f"📁 콜드메일 저장: {email_file}")

                # 콜드메일 표시
                self.log("=" * 50)
                self.log("📧 최종 생성된 콜드메일:")
                self.log("=" * 50)
                self.log(result["stage2_result"]["cold_email"])
                self.log("=" * 50)

                self.status_var.set("✅ 완전한 워크플로우 완료")

            except Exception as e:
                self.log(f"❌ 워크플로우 실패: {str(e)}")
                self.status_var.set("❌ 워크플로우 실패")
            finally:
                self.complete_button.config(state="normal")

        threading.Thread(target=async_complete, daemon=True).start()


def main():
    """메인 실행 함수"""
    root = tk.Tk()
    app = TwoStageGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()