from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol, TypeAlias

import cv2
import numpy as np

from app.services.ocr.mark_normalizer import json_numeric, normalize_numeric_token

ImageSource: TypeAlias = str | os.PathLike[str] | bytes | bytearray | np.ndarray


class DigitClassifier(Protocol):
    version: str

    def predict_digit(self, glyph: np.ndarray) -> tuple[int, float]:
        """Return an ASCII digit 0..9 and calibrated confidence 0..1."""


@dataclass(frozen=True)
class RecognizedGlyph:
    symbol: str
    confidence: float
    bounding_box: tuple[int, int, int, int]


@dataclass(frozen=True)
class NumericRecognitionResult:
    raw_text: str
    numeric_value: Decimal
    confidence: float
    requires_review: bool
    recognizer_version: str
    glyphs: tuple[RecognizedGlyph, ...]

    def as_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "numeric_value": json_numeric(self.numeric_value),
            "confidence": round(self.confidence, 6),
            "requires_review": self.requires_review,
            "recognizer_version": self.recognizer_version,
            "glyphs": [
                {"symbol": item.symbol, "confidence": round(item.confidence, 6), "bounding_box": list(item.bounding_box)}
                for item in self.glyphs
            ],
        }


class OpenCVDnnDigitClassifier:
    """Offline ONNX digit classifier loaded from the local filesystem.

    The model must accept a single 28x28 grayscale glyph and return ten logits
    ordered from digit 0 through 9. No model is downloaded and no network or
    external API is used.
    """

    def __init__(self, model_path: str | os.PathLike[str], *, version: str | None = None) -> None:
        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(f"Local digit model was not found: {path}")
        self._network = cv2.dnn.readNetFromONNX(str(path))
        self.version = version or f"opencv-onnx:{path.name}"

    def predict_digit(self, glyph: np.ndarray) -> tuple[int, float]:
        prepared = _prepare_model_glyph(glyph)
        self._network.setInput(prepared[np.newaxis, np.newaxis, :, :])
        logits = np.asarray(self._network.forward(), dtype=np.float32).reshape(-1)
        if logits.size != 10:
            raise ValueError("Digit model must return exactly ten class logits")
        probabilities = _softmax(logits)
        digit = int(np.argmax(probabilities))
        return digit, float(probabilities[digit])


class SyntheticKnnDigitClassifier:
    """Offline fallback trained from augmented OpenCV glyphs at startup.

    This keeps development and testing functional without downloads. Production
    deployments should prefer a reviewed local ONNX handwriting model.
    """

    version = "opencv-synthetic-knn-v1"

    def __init__(self) -> None:
        samples: list[np.ndarray] = []
        labels: list[int] = []
        fonts = [cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX, cv2.FONT_HERSHEY_COMPLEX]
        for digit in range(10):
            for font in fonts:
                for scale in (0.75, 0.9, 1.05):
                    for thickness in (1, 2, 3):
                        canvas = np.zeros((40, 32), dtype=np.uint8)
                        cv2.putText(canvas, str(digit), (3, 32), font, scale, 255, thickness, cv2.LINE_AA)
                        for angle in (-8, -4, 0, 4, 8):
                            matrix = cv2.getRotationMatrix2D((16, 20), angle, 1.0)
                            rotated = cv2.warpAffine(canvas, matrix, (32, 40))
                            samples.append(_prepare_model_glyph(rotated).reshape(-1))
                            labels.append(digit)
        self._knn = cv2.ml.KNearest_create()
        self._knn.train(np.asarray(samples, np.float32), cv2.ml.ROW_SAMPLE, np.asarray(labels, np.float32))

    def predict_digit(self, glyph: np.ndarray) -> tuple[int, float]:
        sample = _prepare_model_glyph(glyph).reshape(1, -1).astype(np.float32)
        _, result, neighbours, distances = self._knn.findNearest(sample, k=5)
        digit = int(result[0, 0])
        agreement = float(np.mean(neighbours[0] == digit))
        distance_score = 1.0 / (1.0 + float(np.mean(distances[0])) / 20.0)
        return digit, max(0.0, min(1.0, agreement * 0.75 + distance_score * 0.25))


