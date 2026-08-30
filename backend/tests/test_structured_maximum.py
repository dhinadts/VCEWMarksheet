from decimal import Decimal

from app.services.ocr.structured_pipeline import question_maximum


def test_question_specific_maximums_match_the_valuation_sheet():
    assessment_maximum = Decimal("100")
    assert question_maximum(1, assessment_maximum) == Decimal("2")
    assert question_maximum(10, assessment_maximum) == Decimal("2")
    assert question_maximum(11, assessment_maximum) == Decimal("13")
    assert question_maximum(15, assessment_maximum) == Decimal("13")
    assert question_maximum(16, assessment_maximum) == Decimal("15")
    assert question_maximum(17, assessment_maximum) == assessment_maximum
