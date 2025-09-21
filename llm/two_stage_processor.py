"""
2단계 분리 처리 시스템

Stage 1: OCR 및 데이터 추출 (상품 이미지 → 구조화된 텍스트)
Stage 2: 콜드메일 생성 (구조화된 텍스트 + 리뷰 데이터 → 콜드메일)
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from .gemini_client import GeminiClient

# 상위 경로에서 EmailSenderManager import
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compose.email_sender_manager import EmailSenderManager


class TwoStageProcessor:
    """2단계 분리 처리 시스템"""

    def __init__(self, config):
        self.config = config
        self.client = GeminiClient(config)

        # 발송 관리자 초기화
        self.email_sender_manager = EmailSenderManager()

        # 프롬프트 파일 경로 (PyInstaller 환경 지원)
        prompts_dir = self._resolve_prompts_dir(config.paths.prompts_dir)
        self.ocr_prompt_path = prompts_dir / "ocr_extraction.txt"
        self.coldmail_prompt_path = prompts_dir / "cold_email_generation.json"

        # 프롬프트 로드
        self.ocr_prompt = self._load_ocr_prompt()
        self.coldmail_prompt = self._load_coldmail_prompt()

    def _resolve_prompts_dir(self, prompts_dir: str) -> Path:
        """PyInstaller 환경에서 prompts 디렉토리 경로 해결"""
        prompts_path = Path(prompts_dir)

        # 절대 경로인 경우 그대로 사용
        if prompts_path.is_absolute():
            return prompts_path

        # PyInstaller 실행 환경 확인
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 패키지된 실행 파일에서는 _MEIPASS 사용
            base_path = Path(sys._MEIPASS)
            return base_path / prompts_dir.lstrip('./')
        else:
            # 일반 Python 실행 환경
            return prompts_path

    def _load_ocr_prompt(self) -> str:
        """OCR 및 데이터 추출 프롬프트 로드"""
        try:
            with open(self.ocr_prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"OCR 프롬프트 로드 실패: {e}")
            raise

    def _load_coldmail_prompt(self) -> Dict[str, Any]:
        """콜드메일 생성 프롬프트 로드"""
        try:
            with open(self.coldmail_prompt_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"콜드메일 프롬프트 로드 실패: {e}")
            raise

    def _sample_reviews(self, reviews_data: pd.DataFrame, target_count: int = 300) -> pd.DataFrame:
        """리뷰 데이터를 300개 기준으로 샘플링"""
        if len(reviews_data) <= target_count:
            logger.info(f"리뷰 데이터 {len(reviews_data)}개 - 모든 데이터 사용")
            return reviews_data

        # 평점별로 균등하게 샘플링
        sampled_reviews = []

        # 평점별 분포 확인
        if 'rating' in reviews_data.columns:
            ratings = reviews_data['rating'].unique()
            samples_per_rating = target_count // len(ratings)

            for rating in ratings:
                rating_data = reviews_data[reviews_data['rating'] == rating]
                sample_size = min(len(rating_data), samples_per_rating)
                sampled = rating_data.sample(n=sample_size, random_state=42)
                sampled_reviews.append(sampled)

            # 남은 샘플 수만큼 추가 샘플링
            current_count = sum(len(df) for df in sampled_reviews)
            if current_count < target_count:
                remaining = target_count - current_count
                remaining_data = reviews_data[~reviews_data.index.isin(
                    pd.concat(sampled_reviews).index
                )]
                if len(remaining_data) > 0:
                    additional = remaining_data.sample(
                        n=min(len(remaining_data), remaining),
                        random_state=42
                    )
                    sampled_reviews.append(additional)

            result = pd.concat(sampled_reviews).sample(frac=1, random_state=42)
        else:
            # rating 컬럼이 없으면 랜덤 샘플링
            result = reviews_data.sample(n=target_count, random_state=42)

        logger.info(f"리뷰 데이터 샘플링: {len(reviews_data)}개 → {len(result)}개")
        return result

    async def stage1_ocr_extraction(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Stage 1: OCR 및 데이터 추출 (Tesseract 사용 - 무료!)
        상품 이미지들 → 구조화된 텍스트 데이터
        """
        logger.info("Stage 1 시작: Tesseract OCR 및 데이터 추출")

        try:
            # 이미지 파일들을 처리
            extracted_data = []

            for image_path in image_paths:
                logger.info(f"Tesseract로 이미지 처리 중: {image_path}")

                # Tesseract로 OCR 처리 (무료!)
                raw_text = self._extract_text_with_tesseract(image_path)

                # 추출된 텍스트를 Gemini로 구조화 (비용 절약)
                structured_response = await self.client.process_text_only(
                    prompt=f"{self.ocr_prompt}\n\n추출된 텍스트:\n{raw_text}",
                    temperature=0.3
                )

                extracted_data.append({
                    "image_path": image_path,
                    "raw_text": raw_text,
                    "extracted_text": structured_response,
                    "timestamp": pd.Timestamp.now().isoformat()
                })

            # 결과 통합
            stage1_result = {
                "stage": "ocr_extraction",
                "input_images": image_paths,
                "extracted_data": extracted_data,
                "total_images": len(image_paths),
                "processed_at": pd.Timestamp.now().isoformat()
            }

            logger.info(f"Stage 1 완료: {len(image_paths)}개 이미지 처리")
            return stage1_result

        except Exception as e:
            logger.error(f"Stage 1 처리 실패: {e}")
            raise

    async def stage2_coldmail_generation(
        self,
        stage1_result: Dict[str, Any],
        reviews_file_path: str
    ) -> str:
        """
        Stage 2: 콜드메일 생성
        구조화된 텍스트 + 리뷰 데이터(~300개) → 최종 콜드메일
        """
        logger.info("Stage 2 시작: 콜드메일 생성")

        try:
            # 리뷰 데이터 로드 및 샘플링
            reviews_data = pd.read_csv(reviews_file_path, encoding='utf-8')
            sampled_reviews = self._sample_reviews(reviews_data, target_count=300)

            # Stage 1 결과에서 텍스트 추출
            extracted_texts = []
            for item in stage1_result["extracted_data"]:
                extracted_texts.append(item["extracted_text"])

            # 통합된 상품 정보 생성
            combined_product_info = "\n\n".join([
                f"=== 이미지 {i+1} 분석 결과 ===\n{text}"
                for i, text in enumerate(extracted_texts)
            ])

            # 리뷰 데이터를 텍스트로 변환
            review_text = self._format_reviews_for_prompt(sampled_reviews)

            # 콜드메일 프롬프트 구성
            coldmail_prompt_text = self._build_coldmail_prompt(
                combined_product_info,
                review_text
            )

            # Gemini로 콜드메일 생성
            cold_email = await self.client.process_text_only(
                prompt=coldmail_prompt_text,
                temperature=0.3  # 일관된 품질을 위해 낮은 온도
            )

            # 콜드메일 결과를 발송대기 리스트에 자동 추가
            self._add_to_pending_list(cold_email, combined_product_info)

            logger.info("Stage 2 완료: 콜드메일 생성 및 발송대기 리스트 등록")
            return cold_email

        except Exception as e:
            logger.error(f"Stage 2 처리 실패: {e}")
            raise

    def _format_reviews_for_prompt(self, reviews_data: pd.DataFrame) -> str:
        """리뷰 데이터를 프롬프트용 텍스트로 포맷팅"""
        review_lines = []

        for idx, row in reviews_data.iterrows():
            # 기본적인 리뷰 정보 추출
            rating = row.get('rating', '평점없음')
            content = row.get('content', row.get('review', row.get('text', '')))

            if content:
                review_lines.append(f"평점 {rating}: {content}")

        return "\n".join(review_lines[:300])  # 최대 300개로 제한

    def _build_coldmail_prompt(self, product_info: str, review_text: str) -> str:
        """콜드메일 생성을 위한 최종 프롬프트 구성"""

        # JSON 프롬프트를 텍스트로 변환
        prompt_parts = []

        # 시스템 컨텍스트
        system_ctx = self.coldmail_prompt["system_context"]
        prompt_parts.append(f"당신은 {system_ctx['company']}의 {system_ctx['name']}({system_ctx['role']})입니다.")
        prompt_parts.append(f"목표: {system_ctx['objective']}")

        # 분석할 데이터 제공
        prompt_parts.append("\n=== 분석 데이터 ===")
        prompt_parts.append("## 상품 페이지 정보:")
        prompt_parts.append(product_info)
        prompt_parts.append("\n## 고객 리뷰 데이터:")
        prompt_parts.append(review_text)

        # 실행 지침
        prompt_parts.append("\n=== 실행 지침 ===")
        for step_key, step_desc in self.coldmail_prompt["execution_flow"].items():
            prompt_parts.append(f"{step_key}: {step_desc}")

        # 이메일 생성 규칙
        email_rules = self.coldmail_prompt["email_generation_rules"]["structure"]
        prompt_parts.append("\n=== 이메일 구조 ===")
        prompt_parts.append(f"제목: {email_rules['subject_line']}")
        prompt_parts.append(f"인사말: {email_rules['opening']}")

        # AIDA 분석 규칙
        prompt_parts.append("\n=== AIDA 분석 규칙 ===")
        prompt_parts.append(email_rules["main_content"]["mandatory_structure"])

        # 품질 체크리스트
        checklist = self.coldmail_prompt["quality_checklist"]["before_sending"]
        prompt_parts.append("\n=== 품질 체크리스트 ===")
        for item in checklist:
            prompt_parts.append(f"- {item}")

        prompt_parts.append("\n위 지침에 따라 전문적인 콜드메일을 작성해주세요.")

        return "\n".join(prompt_parts)

    async def process_complete_workflow(
        self,
        image_paths: List[str],
        reviews_file_path: str
    ) -> Dict[str, Any]:
        """
        완전한 2단계 워크플로우 실행
        """
        logger.info("2단계 워크플로우 시작")

        try:
            # Stage 1: OCR 및 데이터 추출
            stage1_result = await self.stage1_ocr_extraction(image_paths)

            # Stage 2: 콜드메일 생성
            cold_email = await self.stage2_coldmail_generation(
                stage1_result,
                reviews_file_path
            )

            # 최종 결과
            final_result = {
                "workflow": "two_stage_processing",
                "stage1_result": stage1_result,
                "stage2_result": {
                    "cold_email": cold_email,
                    "reviews_processed": reviews_file_path,
                    "generated_at": pd.Timestamp.now().isoformat()
                },
                "summary": {
                    "images_processed": len(image_paths),
                    "reviews_file": reviews_file_path,
                    "success": True,
                    "completed_at": pd.Timestamp.now().isoformat()
                }
            }

            logger.info("2단계 워크플로우 완료")
            return final_result

        except Exception as e:
            logger.error(f"2단계 워크플로우 실패: {e}")
            raise

    def _add_to_pending_list(self, cold_email: str, product_info: str = "") -> bool:
        """콜드메일 생성 결과를 발송대기 리스트에 추가"""
        try:
            # 콜드메일에서 제목과 본문 분리 (간단한 파싱)
            email_subject = "상세페이지 개선 제안"
            email_content = cold_email

            # 상품 정보에서 스토어명과 상품명 추출 시도
            store_name = self._extract_store_name_from_content(cold_email, product_info)
            product_name = self._extract_product_name_from_content(cold_email, product_info)

            # 콜드메일 결과 딕셔너리 구성
            coldmail_result = {
                'subject': email_subject,
                'body': cold_email,
                'store_name': store_name,
                'product_name': product_name
            }

            # EmailSenderManager를 통해 발송대기 리스트에 추가
            success = self.email_sender_manager.add_coldmail_result(coldmail_result)

            if success:
                logger.info(f"발송대기 리스트 추가 완료: {store_name} - {product_name}")
            else:
                logger.warning("발송대기 리스트 추가 실패")

            return success

        except Exception as e:
            logger.error(f"발송대기 리스트 추가 중 오류: {e}")
            return False

    def _extract_store_name_from_content(self, cold_email: str, product_info: str) -> str:
        """콜드메일 내용에서 스토어명 추출"""
        try:
            # 상품 정보에서 브랜드명 패턴 찾기
            import re

            # 일반적인 브랜드명 패턴들
            brand_patterns = [
                r'브랜드[:\s]*([가-힣A-Za-z0-9\s]+)',
                r'제조사[:\s]*([가-힣A-Za-z0-9\s]+)',
                r'판매자[:\s]*([가-힣A-Za-z0-9\s]+)',
                r'([가-힣A-Za-z0-9]+)\s*제품',
                r'([가-힣A-Za-z0-9]+)\s*스토어'
            ]

            # 상품 정보에서 브랜드명 추출 시도
            content_to_search = f"{product_info}\n{cold_email}"

            for pattern in brand_patterns:
                matches = re.findall(pattern, content_to_search)
                if matches:
                    brand_name = matches[0].strip()
                    if len(brand_name) > 1 and len(brand_name) < 20:
                        return brand_name

            return "미확인"

        except Exception:
            return "미확인"

    def _extract_text_with_tesseract(self, image_path: str) -> str:
        """Tesseract를 사용한 무료 OCR 처리"""
        try:
            import pytesseract
            from PIL import Image

            # Tesseract 설정
            pytesseract.pytesseract.tesseract_cmd = self.config.ocr.tesseract_cmd

            # 이미지 로드 및 OCR
            image = Image.open(image_path)

            # 언어 설정 (한국어 + 영어)
            languages = '+'.join(self.config.ocr.languages)

            # OCR 실행
            extracted_text = pytesseract.image_to_string(
                image,
                lang=languages,
                config=f'--psm {self.config.ocr.psm} --oem {self.config.ocr.oem}'
            )

            logger.info(f"Tesseract OCR 완료: {len(extracted_text)}자 추출")
            return extracted_text.strip()

        except Exception as e:
            logger.error(f"Tesseract OCR 실패: {e}")
            return f"OCR 처리 실패: {str(e)}"

    def _extract_product_name_from_content(self, cold_email: str, product_info: str) -> str:
        """콜드메일 내용에서 상품명 추출"""
        try:
            import re

            # 상품명 패턴들
            product_patterns = [
                r'상품명[:\s]*([가-힣A-Za-z0-9\s\-\/]+)',
                r'제품명[:\s]*([가-힣A-Za-z0-9\s\-\/]+)',
                r'([가-힣A-Za-z0-9\s\-\/]{5,50})\s*(?:상품|제품)'
            ]

            content_to_search = f"{product_info}\n{cold_email}"

            for pattern in product_patterns:
                matches = re.findall(pattern, content_to_search)
                if matches:
                    product_name = matches[0].strip()
                    if len(product_name) > 3 and len(product_name) < 100:
                        return product_name

            return "미확인"

        except Exception:
            return "미확인"

    def _extract_text_with_tesseract(self, image_path: str) -> str:
        """Tesseract를 사용한 무료 OCR 처리"""
        try:
            import pytesseract
            from PIL import Image

            # Tesseract 설정
            pytesseract.pytesseract.tesseract_cmd = self.config.ocr.tesseract_cmd

            # 이미지 로드 및 OCR
            image = Image.open(image_path)

            # 언어 설정 (한국어 + 영어)
            languages = '+'.join(self.config.ocr.languages)

            # OCR 실행
            extracted_text = pytesseract.image_to_string(
                image,
                lang=languages,
                config=f'--psm {self.config.ocr.psm} --oem {self.config.ocr.oem}'
            )

            logger.info(f"Tesseract OCR 완료: {len(extracted_text)}자 추출")
            return extracted_text.strip()

        except Exception as e:
            logger.error(f"Tesseract OCR 실패: {e}")
            return f"OCR 처리 실패: {str(e)}"