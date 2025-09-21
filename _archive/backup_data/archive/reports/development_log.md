# 개발 과정 로그

## 개발 히스토리
- **초기 개발**: GPT + Gemini CLI 조합으로 MVP 구축
- **테스트 검증**: 스모크 테스트 통과, 콜드메일 생성 확인
- **현재 전환**: Claude Code로 작업 방식 변경
- **GitHub 연동**: Private repo (ghfkddl4818/all_in_one_sibal) 업로드 완료

## 주요 완성 기능

### 1. OCR 처리
- **Tesseract 연동**: 한국어+영어 동시 처리
- **경로**: E:/Tesseract/tesseract.exe
- **파일**: ocr/engine.py, ocr/postproc.py

### 2. AI 모델 연동
- **Vertex AI + Gemini**: ADC 인증 방식 (API 키 불필요)
- **모델**: Gemini 2.5 Pro
- **파일**: llm/gemini_client.py
- **주요 특징**: JSON 파싱 가드, 재시도 로직, 예산 제한

### 3. 콜드메일 프롬프트
- **핵심 파일**: llm/prompts/cold_email.json
- **구조**: AIDA 프레임워크 + Gap Analysis
- **페르소나**: 이승윤(데이터그로스 파트너스)
- **특징**: 12가지 상세페이지 제작 원칙, 단계별 조건부 분석

### 4. 정책 보정 시스템
- **파일**: compose/composer.py
- **기능**:
  - [광고] 접두사 자동 추가
  - 350-600자 길이 강제 조정
  - 민감표현 완곡 처리 (치료→관리, 효능→도움 등)
  - 톤앤매너 적용 (consultant/student)

### 5. 데이터 스키마
- **파일**: core/schemas.py
- **주요 모델**:
  - ProductStructured: OCR 결과 구조화
  - ReviewsNormalized: 리뷰 데이터 표준화
  - EmailDraft: 콜드메일 초안

## 과거 테스트 결과

### 성공 케이스
- `python run_email_smoke.py` 통과
- outputs/smoke_email.log 정상 생성
- email_final.txt/json 생성 확인
- [광고] 접두사, 길이 제한, 민감표현 처리 모두 적용

### 발견된 문제들
1. **JSON 파싱 실패**: Gemini 응답이 코드펜스로 감싸져서 파싱 실패 → JSON 가드로 해결
2. **길이 부족**: 초기 이메일이 350자 미만 → composer.py 최소 길이 보장 로직 추가
3. **AIDA 단계 누락**: Interest 단계가 빠지는 문제 → 프롬프트 강화로 해결

## 현재 문제점

### 경로 오류
```
config/config.yaml의 절대 경로들:
- paths.input_images_dir: "./data/product_images"
- paths.input_reviews_dir: "./data/reviews"
- 실제 폴더 구조와 불일치로 FileNotFoundError 발생
```

### 누락된 리소스
- data/ 폴더 미생성
- 샘플 데이터 파일 없음

## 해결 방안

### 즉시 해결 필요
1. **config.yaml 수정**: 모든 경로를 현재 폴더 기준 상대경로로
2. **data 폴더 생성**: product_images/, reviews/ 하위폴더 포함
3. **샘플 데이터**: PNG 이미지 1개, CSV 리뷰 파일 1개

### 테스트 시나리오
1. `python run_email_smoke.py` 실행
2. outputs/ 폴더에 결과 확인
3. email_final.txt 내용 검증:
   - [광고] 접두사 존재
   - 350-600자 범위
   - AIDA 4단계 모두 포함
   - 민감표현 완곡처리

## 다음 개발 계획

### 단기 (1-2일)
- A/B 테스트용 제목 2개 생성
- 개인화 변수 강화 (스토어명, 상품명 자동삽입)
- 길이/톤 하드 클램프 규칙 정교화

### 중기 (1주)
- 대량 처리 시스템
- 발송 큐 CSV 생성
- 중복 체크 및 옵트아웃 관리

### 장기 (2주+)
- 답장률 추적 분석
- 성공 패턴 학습
- 자동 프롬프트 튜닝

## 기술 부채
- Windows 경로 처리 (UTF-8 강제)
- Tesseract 의존성 검증
- Vertex AI SDK 버전 호환성
- 메모리 사용량 최적화 (대량 처리시)