from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class DocumentDetection:
    corners: np.ndarray | None
    detected: bool
    perspective_score: float


def detect_document(image: np.ndarray) -> DocumentDetection:
    """Locate the largest page-like quadrilateral in a camera image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    image_area = float(gray.shape[0] * gray.shape[1])
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:12]:
        area = cv2.contourArea(contour)
        # A marksheet contains several large internal rectangles (notably the
        # graph-paper answer area). Never mistake one of those for the page.
        # Perspective correction is only safe when the quadrilateral covers
        # most of the captured image.
        if area < image_area * 0.65:
            continue
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(polygon) == 4 and cv2.isContourConvex(polygon):
            corners = polygon.reshape(4, 2).astype(np.float32)
            fill_ratio = min(1.0, area / image_area)
            return DocumentDetection(corners, True, round(fill_ratio, 4))
    # Mobile gallery images and scanner exports are often already cropped to
    # the page, so no outer paper contour exists. Treat a predominantly light,
    # portrait document as a safe full-frame page without perspective warp.
    light_page_ratio = float(np.mean(gray > 120))
    if light_page_ratio >= 0.72 and gray.shape[0] >= gray.shape[1]:
        return DocumentDetection(None, True, 1.0)
    return DocumentDetection(None, False, 0.0)