def extract_handwritten_numeric(
    image: ImageSource,
    classifier: DigitClassifier,
    *,
    minimum: int | Decimal = 0,
    maximum: int | Decimal = 100,
    allow_decimal: bool = False,
    review_confidence: float = 0.90,
) -> NumericRecognitionResult:
    """Extract a handwritten single- or multi-digit mark from one cell image.

    The function is entirely local. It segments glyphs with OpenCV, classifies
    digits through the injected local classifier, recognizes a geometric
    decimal point when enabled, and returns a canonical Decimal value.
    """
    if not 0 <= review_confidence <= 1:
        raise ValueError("review_confidence must be between 0 and 1")
    gray = _load_grayscale(image)
    binary = _binarize(gray)
    components = _numeric_components(binary, allow_decimal=allow_decimal)
    if not components:
        raise ValueError("No handwritten numeric glyph was detected")

    glyphs: list[RecognizedGlyph] = []
    raw_symbols: list[str] = []
    digit_confidences: list[float] = []
    for x, y, width, height, is_decimal in components:
        if is_decimal:
            raw_symbols.append(".")
            glyphs.append(RecognizedGlyph(".", 1.0, (x, y, width, height)))
            continue
        crop = binary[y : y + height, x : x + width]
        digit, confidence = classifier.predict_digit(crop)
        if digit < 0 or digit > 9 or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Digit classifier returned an invalid prediction")
        symbol = str(digit)
        raw_symbols.append(symbol)
        digit_confidences.append(confidence)
        glyphs.append(RecognizedGlyph(symbol, confidence, (x, y, width, height)))

    raw_text = "".join(raw_symbols)
    value = normalize_numeric_token(
        raw_text,
        minimum=Decimal(str(minimum)),
        maximum=Decimal(str(maximum)),
        allow_decimal=allow_decimal,
    )
    confidence = sum(digit_confidences) / len(digit_confidences) if digit_confidences else 0.0
    return NumericRecognitionResult(
        raw_text=raw_text,
        numeric_value=value,
        confidence=confidence,
        requires_review=confidence < review_confidence,
        recognizer_version=classifier.version,
        glyphs=tuple(glyphs),
    )


def save_numeric_result(path: str | os.PathLike[str], result: NumericRecognitionResult) -> Path:
    """Atomically save OCR evidence with ``numeric_value`` encoded as a JSON number."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(result.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(target)
    return target


def _load_grayscale(image: ImageSource) -> np.ndarray:
    if isinstance(image, np.ndarray):
        array = image
    elif isinstance(image, (bytes, bytearray)):
        array = cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    else:
        array = cv2.imread(str(image), cv2.IMREAD_UNCHANGED)
    if array is None or array.size == 0:
        raise ValueError("Image could not be decoded")
    if array.ndim == 2:
        return array.astype(np.uint8)
    if array.ndim == 3 and array.shape[2] == 4:
        return cv2.cvtColor(array, cv2.COLOR_BGRA2GRAY)
    if array.ndim == 3:
        return cv2.cvtColor(array, cv2.COLOR_BGR2GRAY)
    raise ValueError("Unsupported image dimensions")


def _binarize(gray: np.ndarray) -> np.ndarray:
    resized = gray if min(gray.shape[:2]) >= 32 else cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.GaussianBlur(resized, (3, 3), 0)
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return binary


def _numeric_components(binary: np.ndarray, *, allow_decimal: bool) -> list[tuple[int, int, int, int, bool]]:
    count, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    height, width = binary.shape
    page_area = height * width
    boxes: list[tuple[int, int, int, int, int]] = []
    for index in range(1, count):
        x, y, box_width, box_height, area = (int(value) for value in stats[index])
        touches_border = x == 0 or y == 0 or x + box_width >= width or y + box_height >= height
        if touches_border or area < max(3, page_area * 0.0004):
            continue
        boxes.append((x, y, box_width, box_height, area))
    if not boxes:
        return []
    median_height = float(np.median([box[3] for box in boxes]))
    components: list[tuple[int, int, int, int, bool]] = []
    for x, y, box_width, box_height, area in boxes:
        decimal = allow_decimal and box_height <= median_height * 0.35 and box_width <= median_height * 0.35 and y > height * 0.45
        if not decimal and box_height < max(5, median_height * 0.45):
            continue
        components.append((x, y, box_width, box_height, decimal))
    return sorted(components, key=lambda item: item[0])


def _prepare_model_glyph(glyph: np.ndarray) -> np.ndarray:
    ys, xs = np.where(glyph > 0)
    if not len(xs):
        raise ValueError("Digit glyph is empty")
    crop = glyph[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    scale = min(20 / crop.shape[1], 20 / crop.shape[0])
    resized = cv2.resize(crop, (max(1, round(crop.shape[1] * scale)), max(1, round(crop.shape[0] * scale))), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((28, 28), dtype=np.float32)
    y = (28 - resized.shape[0]) // 2
    x = (28 - resized.shape[1]) // 2
    canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized.astype(np.float32) / 255.0
    return canvas


def _softmax(values: np.ndarray) -> np.ndarray:
    shifted = values - np.max(values)
    exponentials = np.exp(shifted)
    return exponentials / np.sum(exponentials)
