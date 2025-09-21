# core/config.py  (?꾩껜 援먯껜?? UTF-8 ???沅뚯옣)
from __future__ import annotations
import os
import sys
from typing import List, Dict, Optional, Any
import yaml
from pydantic import BaseModel

# ---- 媛쒕퀎 ?뱀뀡 ?ㅽ궎留?----
class PathsConfig(BaseModel):
    input_images_dir: str
    input_reviews_dir: str
    output_root_dir: str
    prompts_dir: str

class OcrConfig(BaseModel):
    tesseract_cmd: str
    languages: List[str] = ["kor", "eng"]
    psm: int = 6
    oem: int = 3

class LlmConfig(BaseModel):
    provider: str = "vertex"             # vertex ?먮뒗 (援?gemini ??諛⑹떇
    model: str = "gemini-2.5-pro"
    temperature: float = 0.3
    max_output_tokens: int = 1024

class PolicyConfig(BaseModel):
    ad_prefix: bool = True
    tone_default: str = "consultant"
    email_min_chars: int = 350
    email_max_chars: int = 600
    suppress_risky_claims: bool = True

class BudgetConfig(BaseModel):
    max_cost_per_job_usd: float = 0.05

class RuntimeConfig(BaseModel):
    concurrency: int = 2
    rate_limit: Dict[str, int] = {"rpm_soft": 60, "tpm_soft": 120000}
    backoff: List[int] = [2, 4, 8]

# ---- ?낆텛媛: Vertex ?ㅼ젙 洹몃쫯 ----
class VertexConfig(BaseModel):
    project_id: str
    location: str = "global"             # ?꾩슂??"asia-northeast3"

# ---- ???꾩껜 ?ㅼ젙 ----
class AppConfig(BaseModel):
    paths: PathsConfig
    ocr: OcrConfig
    llm: LlmConfig
    policy: PolicyConfig
    budget: BudgetConfig
    runtime: RuntimeConfig
    vertex: Optional[VertexConfig] = None
    gemini_api_key: Optional[str] = None

def _resolve_config_path(path: str) -> str:
    resolved = path
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
        if not os.path.isabs(resolved):
            resolved = os.path.join(base_path, resolved)
    if not os.path.isabs(resolved):
        resolved = os.path.join(os.getcwd(), resolved)
    return resolved


def load_config_data(path: str = 'config/config.yaml') -> Dict[str, Any]:
    resolved_path = _resolve_config_path(path)
    with open(resolved_path, 'r', encoding='utf-8') as f:
        yaml_content = f.read()
    yaml_content = _expand_env_vars(yaml_content)
    return yaml.safe_load(yaml_content) or {}

    paths: PathsConfig
    ocr: OcrConfig
    llm: LlmConfig
    policy: PolicyConfig
    budget: BudgetConfig
    runtime: RuntimeConfig
    vertex: Optional[VertexConfig] = None   # ?낆텛媛 ?꾨뱶
    gemini_api_key: Optional[str] = None    # (援?吏곸젒??諛⑹떇 ?鍮?

def load_config(path: str = "config/config.yaml") -> AppConfig:
    data = load_config_data(path)
    cfg = AppConfig(**data)

    # provider가 'vertex'면 ADC 사용 → GEMINI_API_KEY 필요 없음
    # 그 외(provider가 다른 케이스)면 환경변수로 키 필수
    if cfg.llm.provider.lower() != "vertex":
        cfg.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not cfg.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")

    if cfg.vertex:
        project_id = (cfg.vertex.project_id or "").strip()
        if project_id.startswith("${"):
            raise ValueError("VERTEX_PROJECT_ID 환경변수가 해결되지 않았습니다.")
        if not project_id:
            env_project = os.getenv("VERTEX_PROJECT_ID")
            if env_project:
                cfg.vertex.project_id = env_project
                print(f"[INFO] 환경변수에서 VERTEX_PROJECT_ID 로드: {cfg.vertex.project_id}")
            else:
                print("[WARNING] Vertex project_id가 설정되지 않았습니다. Gemini 기능 사용 시 VERTEX_PROJECT_ID를 설정하세요.")
    return cfg

def _expand_env_vars(yaml_content: str) -> str:
    """YAML ?댁슜?먯꽌 ?섍꼍蹂??${VAR_NAME} ?먮뒗 ${VAR_NAME:-default} ?뺥깭瑜??ㅼ젣 媛믪쑝濡?移섑솚"""
    import re

    def replace_env_var(match):
        expr = match.group(1).strip()
        var_name = expr
        default_value = None

        if ':-' in expr:
            var_name, default_value = [part.strip() for part in expr.split(':-', 1)]

        env_value = os.getenv(var_name)
        if env_value is None or env_value == '':
            if default_value is not None:
                return default_value
            print(f"[WARNING] ?섍꼍蹂??{var_name}???ㅼ젙?섏? ?딆븯?듬땲??")
            return match.group(0)  # ?먮낯 洹몃?濡?諛섑솚

        return env_value

    pattern = r'\$\{([^}]+)\}'
    return re.sub(pattern, replace_env_var, yaml_content)


