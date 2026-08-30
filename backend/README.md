# Marksheet System Backend (Phases 1–2)

FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, JWT authentication, and academic master data.

## Development

```powershell
Copy-Item ..\.env.example ..\.env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

OpenAPI is at `http://localhost:8000/docs`. Seeded accounts use `DEMO_DEFAULT_PASSWORD` and require a password change.

## Offline handwritten numeric extraction

The OCR numeric cell extractor uses OpenCV and a local ONNX digit model. It
does not call a cloud service and does not require any API key. The model must
accept a `1 x 1 x 28 x 28` grayscale tensor and return ten logits ordered
`0..9`.

```python
from app.services.ocr import (
    OpenCVDnnDigitClassifier,
    extract_handwritten_numeric,
    save_numeric_result,
)

classifier = OpenCVDnnDigitClassifier("models/handwritten_digits.onnx")
result = extract_handwritten_numeric(
    "cell.jpg",
    classifier,
    minimum=0,
    maximum=20,
    allow_decimal=True,
)

print(result.numeric_value)  # Decimal('12.5'), safe for SQL NUMERIC
save_numeric_result("output/cell_result.json", result)
```

Uncertain results set `requires_review=True`. Invalid or out-of-range values
raise an error and are never silently corrected.
