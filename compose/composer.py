from __future__ import annotations
import re
from typing import Any, Dict

SENSITIVE_PATTERNS = [
    r"완치", r"치료", r"부작용 없음", r"즉시 효과", r"100%",
    r"기적", r"영구적", r"특효", r"절대", r"보장", r"전부 해결",
]
SENSITIVE_REPLACEMENT = "효과에는 개인차가 있을 수 있습니다"

# 길이 채움용 안전 보일러플레이트(광고·의학 효능 주장 없음)
FILLER_PARAGRAPHS = [
    "현재 상세페이지가 첫 화면(1스크린)에서 핵심 가치 제안, 신뢰 근거, 명확한 행동 유도를 균형 있게 전달하는지 신속히 점검해 드립니다.",
    "리뷰 데이터의 제시 방식, 위험·유의 문구의 노출 위치, 배송·교환·환불 정책의 보장감 등 전환을 방해할 수 있는 요소를 구조적으로 개선합니다.",
    "목표 고객·주력 상품·예산 범위를 알려주시면 AIDA 프레임과 실제 고객 언어를 반영한 1차 시안을 제작해 24시간 내 회신드리겠습니다."
]
FILLER_EXTRA = "자세한 데이터(리뷰·전환·문의)를 공유해 주시면 제안을 더 구체화해 드립니다."

def _normalize_draft(d: Any) -> Dict[str, str]:
    """임의 구조를 {'subject','body'}로 정규화."""
    if isinstance(d, dict) and ("subject" in d or "body" in d):
        return {"subject": str(d.get("subject") or "문의드립니다"),
                "body": str(d.get("body") or "")}
    if isinstance(d, dict) and "email" in d and isinstance(d["email"], dict):
        e = d["email"]
        return {"subject": str(e.get("subject") or "문의드립니다"),
                "body": str(e.get("body") or "")}
    if isinstance(d, str):
        return {"subject": "문의드립니다", "body": d}
    return {"subject": "문의드립니다", "body": str(d)}

def _ensure_ad_prefix(subject: str) -> str:
    s = (subject or "").strip()
    if not s.startswith("[광고]"):
        s = "[광고] " + s
    return s

def _suppress_sensitive(text: str) -> str:
    buf = text or ""
    for pat in SENSITIVE_PATTERNS:
        buf = re.sub(pat, SENSITIVE_REPLACEMENT, buf, flags=re.IGNORECASE)
    return buf

def _apply_tone(body: str, tone: str) -> str:
    # 톤에 따라 마무리만 가볍게 조정
    if body and not body.endswith("감사합니다."):
        body += "\n\n감사합니다."
    return body

def _ensure_min_length(body: str, min_chars: int, max_chars: int) -> str:
    """본문이 min_chars 미만이면 안전 보일러플레이트를 순차적으로 붙여 최소 길이 충족."""
    text = (body or "").strip()

    # 이미 충분하면 그대로
    if len(text) >= min_chars:
        return text

    # 보일러플레이트 순차 추가
    for p in FILLER_PARAGRAPHS:
        if len(text) >= min_chars:
            break
        candidate = (text + ("\n\n" if text else "") + p).strip()
        if max_chars and len(candidate) > max_chars:
            break
        text = candidate

    # 그래도 부족하면 짧은 문장 반복 추가
    while len(text) < min_chars:
        if max_chars and len(text) + len(FILLER_EXTRA) + 2 > max_chars:
            break
        text += "\n\n" + FILLER_EXTRA

    return text

def _clamp_max(body: str, max_chars: int) -> str:
    if max_chars and len(body) > max_chars:
        return body[:max_chars].rstrip() + "…"
    return body

def compose_final_email(email_draft: Any, policy: Any) -> Dict[str, str]:
    """최종 이메일 제목/본문을 정책에 맞게 강제 정규화."""
    d = _normalize_draft(email_draft)

    min_chars = getattr(policy, "email_min_chars", 350)
    max_chars = getattr(policy, "email_max_chars", 600)
    tone = getattr(policy, "tone_default", "consultant")

    subject = _ensure_ad_prefix(d.get("subject") or "")
    body = d.get("body") or ""

    # 1) 길이 보정(최소 채움)
    body = _ensure_min_length(body, min_chars, max_chars)

    # 2) 민감표현 완화
    body = _suppress_sensitive(body)

    # 3) 톤 마무리
    body = _apply_tone(body, tone)

    # 4) 최대 길이 클램프
    body = _clamp_max(body, max_chars)

    return {"subject": subject, "body": body}
