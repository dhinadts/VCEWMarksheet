from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class CellRegion:
    row: int
    column: int
    x: int
    y: int
    width: int
    height: int

    @property
    def bounding_box(self) -> dict:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height, "row": self.row, "column": self.column}


@dataclass(frozen=True)
class GridDetection:
    cells: tuple[CellRegion, ...]
    rows: int
    columns: int
    horizontal_lines: np.ndarray
    vertical_lines: np.ndarray


def detect_grid(binary_page: np.ndarray, *, minimum_cell_size: int = 18) -> GridDetection:
    """Detect table lines and convert adjacent intersections into cell regions."""
    ink = 255 - binary_page if float(np.mean(binary_page)) > 127 else binary_page.copy()
    height, width = ink.shape
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(20, width // 25), 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(20, height // 25)))
    horizontal = cv2.morphologyEx(ink, cv2.MORPH_OPEN, horizontal_kernel)
    vertical = cv2.morphologyEx(ink, cv2.MORPH_OPEN, vertical_kernel)
    y_positions = _cluster_positions(np.where(np.mean(horizontal > 0, axis=1) > 0.18)[0])
    x_positions = _cluster_positions(np.where(np.mean(vertical > 0, axis=0) > 0.18)[0])
    cells: list[CellRegion] = []
    for row, (top, bottom) in enumerate(zip(y_positions, y_positions[1:])):
        for column, (left, right) in enumerate(zip(x_positions, x_positions[1:])):
            cell_width, cell_height = right - left, bottom - top
            if cell_width >= minimum_cell_size and cell_height >= minimum_cell_size:
                cells.append(CellRegion(row, column, int(left), int(top), int(cell_width), int(cell_height)))
    return GridDetection(tuple(cells), max(0, len(y_positions) - 1), max(0, len(x_positions) - 1), horizontal, vertical)


def draw_grid(image: np.ndarray, detection: GridDetection) -> np.ndarray:
    output = image.copy()
    for cell in detection.cells:
        cv2.rectangle(output, (cell.x, cell.y), (cell.x + cell.width, cell.y + cell.height), (0, 0, 255), 2)
        cv2.putText(output, f"{cell.row},{cell.column}", (cell.x + 3, cell.y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    return output


def _cluster_positions(values: np.ndarray, maximum_gap: int = 4) -> list[int]:
    if not len(values): return []
    groups: list[list[int]] = [[int(values[0])]]
    for value in values[1:]:
        if int(value) - groups[-1][-1] <= maximum_gap: groups[-1].append(int(value))
        else: groups.append([int(value)])
    return [round(sum(group) / len(group)) for group in groups]
