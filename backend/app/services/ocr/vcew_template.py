"""Fixed-layout model for the VCEW internal valuation sheet.

The model deliberately exposes only handwritten mark cells.  Printed metadata,
tick columns, totals in words, signatures, and the graph-paper area are outside
all regions of interest.
"""

from dataclasses import dataclass

from app.services.ocr.grid_detector import CellRegion


@dataclass(frozen=True)
class NormalizedRegion:
    left: float
    top: float
    right: float
    bottom: float

    def to_cell(self, width: int, height: int, *, row: int, column: int) -> CellRegion:
        x1, y1 = round(self.left * width), round(self.top * height)
        x2, y2 = round(self.right * width), round(self.bottom * height)
        return CellRegion(row, column, x1, y1, x2 - x1, y2 - y1)


@dataclass(frozen=True)
class VCEWMarkField:
    field_name: str
    question_number: int
    candidates: tuple[NormalizedRegion, ...]
    option_labels: tuple[str | None, ...]


@dataclass(frozen=True)
class VCEWTemplateModel:
    """Normalized regions calibrated from the supplied blank VCEW sheet."""

    version: str = "vcew-internal-valuation-v1"
    minimum_portrait_ratio: float = 1.20
    maximum_portrait_ratio: float = 1.45

    def matches(self, width: int, height: int) -> bool:
        if width <= 0 or height <= 0:
            return False
        ratio = height / width
        return self.minimum_portrait_ratio <= ratio <= self.maximum_portrait_ratio

    def fields(self) -> tuple[VCEWMarkField, ...]:
        # The marks table uses twelve equally spaced answer rows. Part A uses
        # rows 1-10. Part B/C questions have A and B candidate rows; only the
        # candidate containing handwriting is retained by the pipeline.
        # First answer row begins immediately below the two printed header
        # bands. Values are normalized against the full corrected page.
        table_top = 0.6003
        row_height = 0.0198
        part_a_left, part_a_right = 0.202, 0.282
        total_left, total_right = 0.654, 0.727

        def region(left: float, right: float, row: int) -> NormalizedRegion:
            # Keep nearly the full cell height: handwritten digits commonly
            # descend close to the ruled baseline. Border removal happens in
            # ``extract_cell``.
            inset_y = 0.0004
            top = table_top + row * row_height + inset_y
            return NormalizedRegion(left, top, right, table_top + (row + 1) * row_height - inset_y)

        fields: list[VCEWMarkField] = []
        for question in range(1, 11):
            fields.append(VCEWMarkField(
                f"question_{question:02d}", question,
                (region(part_a_left, part_a_right, question - 1),), (None,),
            ))
        for question in range(11, 17):
            answer_row = (question - 11) * 2
            fields.append(VCEWMarkField(
                f"question_{question:02d}", question,
                (region(total_left, total_right, answer_row), region(total_left, total_right, answer_row + 1)),
                ("A", "B"),
            ))
        return tuple(fields)


VCEW_INTERNAL_MARKSHEET = VCEWTemplateModel()
