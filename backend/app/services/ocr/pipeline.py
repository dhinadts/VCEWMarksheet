import json
import os
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.services.ocr.document_detector import detect_document
from app.services.ocr.perspective import four_point_transform
from app.services.ocr.preprocessing import CaptureQuality, correct_orientation, enhance_document, quality_metrics


@dataclass(frozen=True)
class PreprocessingResult:
    corrected_page: np.ndarray
    enhanced_page: np.ndarray
    binary_page: np.ndarray
    quality: CaptureQuality


def preprocess_marksheet(image_source: str | os.PathLike[str] | bytes | np.ndarray, *, debug_directory: str | os.PathLike[str] | None = None, reject_poor_quality: bool = True) -> PreprocessingResult:
    """Run local document detection, perspective correction, orientation, and enhancement."""
    image = _decode(image_source)
    detection = detect_document(image)
    quality = quality_metrics(image, document_detected=detection.detected, perspective_score=detection.perspective_score)
    if reject_poor_quality and not quality.acceptable:
        raise ValueError("Image quality is insufficient. Please capture the marksheet again. " + ", ".join(quality.reasons))
    corrected = four_point_transform(image, detection.corners) if detection.corners is not None else image.copy()
    corrected = correct_orientation(corrected)
    enhanced, binary = enhance_document(corrected)
    result = PreprocessingResult(corrected, enhanced, binary, quality)
    if debug_directory is not None: _save_debug(Path(debug_directory), result)
    return result


def _decode(source) -> np.ndarray:
    if isinstance(source, np.ndarray): image = source
    elif isinstance(source, bytes): image = cv2.imdecode(np.frombuffer(source, np.uint8), cv2.IMREAD_COLOR)
    else: image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if image is None or image.size == 0: raise ValueError("Image could not be decoded")
    return image


def _save_debug(directory: Path, result: PreprocessingResult) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(directory / "corrected_page.jpg"), result.corrected_page)
    cv2.imwrite(str(directory / "enhanced_page.jpg"), result.enhanced_page)
    cv2.imwrite(str(directory / "binary_page.png"), result.binary_page)
    (directory / "quality.json").write_text(json.dumps(result.quality.as_dict(), indent=2), encoding="utf-8")
