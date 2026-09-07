import pytest
from backend.trans.translation import classify_issue, _parse_category

def test_empty_complaint_raises_error():
    with pytest.raises(ValueError, match="Complaint cannot be empty"):
        classify_issue("")

def test_whitespace_complaint_raises_error():
    with pytest.raises(ValueError, match="Complaint cannot be empty"):
        classify_issue("   ")

def test_parse_category_valid_json():
    cat = _parse_category('{"category": "water_resources"}')
    assert cat == "water_resources"

def test_parse_category_with_surrounding_text():
    cat = _parse_category('The domain is: {"category": "healthcare"} in the response.')
    assert cat == "healthcare"

def test_parse_category_invalid():
    with pytest.raises(ValueError, match="Invalid model output"):
        _parse_category('{"category": "non_existent_category"}')

def test_real_ai_classification():
    # Test real Gemini Flash classification
    category = classify_issue("villagers have no drinking water supply")
    assert category == "water_resources"

def test_rule_based_fallback():
    from backend.trans.translation import _rule_based_fallback
    assert _rule_based_fallback("broken water pipe with zero pressure") == "water_resources"
    assert _rule_based_fallback("kisan ki fasal kharab ho gayi") == "agriculture"
    assert _rule_based_fallback("voltage fluctuation in electrical grid") == "energy"

