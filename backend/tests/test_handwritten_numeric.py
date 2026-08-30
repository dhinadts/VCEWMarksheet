import json
from decimal import Decimal

import cv2
import numpy as np
import pytest

from app.services.ocr.digit_recognizer import extract_handwritten_numeric, save_numeric_result
from app.services.ocr.mark_normalizer import NumericNormalizationError, normalize_numeric_token


class SequenceClassifier:
    version = "test-local-classifier-v1"

    def __init__(self, predictions):
        self.predictions = iter(predictions)

    def predict_digit(self, glyph):
        assert glyph.ndim == 2
        return next(self.predictions)


def test_normalizes_integer_and_decimal_to_decimal():
    assert normalize_numeric_token("12") == Decimal("12")
    assert normalize_numeric_token("12.5", allow_decimal=True) == Decimal("12.5")


@pytest.mark.parametrize("token", ["l2", "O", "12/", "1,5", "١٢"])
def test_rejects_ambiguous_or_locale_dependent_ocr_tokens(token):
    with pytest.raises(NumericNormalizationError):
        normalize_numeric_token(token, allow_decimal=True)


def test_range_is_validation_not_silent_correction():
    with pytest.raises(NumericNormalizationError, match="between 0 and 13"):
        normalize_numeric_token("18", maximum=Decimal("13"))


def test_extracts_multiple_digit_value_and_preserves_confidence():
    image = np.full((80, 150), 255, dtype=np.uint8)
    cv2.rectangle(image, (30, 15), (48, 66), 0, -1)
    cv2.rectangle(image, (75, 15), (105, 66), 0, -1)
    result = extract_handwritten_numeric(image, SequenceClassifier([(1, 0.96), (2, 0.88)]), maximum=20)
    assert result.raw_text == "12"
    assert result.numeric_value == Decimal("12")
    assert result.confidence == pytest.approx(0.92)
    assert result.requires_review is False


def test_low_confidence_requires_review_and_json_uses_number(tmp_path):
    image = np.full((80, 90), 255, dtype=np.uint8)
    cv2.rectangle(image, (25, 14), (57, 66), 0, -1)
    result = extract_handwritten_numeric(image, SequenceClassifier([(7, 0.62)]), maximum=10)
    target = save_numeric_result(tmp_path / "result.json", result)
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert result.requires_review is True
    assert saved["numeric_value"] == 7
    assert isinstance(saved["numeric_value"], int)


def test_ignores_tick_mark_and_extracts_only_the_handwritten_number():
    image = np.full((90, 180), 255, dtype=np.uint8)
    cv2.line(image, (12, 44), (25, 60), 0, 5)
    cv2.line(image, (25, 60), (55, 20), 0, 5)
    cv2.rectangle(image, (105, 18), (132, 70), 0, -1)
    result = extract_handwritten_numeric(image, SequenceClassifier([(7, 0.95)]), maximum=10)
    assert result.raw_text == "7"
    assert result.numeric_value == Decimal("7")
    assert len(result.glyphs) == 1


def test_tick_without_a_number_is_not_classified_as_a_digit():
    image = np.full((80, 100), 255, dtype=np.uint8)
    cv2.line(image, (15, 38), (30, 56), 0, 5)
    cv2.line(image, (30, 56), (68, 14), 0, 5)
    with pytest.raises(ValueError, match="No handwritten numeric glyph"):
        extract_handwritten_numeric(image, SequenceClassifier([]), maximum=10)
