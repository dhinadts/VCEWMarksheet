from decimal import Decimal, InvalidOperation


class NumericNormalizationError(ValueError):
    """The recognizer output is not an unambiguous numeric mark."""


def normalize_numeric_token(
    raw_text: str,
    *,
    minimum: Decimal = Decimal("0"),
    maximum: Decimal = Decimal("100"),
    allow_decimal: bool = False,
    decimal_places: int = 1,
) -> Decimal:
    """Convert an OCR token to a locale-independent Decimal without guessing.

    Only ASCII digits and, when enabled, one dot are accepted. Ambiguous OCR
    letters such as ``l`` or ``O`` are intentionally rejected rather than
    silently replaced. The returned Decimal is safe for a SQL NUMERIC column.
    """
    token = raw_text.strip()
    if not token:
        raise NumericNormalizationError("No numeric token was recognized")
    allowed = set("0123456789") | ({"."} if allow_decimal else set())
    if any(character not in allowed for character in token):
        raise NumericNormalizationError("Recognized token contains a non-numeric symbol")
    if token.count(".") > 1 or token.startswith(".") or token.endswith("."):
        raise NumericNormalizationError("Recognized token has an invalid decimal point")
    if "." in token and not allow_decimal:
        raise NumericNormalizationError("Decimal marks are disabled for this assessment")
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise NumericNormalizationError("Recognized token is not numeric") from exc
    if value < minimum or value > maximum:
        raise NumericNormalizationError(f"Recognized value must be between {minimum} and {maximum}")
    if -value.as_tuple().exponent > decimal_places:
        raise NumericNormalizationError(f"At most {decimal_places} decimal place(s) are allowed")
    return value


def json_numeric(value: Decimal) -> int | float:
    """Return a JSON number, never a locale-formatted numeric string."""
    return int(value) if value == value.to_integral_value() else float(value)
