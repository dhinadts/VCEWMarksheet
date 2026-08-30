import cv2
import numpy as np

from app.services.ocr.grid_detector import CellRegion


def extract_cell(binary_page: np.ndarray, cell: CellRegion, *, inset: int = 4) -> np.ndarray:
    """Crop a cell inside its borders and suppress residual table lines."""
    x1, y1 = cell.x + inset, cell.y + inset
    x2, y2 = cell.x + cell.width - inset, cell.y + cell.height - inset
    if x2 <= x1 or y2 <= y1: raise ValueError("Cell is too small after border removal")
    crop = binary_page[y1:y2, x1:x2].copy()
    ink = 255 - crop if float(np.mean(crop)) > 127 else crop
    horizontal = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(8, crop.shape[1] // 2), 1)))
    vertical = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(8, crop.shape[0] // 2))))
    cleaned = cv2.subtract(ink, cv2.bitwise_or(horizontal, vertical))
    return 255 - cleaned
