import cv2
import numpy as np

from app.services.ocr.cell_extractor import extract_cell
from app.services.ocr.grid_detector import detect_grid


def test_detects_table_rows_columns_and_extracts_cells():
    page = np.full((420, 520), 255, dtype=np.uint8)
    for x in (40, 180, 340, 480): cv2.line(page, (x, 40), (x, 380), 0, 3)
    for y in (40, 110, 200, 290, 380): cv2.line(page, (40, y), (480, y), 0, 3)
    cv2.putText(page, "12", (375, 175), cv2.FONT_HERSHEY_SIMPLEX, 1.2, 0, 3)
    detection = detect_grid(page)
    assert detection.rows == 4
    assert detection.columns == 3
    assert len(detection.cells) == 12
    target = next(cell for cell in detection.cells if cell.row == 1 and cell.column == 2)
    crop = extract_cell(page, target)
    assert crop.shape[0] > 40 and crop.shape[1] > 80
    assert np.min(crop) == 0
