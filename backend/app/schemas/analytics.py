"""Analytics request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsMessageResponse(BaseModel):
    """Simple success response for analytics endpoints."""

    model_config = ConfigDict(from_attributes=True)

    status: str = "success"
    message: str


class ColumnProfile(BaseModel):
    """Column-level metadata and type inference."""

    name: str
    dtype: str
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    is_numeric: bool
    is_categorical: bool
    is_datetime: bool
    is_boolean: bool
    is_constant: bool
    is_potential_id: bool


class DatasetProfile(BaseModel):
    """Overall dataset profile."""

    total_rows: int
    total_columns: int
    file_size: int
    memory_usage: int
    missing_values: int
    missing_percentage: float
    duplicate_rows: int
    duplicate_percentage: float
    numeric_columns: int
    categorical_columns: int
    datetime_columns: int
    text_columns: int
    empty_columns: int
    constant_columns: int
    quality_score: int
    quality_label: str


class NumericStatistics(BaseModel):
    """Numeric statistics for a single column."""

    count: int
    sum: float | None
    mean: float | None
    median: float | None
    mode: float | None
    min: float | None
    max: float | None
    range: float | None
    variance: float | None
    standard_deviation: float | None
    percentile_25: float | None
    percentile_50: float | None
    percentile_75: float | None
    iqr: float | None
    outlier_count: int


class CategoricalValueCount(BaseModel):
    """Value frequency entry for categorical columns."""

    value: str
    count: int
    percentage: float


class CategoricalStatistics(BaseModel):
    """Categorical statistics for a single column."""

    unique_count: int
    most_common_value: str | None
    most_common_count: int
    top_values: list[CategoricalValueCount]


class CorrelationResponse(BaseModel):
    """Correlation matrix payload."""

    columns: list[str]
    matrix: list[list[float | None]]
    message: str | None = None


class QualityWarning(BaseModel):
    """Structured data quality warning."""

    type: str
    severity: str
    column: str | None = None
    message: str


class BusinessKPIs(BaseModel):
    """Calculated business KPIs inferred from dataset columns."""

    total_revenue: float | None = None
    average_revenue: float | None = None
    maximum_revenue: float | None = None
    minimum_revenue: float | None = None
    total_profit: float | None = None
    average_profit: float | None = None
    profit_margin: float | None = None
    total_quantity: float | None = None
    average_quantity: float | None = None
    average_price: float | None = None


class InsightItem(BaseModel):
    """Deterministic rule-based insight."""

    type: str
    severity: str
    message: str
    column: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsResponse(BaseModel):
    """Unified frontend-ready analytics payload."""

    model_config = ConfigDict(from_attributes=True)

    dataset_id: UUID
    dataset_name: str
    generated_at: datetime
    profile: DatasetProfile
    columns: list[ColumnProfile]
    numeric_statistics: dict[str, NumericStatistics]
    categorical_statistics: dict[str, CategoricalStatistics]
    correlation: CorrelationResponse
    quality_warnings: list[QualityWarning]
    kpis: BusinessKPIs
    insights: list[InsightItem]


class AnalyticsCollectionResponse(BaseModel):
    """Response wrapper used by analytics endpoints."""

    model_config = ConfigDict(from_attributes=True)

    status: str = "success"
    message: str
    data: Any

class HistogramBin(BaseModel):
    label: str
    count: int
    start: float
    end: float

class DistributionAnalysis(BaseModel):
    column: str
    count: int
    mean: float | None
    median: float | None
    min: float | None
    max: float | None
    standard_deviation: float | None
    q1: float | None
    q2: float | None
    q3: float | None
    histogram: list[HistogramBin]

class OutlierAnalysis(BaseModel):
    column: str
    lower_bound: float | None
    upper_bound: float | None
    outlier_count: int
    outlier_percentage: float
    values: list[float]

class CategoryPerformanceItem(BaseModel):
    category: str
    count: int
    sum: float
    average: float
    min: float
    max: float

class CategoryPerformanceResponse(BaseModel):
    category_column: str | None = None
    metric_column: str | None = None
    items: list[CategoryPerformanceItem] = Field(default_factory=list)
    message: str | None = None

class TrendPoint(BaseModel):
    date: str
    value: float

class TrendResponse(BaseModel):
    date_column: str | None = None
    metric_column: str | None = None
    granularity: str
    points: list[TrendPoint] = Field(default_factory=list)
    message: str | None = None

class RankingItem(BaseModel):
    category: str
    metric: str
    value: float
    rank: int

class RankingResponse(BaseModel):
    category_column: str | None = None
    metric_column: str | None = None
    direction: str
    items: list[RankingItem] = Field(default_factory=list)
    message: str | None = None

class CorrelationPair(BaseModel):
    column_a: str
    column_b: str
    correlation: float
    absolute_correlation: float
    strength: str
