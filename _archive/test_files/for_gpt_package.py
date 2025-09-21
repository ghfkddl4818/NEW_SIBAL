#!/usr/bin/env python3
"""
GPT용 코드 패키지 생성기
핵심 소스코드만 추출하여 20MB 이하로 압축
"""

import os
import shutil
from pathlib import Path
import zipfile

def create_gpt_package():
    """GPT 분석용 패키지 생성"""

    # 현재 디렉토리
    source_dir = Path(".")
    package_dir = Path("./gpt_package")
    zip_path = Path("./complete_automation_for_gpt.zip")

    # 기존 패키지 삭제
    if package_dir.exists():
        shutil.rmtree(package_dir)
    if zip_path.exists():
        zip_path.unlink()

    # 패키지 디렉토리 생성
    package_dir.mkdir()

    # 포함할 핵심 파일/폴더들
    include_patterns = [
        # 핵심 소스코드
        "*.py",
        "*.yaml",
        "*.yml",
        "*.json",
        "*.txt",
        "*.md",

        # 핵심 디렉토리
        "core/",
        "llm/",
        "compose/",
        "config/",
        "gui/",
        "data/reviews/", # 리뷰 데이터만
        "ocr/",
        "app/",
    ]

    # 제외할 패턴들
    exclude_patterns = [
        "build/",
        "dist/",
        "CompleteAutomation_Portable/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.exe",
        "*.spec",
        ".git/",
        "outputs/vertex_test_*",
        "data/product_images/", # 이미지는 용량이 큼
        "archive/",
        "tests/",
        "*.log",
        "gpt_package/",
        "complete_automation_for_gpt.zip"
    ]

    def should_include(file_path: Path) -> bool:
        """파일 포함 여부 판단"""
        path_str = str(file_path)

        # 제외 패턴 확인
        for pattern in exclude_patterns:
            if pattern.rstrip('/') in path_str:
                return False

        # 포함 패턴 확인
        for pattern in include_patterns:
            if pattern.endswith('/'):
                # 디렉토리 패턴
                if pattern.rstrip('/') in path_str:
                    return True
            else:
                # 파일 패턴
                if file_path.match(pattern):
                    return True

        return False

    # 파일 복사
    total_size = 0
    file_count = 0

    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)

        # 제외 디렉토리 스킵
        dirs[:] = [d for d in dirs if not any(pattern.rstrip('/') in str(root_path / d) for pattern in exclude_patterns)]

        for file in files:
            file_path = root_path / file

            if should_include(file_path):
                # 상대 경로 계산
                rel_path = file_path.relative_to(source_dir)
                dest_path = package_dir / rel_path

                # 디렉토리 생성
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # 파일 복사
                try:
                    shutil.copy2(file_path, dest_path)
                    size = dest_path.stat().st_size
                    total_size += size
                    file_count += 1

                    print(f"[OK] {rel_path} ({size:,} bytes)")

                    # 20MB 체크
                    if total_size > 20 * 1024 * 1024:
                        print(f"[WARNING] 20MB 초과 위험: {total_size / (1024*1024):.1f}MB")

                except Exception as e:
                    print(f"[ERROR] 복사 실패: {rel_path} - {e}")

    # README 생성
    readme_content = f"""# Complete Automation System - GPT Analysis Package

## 📋 프로젝트 개요
이커머스 상품 이미지 OCR + 콜드메일 자동 생성 시스템

## 🏗️ 시스템 아키텍처
```
Stage 1: Tesseract OCR (무료)
    └── 상품 이미지 → 텍스트 추출

Stage 2: Gemini AI (유료)
    └── 추출된 텍스트 + 리뷰 → 콜드메일 생성

Stage 3: 발송 관리
    └── 자동으로 엑셀 발송대기 리스트에 등록
```

## 📁 주요 구조
- `core/`: 설정 및 안전 모니터링
- `llm/`: AI 처리 (Gemini 클라이언트, 2단계 프로세서)
- `compose/`: 이메일 발송 관리 시스템
- `gui/`: 사용자 인터페이스
- `ocr/`: Tesseract OCR 엔진
- `config/`: 설정 파일들

## 🚀 핵심 기능
1. **무료 OCR**: Tesseract로 이미지에서 텍스트 추출
2. **AI 콜드메일**: Gemini로 개인화된 이메일 생성
3. **발송 관리**: 자동 엑셀 발송대기 리스트 관리
4. **비용 안전장치**: API 사용량 모니터링 및 제한
5. **기존 DB 연동**: 이커머스 데이터베이스 연동

## 📊 패키지 정보
- 총 파일: {file_count:,}개
- 총 크기: {total_size / (1024*1024):.1f}MB
- 생성일: {Path().cwd().name}

## 💡 추가 기능 아이디어 요청
이 시스템을 기반으로 추가할 수 있는 기능들에 대한 아이디어를 제안해주세요.
"""

    with open(package_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    # ZIP 파일 생성
    print(f"\n[PACKAGE] ZIP 파일 생성 중...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)

    # 결과 출력
    zip_size = zip_path.stat().st_size
    print(f"\n[SUCCESS] 패키지 생성 완료!")
    print(f"[DIR] 디렉토리: {package_dir}")
    print(f"[ZIP] ZIP 파일: {zip_path}")
    print(f"[SIZE] ZIP 크기: {zip_size / (1024*1024):.1f}MB")
    print(f"[COUNT] 파일 개수: {file_count:,}개")
    print(f"[ORIG] 원본 크기: {total_size / (1024*1024):.1f}MB")
    print(f"[COMPRESS] 압축률: {(1 - zip_size/total_size)*100:.1f}%")

    if zip_size > 20 * 1024 * 1024:
        print(f"[WARNING] 경고: ZIP 파일이 20MB를 초과했습니다!")
    else:
        print(f"[OK] 20MB 이내: GPT 업로드 가능!")

    # 임시 디렉토리 정리
    shutil.rmtree(package_dir)

if __name__ == "__main__":
    create_gpt_package()