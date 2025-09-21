from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ProductStructured(BaseModel):
    meta: Dict[str, Any]
    product: Dict[str, Any] = Field(..., description="brand/name/category/images_count/badges/specs[key,value]/claims[]/warnings[]/cta_texts[]/policy_flags{health_claims,before_after,medical_terms}/missing_info[]")
    structure_quality: Dict[str, Any] = Field(..., description="source_noise in {low,mid,high}, confidence_note str")

class ReviewsNormalized(BaseModel):
    stats: Dict[str, Any] = Field(..., description="total_reviews number, rating_avg number|null, recent_ratio_30d number")
    signals: Dict[str, Any] = Field(..., description="demand[], friction[], keywords_top[{term,count}]")
    quotes: Dict[str, Any] = Field(..., description="positive[], negative[]")

class EmailDraft(BaseModel):
    meta: Dict[str, Any] = Field(..., description="job_id, brand|null, product_name|null")
    aida_mapping: Dict[str, str] = Field(..., description="A,I,D,A strings")
    gap_analysis: List[Dict[str, str]] = Field(..., description="list of {gap,evidence,suggestion}")
    email: Dict[str, str] = Field(..., description="subject, body")
    compliance: Dict[str, Any] = Field(..., description="ad_prefix_required bool, risky_claims_removed bool, placeholders[]")
