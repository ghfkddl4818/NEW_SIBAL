# 프로젝트 컨텍스트: AI 콜드메일 자동생성 시스템

## 프로젝트 개요
**목적**: 이커머스 상품 상세페이지 이미지와 고객 리뷰 데이터를 분석하여 전환율 개선을 위한 개인화된 콜드메일 자동 생성

**최종 목표**: 데이터 기반의 고품질 영업 제안 자료를 대량으로, 신속하게 생성하여 답장률 극대화

## 기술 스택
- **Python 3.13** + 주요 라이브러리 (pydantic, typer, pandas 등)
- **AI 모델**: Vertex AI + Gemini 2.5 Pro (ADC 인증, API 키 불필요)
- **OCR**: Tesseract (한국어+영어)
- **개발환경**: Windows 10, Claude Code + GitHub 연동

## 파이프라인 구조 (7단계)
1. **DISCOVER**: 입력 파일 탐색 (이미지/리뷰)
2. **OCR**: Tesseract로 상세페이지 이미지→텍스트 추출
3. **OCR 정제**: 텍스트 정리 (줄바꿈, 공백, 이상문자 제거)
4. **LLM 콜 #1**: 제품 정보 구조화 (product_structuring.json)
5. **리뷰 정규화**: 엑셀/CSV 리뷰 데이터 표준화
6. **LLM 콜 #2**: 콜드메일 생성 (cold_email.json)
7. **최종 조립**: [광고] 접두사, 길이 조정, 민감표현 완곡처리

## 핵심 페르소나
- **이름**: 이승윤
- **소속**: 데이터그로스 파트너스
- **역할**: 이커머스 데이터 분석 컨설턴트
- **어조**: 전문적이되 이해하기 쉬운 설명, 데이터 근거 팩트 중심

## 프로젝트 현황
- **MVP 상태**: 완성 (과거 스모크테스트 통과 경험)
- **GitHub**: ghfkddl4818/all_in_one_sibal (Private)
- **현재 위치**: E:\VSC\all_in_one\all_in_one_new\all_in_one
- **현재 문제**: config.yaml 경로 오류로 테스트 실패

## 주요 정책
- **광고 표기**: 제목 앞 [광고] 접두사 필수
- **이메일 길이**: 350-600자 (하드 제한)
- **톤**: consultant(전문가) vs student(학습자) 선택 가능
- **민감표현**: 의학/효능/과장 표현 자동 완곡 처리
- **예산**: 건당 최대 $0.05 제한

## 핵심 파일 구조
```
app/
├── main.py              # CLI 엔트리 포인트
└── pipeline.py          # 메인 파이프라인 오케스트레이터

core/
├── config.py           # 설정 로드/검증
├── logger.py           # 파일+콘솔 로깅
├── schemas.py          # Pydantic 데이터 모델
└── limiter.py          # 레이트리밋/예산관리

llm/
├── gemini_client.py    # Vertex AI 연동
└── prompts/
    ├── product_structuring.json
    └── cold_email.json  # 핵심 콜드메일 프롬프트

compose/
└── composer.py         # 최종 정책 보정

config/
└── config.yaml         # 전체 설정 (현재 경로 오류)
```

## 다음 단계 로드맵
1. **현재**: 경로 문제 해결 + 테스트 통과
2. **1단계**: A/B 테스트용 제목 2개 생성
3. **2단계**: 개인화 변수 강화 (스토어명, 상품명 자동삽입)
4. **3단계**: 대량 처리 + 발송 큐 시스템
5. **4단계**: 답장률 추적 + 성과 분석

## 문제 해결 우선순위
1. config/config.yaml 경로를 상대경로로 수정
2. data/ 폴더 생성 및 샘플 데이터 준비
3. python run_email_smoke.py 테스트 통과
4. outputs/ 폴더에서 email_final.txt 생성 확인