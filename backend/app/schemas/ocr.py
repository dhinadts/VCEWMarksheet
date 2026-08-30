import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class OCRCorrection(BaseModel):
    extraction_id: uuid.UUID
    corrected_numeric_value: Decimal = Field(ge=0)
    selected_option: Literal["A", "B"] | None = None


class OCRReviewRequest(BaseModel):
    corrections: list[OCRCorrection]
