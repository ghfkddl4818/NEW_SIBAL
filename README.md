# 🎯 AI 콜드메일 2단계 분리 처리 시스템

## 📋 핵심 실행 파일들

### 🌟 **추천: 2단계 분리 처리 시스템**
```bash
start_two_stage_gui.bat
```
- 사용자 실제 워크플로우 맞춤
- Stage 1: OCR/데이터추출 → Stage 2: 콜드메일생성
- 온도값 0.3, 리뷰 300개 자동 샘플링

### 🔧 **기타 실행 파일들**
```bash
start_ultimate_system.bat  # 통합 자동화 시스템
start_gui.bat              # 기본 AI GUI
run_two_stage_test.py       # 2단계 테스트 (명령줄)
```

## 📁 **핵심 폴더 구조**

```
├── core/           # 설정 및 로깅
├── llm/            # AI 처리기 (2단계 시스템 포함)
├── gui/            # GUI 인터페이스들
├── data/           # 입력 데이터 (이미지, 리뷰)
├── outputs/        # 결과 파일들
├── config/         # 설정 파일
└── archive/        # 정리된 구 버전/보고서들
```

## 🚀 **사용법**

1. **이미지 준비**: `data/product_images/`에 상품 이미지 저장
2. **리뷰 준비**: `data/reviews/`에 CSV 형식 리뷰 저장
3. **실행**: `start_two_stage_gui.bat` 더블클릭
4. **결과 확인**: `outputs/` 폴더에서 생성된 콜드메일 확인

## 📞 **문의사항**

더 자세한 내용은 `프로젝트_진행상황_보고서_최종.md` 참조