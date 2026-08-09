"""Shared analytics helpers for dataset profiling and insights."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

QUALITY_LABELS = (
    (90, "Excellent"),
    (75, "Good"),
    (50, "Average"),
    (0, "Poor"),
)

REVENUE_KEYWORDS = ("revenue", "sales", "income", "amount")
PROFIT_KEYWORDS = ("profit", "net_profit", "gross_profit")
COST_KEYWORDS = ("cost", "expense", "spending")
QUANTITY_KEYWORDS = ("quantity", "qty", "units")
PRICE_KEYWORDS = ("price", "unit_price")

HIGH_CARDINALITY_RATIO = 0.9
HIGH_MISSING_RATIO = 0.3
HIGH_MISSING_WARNING_RATIO = 0.2
IDENTIFIER_RATIO = 0.95
STRONG_CORRELATION_THRESHOLD = 0.8
OUTLIER_WARNING_THRESHOLD = 5


@dataclass(slots=True)
class ColumnTypeSummary:
    numeric: int
    categorical: int
    datetime: int
    text: int
    empty: int
    constant: int


def is_effectively_missing(value: Any) -> bool:
    """Return True for NaN-like or infinite placeholders."""
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value) or math.isinf(value)
    return False


def safe_numeric_series(series: pd.Series) -> pd.Series:
    """Coerce a series to finite numeric values only."""
    numeric = pd.to_numeric(series, errors="coerce")
    numeric = numeric.replace([np.inf, -np.inf], np.nan)
    return numeric.dropna()


def classify_column(series: pd.Series) -> dict[str, bool]:
    """Infer common semantic column types from a pandas series."""
    non_null = series.dropna()
    if non_null.empty:
        return {
            "is_numeric": False,
            "is_categorical": False,
            "is_datetime": False,
            "is_boolean": False,
            "is_constant": False,
            "is_potential_id": False,
        }

    dtype = series.dtype
    is_bool = pd.api.types.is_bool_dtype(dtype) or str(dtype) == "boolean"
    is_numeric = pd.api.types.is_numeric_dtype(dtype) and not is_bool
    is_datetime = pd.api.types.is_datetime64_any_dtype(dtype)
    unique_count = int(non_null.nunique(dropna=True))
    total_count = int(len(series)) or 1
    unique_ratio = unique_count / total_count
    is_constant = unique_count <= 1
    is_potential_id = unique_ratio >= IDENTIFIER_RATIO and unique_count >= min(total_count, 10)

    if is_datetime:
        is_categorical = False
    elif is_numeric:
        is_categorical = False
    elif is_bool:
        is_categorical = True
    else:
        is_categorical = True

    return {
        "is_numeric": is_numeric,
        "is_categorical": is_categorical,
        "is_datetime": is_datetime,
        "is_boolean": is_bool,
        "is_constant": is_constant,
        "is_potential_id": is_potential_id,
    }


def infer_datetime_column(series: pd.Series) -> bool:
    """Try a lightweight datetime inference for object columns."""
    if pd.api.types.is_datetime64_any_dtype(series.dtype):
        return True
    if not pd.api.types.is_object_dtype(series.dtype):
        return False

    sample = series.dropna().astype(str).head(25)
    if sample.empty:
        return False

    parsed = pd.to_datetime(sample, errors="coerce")
    return float(parsed.notna().mean()) >= 0.8


def detect_column_type_counts(dataframe: pd.DataFrame) -> ColumnTypeSummary:
    """Count broad column categories for a dataframe."""
    numeric = categorical = datetime = text = empty = constant = 0
    for column in dataframe.columns:
        series = dataframe[column]
        non_null = series.dropna()
        if non_null.empty:
            empty += 1
            constant += 1
            continue
        if infer_datetime_column(series):
            datetime += 1
            continue

        classification = classify_column(series)
        if classification["is_numeric"]:
            numeric += 1
        elif classification["is_boolean"]:
            categorical += 1
        elif classification["is_categorical"]:
            if pd.api.types.is_object_dtype(series.dtype) and non_null.astype(str).str.len().mean() > 40:
                text += 1
            else:
                categorical += 1

        if classification["is_constant"]:
            constant += 1

    return ColumnTypeSummary(
        numeric=numeric,
        categorical=categorical,
        datetime=datetime,
        text=text,
        empty=empty,
        constant=constant,
    )


def calculate_quality_score(
    *,
    total_rows: int,
    missing_values: int,
    duplicate_rows: int,
    empty_columns: int,
    constant_columns: int,
    high_cardinality_columns: int,
) -> tuple[int, str]:
    """Compute a deterministic quality score.

    The score starts at 100 and subtracts penalties for quality risks. The weighting
    is intentionally explicit so that it can be tuned later without changing the
    public API shape.
    """

    if total_rows <= 0:
        return 0, "Poor"

    missing_ratio = missing_values / total_rows
    duplicate_ratio = duplicate_rows / total_rows

    score = 100.0
    score -= min(35.0, missing_ratio * 60.0)
    score -= min(20.0, duplicate_ratio * 80.0)
    score -= min(15.0, empty_columns * 8.0)
    score -= min(10.0, constant_columns * 4.0)
    score -= min(10.0, high_cardinality_columns * 2.5)

    final_score = max(0, min(100, int(round(score))))
    label = quality_label_for_score(final_score)
    return final_score, label


def quality_label_for_score(score: int) -> str:
    """Map a numeric score to a quality label."""
    for threshold, label in QUALITY_LABELS:
        if score >= threshold:
            return label
    return "Poor"


def build_top_values(series: pd.Series, limit: int = 10) -> list[dict[str, Any]]:
    """Return the most common values for a categorical series."""
    counts = series.fillna("<missing>").astype(str).value_counts(dropna=False).head(limit)
    total = len(series) or 1
    return [
        {
            "value": index,
            "count": int(count),
            "percentage": round((int(count) / total) * 100, 2),
        }
        for index, count in counts.items()
    ]


def is_high_cardinality(series: pd.Series) -> bool:
    """Detect columns whose unique values dominate the column."""
    non_null = series.dropna()
    if non_null.empty:
        return False
    unique_ratio = non_null.nunique(dropna=True) / len(series)
    return unique_ratio >= HIGH_CARDINALITY_RATIO


def is_potential_identifier(column_name: str, series: pd.Series) -> bool:
    """Heuristically detect identifier-like columns."""
    classification = classify_column(series)
    if classification["is_potential_id"]:
        return True

    name = column_name.lower()
    if re.search(r"(^|_)(id|uuid|key)$", name):
        return True

    return False


def detect_business_metric_column(columns: list[str], keywords: tuple[str, ...]) -> str | None:
    """Return the first column whose name matches a list of business keywords."""
    lowered = [column.lower() for column in columns]
    for keyword in keywords:
        for column, lower_name in zip(columns, lowered, strict=False):
            if keyword in lower_name:
                return column
    return None


def safe_float(value: Any) -> float | None:
    """Convert a numeric-like value into a JSON-friendly float."""
    if value is None:
        return None
    if isinstance(value, (np.floating, float, int, np.integer)):
        if pd.isna(value) or np.isinf(value):
            return None
        return float(value)
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(converted) or math.isinf(converted):
        return None
    return converted
