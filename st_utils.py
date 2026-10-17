"""Reusable validation and terminal-table utilities."""
from __future__ import annotations
import re
from datetime import date
from typing import Iterable, Sequence

_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PHONE = re.compile(r"^[0-9+() .-]+$")

class ValidationError(ValueError):
    """Raised when input does not satisfy the field's validation rules."""

def clean_text(value: str, field: str, minimum: int = 1, maximum: int = 100) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be text.")
    result = " ".join(value.strip().split())
    if len(result) < minimum:
        raise ValidationError(f"{field} cannot be empty and must contain at least {minimum} character(s).")
    if len(result) > maximum:
        raise ValidationError(f"{field} must be no longer than {maximum} characters.")
    return result

def validate_email(value: str) -> str:
    email = value.strip().lower() if isinstance(value, str) else ""
    if len(email) > 254 or not _EMAIL.fullmatch(email):
        raise ValidationError("Enter a valid email address, for example name@example.com.")
    return email

def validate_phone(value: str) -> str:
    phone = value.strip() if isinstance(value, str) else ""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not _PHONE.fullmatch(phone) or not 7 <= len(digits) <= 15:
        raise ValidationError("Enter a valid phone number containing 7–15 digits.")
    return phone

def validate_duration(value: str) -> str:
    return clean_text(value, "Course duration", 1, 50)

def validate_fee(value: object) -> float:
    try:
        fee = float(value)
    except (TypeError, ValueError) as error:
        raise ValidationError("Course fee must be a number.") from error
    if fee < 0 or fee != fee or fee in (float("inf"), float("-inf")) or fee > 1_000_000_000:
        raise ValidationError("Course fee must be a finite non-negative number within the allowed range.")
    return round(fee, 2)

def validate_id(value: object, field: str = "ID") -> int:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{field} must be a whole number.") from error
    if number <= 0:
        raise ValidationError(f"{field} must be greater than zero.")
    return number

def validate_date(value: str | None) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return date.today().isoformat()
    if not isinstance(value, str):
        raise ValidationError("Enrollment date must use YYYY-MM-DD format.")
    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError as error:
        raise ValidationError("Enrollment date must use YYYY-MM-DD format.") from error
    if parsed.isoformat() != value.strip():
        raise ValidationError("Enrollment date must use YYYY-MM-DD format.")
    return parsed.isoformat()

def print_table(headers: Sequence[object], rows: Iterable[Sequence[object]]) -> None:
    data = [["-" if item is None else str(item) for item in row] for row in rows]
    widths = [len(str(header)) for header in headers]
    for row in data:
        for i, value in enumerate(row[:len(widths)]):
            widths[i] = min(max(widths[i], len(value)), 34)
    def render(values: Sequence[object]) -> str:
        cells = []
        for i, item in enumerate(values[:len(widths)]):
            text = str(item).replace("\n", " ")
            if len(text) > widths[i]:
                text = text[:max(1, widths[i] - 1)] + "…"
            cells.append(text.ljust(widths[i]))
        return " | ".join(cells)
    print(render(headers))
    print("-+-".join("-" * width for width in widths))
    if not data:
        print("(no records found)")
        return
    for row in data:
        print(render(row))
