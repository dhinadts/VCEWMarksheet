import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import cv2

from app.services.ocr.cell_extractor import extract_cell
from app.services.ocr.digit_recognizer import DigitClassifier, NumericRecognitionResult, extract_handwritten_numeric
from app.services.ocr.grid_detector import CellRegion, GridDetection, detect_grid, draw_grid
from app.services.ocr.pipeline import preprocess_marksheet


@dataclass(frozen=True)
class CellOCRResult:
    field_name: str
    cell: CellRegion
    recognition: NumericRecognitionResult | None
    error: str | None


@dataclass(frozen=True)
class StructuredOCRResult:
    cells: tuple[CellOCRResult, ...]
    rows: int
    columns: int


def question_maximum(question_number: int, assessment_maximum: Decimal) -> Decimal:
    """Return the printed maximum for a VCEW valuation-sheet question."""
    if question_number <= 10:
        return Decimal("2")
    if question_number <= 15:
        return Decimal("13")
    if question_number == 16:
        return Decimal("15")
    return assessment_maximum


def process_structured_marksheet(
    image: bytes,
    classifier: DigitClassifier,
    *,
    maximum: Decimal,
    mark_column_indices: tuple[int, ...] = (-1,),
    skip_header_rows: int = 1,
    debug_directory: str | Path | None = None,
) -> StructuredOCRResult:
    preprocessing = preprocess_marksheet(image, debug_directory=debug_directory)
    grid = detect_grid(preprocessing.binary_page)
    university_template = grid.rows > 30
    # The university sheet has a large graph-paper grid above the valuation
    # table. When it dominates line detection, isolate the lower marks table.
    if university_template:
        page_height, page_width = preprocessing.binary_page.shape
        top, bottom = int(page_height * 0.45), int(page_height * 0.86)
        left, right = int(page_width * 0.05), int(page_width * 0.95)
        # Phone screenshots and messaging apps can downscale the paper enough
        # that valid table rows are only 8-9 pixels high after correction.
        table_grid = detect_grid(preprocessing.binary_page[top:bottom, left:right], minimum_cell_size=8)
        translated = tuple(CellRegion(cell.row, cell.column, cell.x + left, cell.y + top, cell.width, cell.height) for cell in table_grid.cells)
        grid = GridDetection(translated, table_grid.rows, table_grid.columns, table_grid.horizontal_lines, table_grid.vertical_lines)
    if not grid.cells or grid.columns < 1:
        raise ValueError("No marks table grid was detected")
    columns = {index if index >= 0 else grid.columns + index for index in mark_column_indices}
    if university_template:
        # VCEW valuation layout: questions 1-10 use the Part-A marks
        # column; questions 11-16 use each paired row's Total Marks cell.
        part_a = sorted((cell for cell in grid.cells if cell.column == 2 and cell.row >= 7), key=lambda cell: cell.row)[:10]
        part_bc = sorted((cell for cell in grid.cells if cell.column == grid.columns - 1 and cell.row in range(7, 18, 2)), key=lambda cell: cell.row)[:6]
        selected = [*part_a, *part_bc]
    else:
        selected = [cell for cell in grid.cells if cell.row >= skip_header_rows and cell.column in columns]
    results: list[CellOCRResult] = []
    debug_path = Path(debug_directory) if debug_directory else None
    if debug_path:
        cv2.imwrite(str(debug_path / "detected_grid.jpg"), draw_grid(preprocessing.corrected_page, grid))
    for sequence, cell in enumerate(selected, 1):
        crop = extract_cell(preprocessing.binary_page, cell)
        if debug_path: cv2.imwrite(str(debug_path / f"cell_{sequence:03d}.png"), crop)
        field_name = f"question_{sequence:02d}" if university_template else f"cell_r{cell.row:03d}_c{cell.column:03d}"
        try:
            cell_maximum = question_maximum(sequence, maximum) if university_template else maximum
            recognition = extract_handwritten_numeric(crop, classifier, minimum=0, maximum=cell_maximum)
            results.append(CellOCRResult(field_name, cell, recognition, None))
        except ValueError as exc:
            results.append(CellOCRResult(field_name, cell, None, str(exc)))
    output = StructuredOCRResult(tuple(results), grid.rows, grid.columns)
    if debug_path:
        payload = [{"field_name": item.field_name, "bounding_box": item.cell.bounding_box, "recognition": item.recognition.as_dict() if item.recognition else None, "error": item.error} for item in results]
        (debug_path / "ocr_result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output
