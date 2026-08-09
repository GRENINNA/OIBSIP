"""BMI calculation, validation, and classification rules."""

from __future__ import annotations

import math
from typing import NamedTuple


CATEGORY_COLORS = {
    "Underweight": "#2563EB",
    "Normal": "#15803D",
    "Overweight": "#C2410C",
    "Obese": "#B91C1C",
}


class BMIResult(NamedTuple):
    bmi: float
    category: str
    color: str


def classify_bmi(bmi: float) -> tuple[str, str]:
    """Return the standard health category and its display colour."""
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obese"
    return category, CATEGORY_COLORS[category]


def calculate_bmi(weight_kg: float, height_m: float) -> BMIResult:
    """Calculate BMI after validating positive, finite measurements."""
    if not math.isfinite(weight_kg) or not math.isfinite(height_m):
        raise ValueError("Weight and height must be finite numbers.")
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than 0 kg.")
    if height_m <= 0:
        raise ValueError("Height must be greater than 0 m.")

    bmi = weight_kg / (height_m**2)
    category, color = classify_bmi(bmi)
    return BMIResult(bmi, category, color)
