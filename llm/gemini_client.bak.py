from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, Optional, Tuple

import vertexai
from vertexai.generative_models import GenerativeModel

# core.limiter의 RateLimiter를 이 모듈에서 그대로 내보내기
from core.limiter import RateLimiter as _CoreRateLimiter
RateLimiter = _CoreRateLimiter


class BudgetGuard:
    """아주 단순한 예산 가드(필요 최소한)."""
    def __init__(self, max_cost_per_job_usd: Optional[float] = None):
        self.max = max_cost_per_job_usd
        self.spent = 0.0

    def add(self, usd: float) -> None:
        try:
            self.spent += float(usd or 0.0)
        except Exception:
            return
        if self.max is not None and self.spent > self.max:
            raise RuntimeError(
                f"Budget exceeded: {self.spent:.4f} > {self.max:.4f}"
            )


def _clean_text(s: str) -> str:
    """BOM/코드펜스/앞뒤 공백 제거."""
    if not s:
        return ""
    s = s.replace("\r\n", "\n").lstrip("\ufeff").strip()  # BOM 제거 + 트림

    # 맨 앞에 코드펜스(``` 또는 ```json) 있으면 제거
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1 :]
        # 맨 끝 '```' 제거
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def _extract_json(text: str) -> Dict[str, Any]:
    """
    모델이 ```json ... ``` 로 감싸거나, 앞뒤에 잡소리/공백/BOM이 있어도
    JSON만 뽑아 파싱한다.
    """
    if not text:
        raise ValueError("empty model output")

    s = _clean_text(text)

    # 1) 바로 파싱 시도
    try:
        return json.loads(s)
    except Exception:
        pass

    # 2) 본문 안에서 { ... } 범위 추출해서 파싱
    m = re.search(r"\{[\s\S]*\}", s)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    # 3) 리스트 JSON일 수도 있으니 [ ... ] 범위도 시도
    m = re.search(r"\[[\s\S]*\]", s)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    raise ValueError("no valid JSON found in model output")


def _split_subject_body(text: str) -> Tuple[str, str]:
    """
    JSON이 안 나왔을 때, 일반 텍스트를 subject/body로 나눠서 폴백 생성.
    - 'Subject:' 접두가 있으면 그 줄을 제목으로
    - 없으면 첫 빈 줄 전까지 첫 블록의 첫 줄을 제목 후보로
    - 너무 길면 80자로 자름
    """
    s = _clean_text(text)
    if not s:
        return ("Untitled", "")

    # 1) 명시적 Subject: 라인
    for line in s.splitlines():
        lt = line.strip()
        if lt.lower().startswith("subject:"):
            subj = lt.split(":", 1)[1].strip() or "Untitled"
            body = s.replace(line, "", 1).strip()
            if len(subj) > 80:
                subj = subj[:80] + "…"
            return (subj, body)

    # 2) 첫 단락의 첫 줄을 제목으로
    blocks = s.split("\n\n")
    first_block = blocks[0].strip()
    first_line = first_block.splitlines()[0].strip() if first_block else "Untitled"
    if len(first_line) > 80:
        first_line = first_line[:80] + "…"

    # 본문은 전체에서 첫 줄을 제거한 나머지
    rest = s[len(first_line):].lstrip()
    return (first_line or "Untitled", rest)


class GeminiClient:
    """
    Vertex AI(Gemini) 호출 래퍼.
    pipeline.py에서는 await client.generate(system_json, user_payload) 형태로 사용.
    """
    def __init__(self, cfg):
        # Vertex 초기화(ADC) — provider가 vertex일 때만
        if getattr(cfg.llm, "provider", "").lower() == "vertex":
            vertex = getattr(cfg, "vertex", None)
            if vertex is None:
                raise ValueError("cfg.vertex is required when provider=vertex")
            vertexai.init(project=vertex.project_id, location=vertex.location)
        else:
            # 현재 구현은 Vertex 경로만 지원
            raise ValueError("Only provider=vertex is supported in this client.")

        self.model_name = getattr(cfg.llm, "model", "gemini-2.5-pro")
        self.temperature = getattr(cfg.llm, "temperature", 0.3)
        self.max_output_tokens = getattr(cfg.llm, "max_output_tokens", 1024)

        self.model = GenerativeModel(self.model_name)

    async def generate(self, system_json: Dict[str, Any], user_payload: str) -> Dict[str, Any]:
        """비동기 인터페이스: 내부는 to_thread로 동기 호출."""
        return await asyncio.to_thread(self._generate_sync, system_json, user_payload)

    # ------------------ 내부 동기 구현 ------------------ #
    def _build_prompt(self, system_json: Dict[str, Any], user_payload: str) -> str:
        rules = system_json.get("rules", [])
        schema = system_json.get("output_schema", "JSON")
        lines = [
            "You are a strict JSON generator. Return ONLY valid JSON, no prose.",
            "Do NOT use code fences.",
            "Output MUST be a single JSON object.",
            "[SYSTEM_RULES]",
            *[f"- {r}" for r in rules],
            f"[OUTPUT_SCHEMA] {schema}",
            "[INPUT]",
            user_payload,
        ]
        return "\n".join(lines)

    def _gen_once(self, prompt: str) -> str:
        resp = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
                "response_mime_type": "application/json",  # ★ JSON 강제 요청
            },
            safety_settings=None,
        )
        # SDK가 .text 제공 (없으면 parts에서 조합)
        text = getattr(resp, "text", None)
        if not text:
            try:
                c0 = resp.candidates[0]
                parts = getattr(c0.content, "parts", []) or []
                text = "".join(getattr(p, "text", "") for p in parts).strip()
            except Exception:
                text = ""
        return text

    def _generate_sync(self, system_json: Dict[str, Any], user_payload: str) -> Dict[str, Any]:
        prompt = self._build_prompt(system_json, user_payload)

        # 1차 시도
        text = self._gen_once(prompt)
        try:
            return _extract_json(text)
        except Exception:
            pass

        # 2차 시도: 더 강하게 JSON만 요구
        strict_prompt = (
            prompt
            + "\n\nReturn ONLY strict JSON. Do NOT use code fences. Do NOT include any extra text."
        )
        text2 = self._gen_once(strict_prompt)
        try:
            return _extract_json(text2)
        except Exception:
            # 3차 폴백: 그냥 텍스트를 subject/body로 감싸서 JSON으로 반환
            cleaned = _clean_text(text2 or text)
            subj, body = _split_subject_body(cleaned)
            return {"subject": subj, "body": body, "_raw": cleaned}
