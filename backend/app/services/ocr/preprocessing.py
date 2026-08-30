from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class CaptureQuality:
    blur_score: float
    glare_score: float
    perspective_score: float
    resolution_score: float
    document_detected: bool
    acceptable: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict:
        return {"blur_score": self.blur_score, "glare_score": self.glare_score, "perspective_score": self.perspective_score, "resolution_score": self.resolution_score, "document_detected": self.document_detected, "acceptable": self.acceptable, "reasons": list(self.reasons)}


def quality_metrics(image: np.ndarray, *, document_detected: bool, perspective_score: float) -> CaptureQuality:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    laplacian_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur_score = round(min(1.0, laplacian_variance / 350.0), 4)
    pixels = gray.shape[0] * gray.shape[1]
    bright = (gray >= 250).astype(np.uint8)
    component_count, _, stats, _ = cv2.connectedComponentsWithStats(bright, connectivity=8)
    glare_pixels = 0
    for index in range(1, component_count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        # Ignore the large normal white-paper region; glare appears as smaller
        # clipped islands that erase nearby ink detail.
        if pixels * 0.0005 <= area <= pixels * 0.08:
            glare_pixels += area
    glare_ratio = glare_pixels / pixels
    glare_score = round(min(1.0, glare_ratio), 4)
    resolution_score = round(min(1.0, pixels / 1_500_000), 4)
    reasons: list[str] = []
    if not document_detected: reasons.append("DOCUMENT_NOT_DETECTED")
    if blur_score < 0.25: reasons.append("IMAGE_TOO_BLURRY")
    if glare_score > 0.18: reasons.append("EXCESSIVE_GLARE")
    if resolution_score < 0.20: reasons.append("INSUFFICIENT_RESOLUTION")
    return CaptureQuality(blur_score, glare_score, round(perspective_score, 4), resolution_score, document_detected, not reasons, tuple(reasons))


def enhance_document(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return contrast-enhanced grayscale and clean adaptive binary images."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    denoised = cv2.fastNlMeansDenoising(gray, None, 8, 7, 21)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
    binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return enhanced, binary


def correct_orientation(image: np.ndarray) -> np.ndarray:
    """Normalize likely portrait marksheets without any cloud orientation OCR."""
    return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE) if image.shape[1] > image.shape[0] * 1.25 else image
