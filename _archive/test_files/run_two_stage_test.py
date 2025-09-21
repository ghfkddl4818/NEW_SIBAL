#!/usr/bin/env python3
"""
2단계 분리 처리 시스템 테스트 스크립트

사용자의 실제 워크플로우에 맞춘 테스트:
1. 상품 이미지 → OCR/데이터 추출 (온도 0.3)
2. 추출된 데이터 + 리뷰(~300개) → 콜드메일 생성 (온도 0.3)
"""

import asyncio
import json
from pathlib import Path
from loguru import logger

from core.config import load_config
from llm.two_stage_processor import TwoStageProcessor


async def main():
    """2단계 처리 테스트 메인 함수"""
    logger.info("🚀 2단계 분리 처리 시스템 테스트 시작")

    try:
        # 설정 로드
        config = load_config()
        logger.info("✅ 설정 로드 완료")

        # 2단계 처리기 초기화
        processor = TwoStageProcessor(config)
        logger.info("✅ 2단계 처리기 초기화 완료")

        # 테스트 데이터 경로
        data_dir = Path(config.paths.input_images_dir)
        reviews_dir = Path(config.paths.input_reviews_dir)

        # 이미지 파일 찾기
        image_files = list(data_dir.glob("*.png")) + list(data_dir.glob("*.jpg")) + list(data_dir.glob("*.jpeg"))
        if not image_files:
            logger.warning(f"⚠️  이미지 파일이 없습니다: {data_dir}")
            # 샘플 이미지 생성 안내
            logger.info("샘플 이미지를 data/product_images/ 폴더에 추가하세요")
            return

        # 리뷰 파일 찾기
        review_files = list(reviews_dir.glob("*.csv"))
        if not review_files:
            logger.warning(f"⚠️  리뷰 파일이 없습니다: {reviews_dir}")
            # 샘플 리뷰 생성 안내
            logger.info("샘플 리뷰 파일을 data/reviews/ 폴더에 추가하세요")
            return

        # 첫 번째 리뷰 파일 사용
        review_file = str(review_files[0])
        image_paths = [str(f) for f in image_files[:3]]  # 최대 3개 이미지

        logger.info(f"📊 처리할 데이터:")
        logger.info(f"   - 이미지: {len(image_paths)}개")
        logger.info(f"   - 리뷰 파일: {review_file}")

        # ===== STAGE 1: OCR 및 데이터 추출 =====
        logger.info("🔍 Stage 1 시작: OCR 및 데이터 추출")
        stage1_result = await processor.stage1_ocr_extraction(image_paths)

        logger.info("✅ Stage 1 완료")
        logger.info(f"   - 처리된 이미지: {stage1_result['total_images']}개")

        # Stage 1 결과 저장
        output_dir = Path(config.paths.output_root_dir)
        output_dir.mkdir(exist_ok=True)

        stage1_output = output_dir / "stage1_ocr_result.json"
        with open(stage1_output, 'w', encoding='utf-8') as f:
            json.dump(stage1_result, f, ensure_ascii=False, indent=2)
        logger.info(f"   - Stage 1 결과 저장: {stage1_output}")

        # ===== STAGE 2: 콜드메일 생성 =====
        logger.info("📧 Stage 2 시작: 콜드메일 생성")
        cold_email = await processor.stage2_coldmail_generation(
            stage1_result,
            review_file
        )

        logger.info("✅ Stage 2 완료")

        # Stage 2 결과 저장
        stage2_output = output_dir / "stage2_coldmail_result.txt"
        with open(stage2_output, 'w', encoding='utf-8') as f:
            f.write(cold_email)
        logger.info(f"   - Stage 2 결과 저장: {stage2_output}")

        # ===== 완전한 워크플로우 테스트 =====
        logger.info("🎯 완전한 2단계 워크플로우 테스트")
        complete_result = await processor.process_complete_workflow(
            image_paths,
            review_file
        )

        logger.info("✅ 완전한 워크플로우 완료")

        # 최종 결과 저장
        final_output = output_dir / "two_stage_complete_result.json"
        with open(final_output, 'w', encoding='utf-8') as f:
            json.dump(complete_result, f, ensure_ascii=False, indent=2)
        logger.info(f"   - 최종 결과 저장: {final_output}")

        # 결과 요약
        logger.info("🎉 테스트 완료 요약:")
        logger.info(f"   - Stage 1 (OCR): {complete_result['summary']['images_processed']}개 이미지 처리")
        logger.info(f"   - Stage 2 (Email): 리뷰 데이터 기반 콜드메일 생성")
        logger.info(f"   - 온도값: 0.3 (Google AI Studio 방식)")
        logger.info(f"   - 결과 폴더: {output_dir}")

        # 생성된 콜드메일 미리보기
        logger.info("\n📧 생성된 콜드메일 미리보기:")
        logger.info("=" * 50)
        email_preview = complete_result["stage2_result"]["cold_email"]
        if len(email_preview) > 500:
            logger.info(email_preview[:500] + "\n... (더 보려면 출력 파일 확인)")
        else:
            logger.info(email_preview)
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())