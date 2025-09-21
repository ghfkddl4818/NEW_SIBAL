import pytest
from core.schemas import ProductStructured, ReviewsNormalized, EmailDraft

def test_product_structured_schema():
    # This is a basic check, can be expanded with more specific tests
    assert ProductStructured.model_fields['product'].is_required()
    assert "brand" in ProductStructured.model_fields['product'].description

def test_reviews_normalized_schema():
    assert ReviewsNormalized.model_fields['stats'].is_required()
    assert "total_reviews" in ReviewsNormalized.model_fields['stats'].description

def test_email_draft_schema():
    assert EmailDraft.model_fields['email'].is_required()
    assert "subject" in EmailDraft.model_fields['email'].description
