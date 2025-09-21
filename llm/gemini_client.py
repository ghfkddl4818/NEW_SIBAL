# llm/gemini_client.py (구버전 SDK 호환, Schema 미사용)
from __future__ import annotations
import json, re, asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationResponse, Part, Content, Image

# 안전 모니터 import
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.safety_monitor import api_safety

@dataclass
class BudgetGuard:
    max_cost_usd: float = 0.0  # reserved

@dataclass
class RateLimiter:
    rpm_soft: int = 60
    tpm_soft: int = 120_000

class GeminiClient:
    """
    provider='vertex' (ADC) 전용. API Key 불요.
    cfg.vertex.project_id / cfg.vertex.location 필요.
    """
    def __init__(self, cfg):
        if getattr(cfg, 'llm', None) and getattr(cfg.llm, 'provider', '').lower() != 'vertex':
            raise RuntimeError("This GeminiClient is for provider='vertex' only.")

        vertex_cfg = getattr(cfg, 'vertex', None)
        if not vertex_cfg or not getattr(vertex_cfg, 'project_id', None):
            raise RuntimeError("Vertex project_id is not configured. Set VERTEX_PROJECT_ID or update config.vertex.project_id.")

        location = getattr(vertex_cfg, 'location', 'global') or 'global'
        vertexai.init(project=vertex_cfg.project_id, location=location)

        self.model_name: str = getattr(cfg.llm, 'model', 'gemini-2.5-pro')
        self.temperature: float = float(getattr(cfg.llm, 'temperature', 0.2))
        self.max_output_tokens: int = int(getattr(cfg.llm, 'max_output_tokens', 1024))

        self.model = GenerativeModel(self.model_name)
        # 구버전 SDK 호환: dict로 generation_config 전달
        self.generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "response_mime_type": "application/json",
        }

    # -------- JSON 가드 --------
    def _clean_json_text(self, s: str) -> str:
        s = (s or "").strip()
        if s.startswith("```"):
            parts = s.split("```")
            if len(parts) > 1:
                s = parts[1]
                if s.lower().startswith("json"):
                    s = s[4:]
        return s.strip()

    _first_object_regex = re.compile(r"\{.*\}", re.S)
    _first_array_regex  = re.compile(r"\[.*\]", re.S)

    def _extract_first_json_block(self, s: str) -> Optional[str]:
        m = self._first_object_regex.search(s)
        if m:
            return m.group(0)
        m = self._first_array_regex.search(s)
        if m:
            return m.group(0)
        return None

    def _robust_json_loads(self, text: str) -> Any:
        s = self._clean_json_text(text)
        block = self._extract_first_json_block(s) or s
        # 1차: 그대로
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            # 2차: 단일 인용부호 → 쌍따옴표 치환(임시 보정)
            fixed = block.replace("'", '"')
            return json.loads(fixed)

    def _extract_text(self, resp: Any) -> str:
        txt = getattr(resp, "text", None)
        if isinstance(txt, str) and txt.strip():
            return txt
        try:
            cands = getattr(resp, "candidates", None) or []
            for c in cands:
                content = getattr(c, "content", None)
                if not content:
                    continue
                parts = getattr(content, "parts", None) or []
                buf = []
                for p in parts:
                    t = getattr(p, "text", None)
                    if isinstance(t, str):
                        buf.append(t)
                if buf:
                    return "\n".join(buf)
        except Exception:
            pass
        return ""

    def _log_usage_safely(self, resp: Any) -> None:
        usage = getattr(resp, "usage_metadata", None)
        if not usage:
            return
        g = lambda k: getattr(usage, k, None)
        try:
            print(f"[TOKENS] prompt={g('prompt_token_count')}, candidates={g('candidates_token_count')}, total={g('total_token_count')}")
        except Exception:
            pass

    # -------- 이미지 처리 메서드 추가 --------
    async def process_image_with_text(self, image_path: str, prompt: str, temperature: float = None) -> str:
        """
        이미지와 텍스트를 함께 처리 (텍스트 응답)
        """
        import PIL.Image

        # 온도값 설정
        temp = temperature if temperature is not None else self.temperature
        text_config = {
            "temperature": temp,
            "max_output_tokens": self.max_output_tokens,
        }

        # 이미지 로드
        image = Image.load_from_file(image_path)

        # Content 형식으로 구성
        content = [
            Content(
                role="user",
                parts=[
                    Part.from_text(prompt),
                    Part.from_image(image)
                ]
            )
        ]

        # 안전장치를 통한 생성
        def _safe_generate():
            return self.model.generate_content(content, generation_config=text_config)

        resp: GenerationResponse = await asyncio.to_thread(
            api_safety.safe_api_call,
            _safe_generate,
            estimated_cost=0.02  # 이미지+텍스트 처리 예상 비용
        )

        self._log_usage_safely(resp)
        return self._extract_text(resp)

    async def process_text_only(self, prompt: str, temperature: float = None) -> str:
        """
        텍스트만 처리 (텍스트 응답)
        """
        # 온도값 설정
        temp = temperature if temperature is not None else self.temperature
        text_config = {
            "temperature": temp,
            "max_output_tokens": self.max_output_tokens,
        }

        # 안전장치를 통한 생성
        def _safe_generate():
            return self.model.generate_content(prompt, generation_config=text_config)

        resp: GenerationResponse = await asyncio.to_thread(
            api_safety.safe_api_call,
            _safe_generate,
            estimated_cost=0.01  # 텍스트 전용 처리 예상 비용
        )

        self._log_usage_safely(resp)
        return self._extract_text(resp)

    # -------- 메인 호출 --------
    async def generate(self, system_json: Dict[str, Any], user_payload: str) -> Any:
        """
        system_json: prompts/*.json dict (keys: role, rules/constraints, output_schema, optional schema_definition)
        user_payload: 입력 텍스트
        """
        schema_name = str(system_json.get("output_schema") or "").strip()
        rules = system_json.get("rules") or system_json.get("constraints")

        # 일부 모델/버전에서 system 역할 미지원 → 규칙+입력을 단일 user 프롬프트로 합침
        sys_text = json.dumps({"schema": schema_name, "rules": rules}, ensure_ascii=False)
        full_prompt = (
            "You MUST reply with JSON only. No code fences, no extra text.\n"
            f"System Instructions:\n{sys_text}\n\n"
            f"User Payload:\n{user_payload or ''}"
        )
        prompt = [{'role': 'user', 'parts': [{'text': full_prompt}]}]

        # 1차 호출
        raw_text = ""

        resp: GenerationResponse = await asyncio.to_thread(
            self.model.generate_content,
            prompt,
            generation_config=self.generation_config,
        )
        self._log_usage_safely(resp)
        text_primary = self._extract_text(resp)
        raw_text = text_primary or ""

        try:
            obj = self._robust_json_loads(text_primary)
        except Exception:
            # 2차(재시도): 첫 응답 원문을 넘겨 "JSON만"으로 변환 요구
            repair = (
                "Convert the following content to JSON ONLY. "
                "Do not add any explanations or markdown. "
                f"Required keys: {['subject','body'] if schema_name.lower()=='emaildraft' else 'follow schema'}.\n\n"
                f"CONTENT:\n{text_primary}"
            )
            resp2: GenerationResponse = await asyncio.to_thread(
                self.model.generate_content,
                [{'role': 'user', 'parts': [{'text': repair}]}],
                generation_config=self.generation_config,
            )
            self._log_usage_safely(resp2)
            text2 = self._extract_text(resp2)
            raw_text = text2 or text_primary
            try:
                obj = self._robust_json_loads(text2)
            except Exception:
                raise ValueError("no valid JSON")

        # ProductStructured는 dict 강제
        if schema_name and schema_name.lower() == "productstructured" and not isinstance(obj, dict):
            obj = {}
        elif isinstance(obj, str):
            try:
                obj = self._robust_json_loads(obj)
            except Exception:
                obj = {"_raw": raw_text, "text": obj}

        if isinstance(obj, dict):
            obj.setdefault("_raw", raw_text)

        return obj
