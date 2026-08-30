import json

import cv2
import numpy as np
import pytest

from app.services.ocr import preprocess_marksheet


def synthetic_marksheet():
    image = np.full((900, 700, 3), 35, dtype=np.uint8)
    page = np.array([[70, 55], [645, 85], [620, 850], [45, 820]], dtype=np.int32)
    cv2.fillConvexPoly(image, page, (242, 242, 242))
    for y in range(160, 760, 55):
        cv2.line(image, (100, y), (575, y + 8), (45, 45, 45), 2)
    for x in range(100, 600, 95):
        cv2.line(image, (x, 145), (x - 15, 775), (70, 70, 70), 2)
    cv2.putText(image, "12  08  15", (130, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (10, 10, 10), 2)
    return image


def test_preprocess_detects_corrects_and_saves_debug_images(tmp_path):
    result = preprocess_marksheet(synthetic_marksheet(), debug_directory=tmp_path)
    assert result.quality.document_detected is True
    assert result.quality.acceptable is True
    assert result.corrected_page.shape[0] > result.corrected_page.shape[1]
    assert result.binary_page.ndim == 2
    assert (tmp_path / "corrected_page.jpg").is_file()
    quality = json.loads((tmp_path / "quality.json").read_text(encoding="utf-8"))
    assert quality["acceptable"] is True


def test_preprocess_rejects_blurry_image():
    blurred = cv2.GaussianBlur(synthetic_marksheet(), (81, 81), 0)
    with pytest.raises(ValueError, match="Image quality is insufficient"):
        preprocess_marksheet(blurred)
