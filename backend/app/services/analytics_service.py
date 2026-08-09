"""Dataset analytics and profiling service."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import numpy as np
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.analytics import (
    AnalyticsResponse,
    BusinessKPIs,
    CategoricalStatistics,
    CategoricalValueCount,
    ColumnProfile,
    CorrelationResponse,
    DatasetProfile,
    InsightItem,
    NumericStatistics,
    QualityWarning,
)
from app.services.dataset_service import DatasetService
from app.utils.analytics import (
    OUTLIER_WARNING_THRESHOLD,
    PRICE_KEYWORDS,
    PROFIT_KEYWORDS,
    QUANTITY_KEYWORDS,
    REVENUE_KEYWORDS,
    STRONG_CORRELATION_THRESHOLD,
    classify_column,
    calculate_quality_score,
    build_top_values,
    detect_business_metric_column,
    detect_column_type_counts,
    is_high_cardinality,
    is_potential_identifier,
    safe_float,
    safe_numeric_series,
)


class AnalyticsService:
    """Generate dataset analytics directly from stored CSV files."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = DatasetRepository(session)
        self.dataset_service = DatasetService(session)

    def get_dataset(self, dataset_id: UUID) -> Dataset:
        dataset = self.repository.get(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset

    def profile_dataset(self, dataset_id: UUID) -> tuple[Dataset, pd.DataFrame, DatasetProfile]:
        dataset = self.get_dataset(dataset_id)
        dataframe = self._load_dataframe(dataset)
        profile = self._build_profile(dataset, dataframe)
        return dataset, dataframe, profile

    def columns_profile(self, dataset_id: UUID) -> list[ColumnProfile]:
        _, dataframe, _ = self.profile_dataset(dataset_id)
        return self._build_column_profiles(dataframe)

    def numeric_statistics(self, dataset_id: UUID) -> dict[str, NumericStatistics]:
        _, dataframe, _ = self.profile_dataset(dataset_id)
        return self._build_numeric_statistics(dataframe)

    def categorical_statistics(self, dataset_id: UUID) -> dict[str, CategoricalStatistics]:
        _, dataframe, _ = self.profile_dataset(dataset_id)
        return self._build_categorical_statistics(dataframe)

    def correlation(self, dataset_id: UUID) -> CorrelationResponse:
        _, dataframe, _ = self.profile_dataset(dataset_id)
        return self._build_correlation(dataframe)

    def data_quality_warnings(self, dataset_id: UUID) -> list[QualityWarning]:
        _, dataframe, profile = self.profile_dataset(dataset_id)
        return self._build_quality_warnings(dataframe, profile)

    def kpis(self, dataset_id: UUID) -> BusinessKPIs:
        _, dataframe, _ = self.profile_dataset(dataset_id)
        return self._build_kpis(dataframe)

    def insights(self, dataset_id: UUID) -> list[InsightItem]:
        _, dataframe, profile = self.profile_dataset(dataset_id)
        return self._build_insights(dataframe, profile)

    def analytics(self, dataset_id: UUID) -> AnalyticsResponse:
        dataset, dataframe, profile = self.profile_dataset(dataset_id)
        columns = self._build_column_profiles(dataframe)
        numeric_statistics = self._build_numeric_statistics(dataframe)
        categorical_statistics = self._build_categorical_statistics(dataframe)
        correlation = self._build_correlation(dataframe)
        quality_warnings = self._build_quality_warnings(dataframe, profile)
        kpis = self._build_kpis(dataframe)
        insights = self._build_insights(dataframe, profile, quality_warnings)

        return AnalyticsResponse(
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            generated_at=datetime.now(timezone.utc),
            profile=profile,
            columns=columns,
            numeric_statistics=numeric_statistics,
            categorical_statistics=categorical_statistics,
            correlation=correlation,
            quality_warnings=quality_warnings,
            kpis=kpis,
            insights=insights,
        )

    def _load_dataframe(self, dataset: Dataset) -> pd.DataFrame:
        try:
            dataframe = self.dataset_service.load_dataset_dataframe(dataset)
        except HTTPException:
            raise
        if dataframe.empty and len(dataframe.columns) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file does not contain data")
        return dataframe

    def _build_profile(self, dataset: Dataset, dataframe: pd.DataFrame) -> DatasetProfile:
        counts = detect_column_type_counts(dataframe)
        missing_values = int(dataframe.isna().sum().sum())
        duplicate_rows = int(dataframe.duplicated().sum())
        quality_score, quality_label = calculate_quality_score(
            total_rows=int(len(dataframe)),
            missing_values=missing_values,
            duplicate_rows=duplicate_rows,
            empty_columns=counts.empty,
            constant_columns=counts.constant,
            high_cardinality_columns=self._count_high_cardinality_columns(dataframe),
        )
        total_rows = max(1, int(len(dataframe)))
        return DatasetProfile(
            total_rows=int(len(dataframe)),
            total_columns=int(dataframe.shape[1]),
            file_size=int(dataset.file_size),
            memory_usage=int(dataframe.memory_usage(deep=True).sum()),
            missing_values=missing_values,
            missing_percentage=round((missing_values / (total_rows * max(1, int(dataframe.shape[1])))) * 100, 2),
            duplicate_rows=duplicate_rows,
            duplicate_percentage=round((duplicate_rows / total_rows) * 100, 2),
            numeric_columns=counts.numeric,
            categorical_columns=counts.categorical,
            datetime_columns=counts.datetime,
            text_columns=counts.text,
            empty_columns=counts.empty,
            constant_columns=counts.constant,
            quality_score=quality_score,
            quality_label=quality_label,
        )

    def _build_column_profiles(self, dataframe: pd.DataFrame) -> list[ColumnProfile]:
        total_rows = max(1, int(len(dataframe)))
        profiles: list[ColumnProfile] = []
        for column in dataframe.columns:
            series = dataframe[column]
            classification = classify_column(series)
            null_count = int(series.isna().sum())
            unique_count = int(series.dropna().nunique(dropna=True))
            profiles.append(
                ColumnProfile(
                    name=str(column),
                    dtype=str(series.dtype),
                    null_count=null_count,
                    null_percentage=round((null_count / total_rows) * 100, 2),
                    unique_count=unique_count,
                    unique_percentage=round((unique_count / total_rows) * 100, 2),
                    is_numeric=classification["is_numeric"],
                    is_categorical=classification["is_categorical"],
                    is_datetime=classification["is_datetime"],
                    is_boolean=classification["is_boolean"],
                    is_constant=classification["is_constant"],
                    is_potential_id=is_potential_identifier(str(column), series),
                )
            )
        return profiles

    def _build_numeric_statistics(self, dataframe: pd.DataFrame) -> dict[str, NumericStatistics]:
        statistics: dict[str, NumericStatistics] = {}
        for column in dataframe.columns:
            series = safe_numeric_series(dataframe[column])
            if series.empty:
                continue

            q1 = float(series.quantile(0.25))
            q2 = float(series.quantile(0.50))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            outlier_count = int(((series < lower_bound) | (series > upper_bound)).sum())
            mode_series = series.mode(dropna=True)
            mode_value = mode_series.iloc[0] if not mode_series.empty else None
            variance = float(series.var(ddof=1)) if len(series) > 1 else None
            standard_deviation = float(series.std(ddof=1)) if len(series) > 1 else None
            statistics[str(column)] = NumericStatistics(
                count=int(series.count()),
                sum=safe_float(series.sum()),
                mean=safe_float(series.mean()),
                median=safe_float(series.median()),
                mode=safe_float(mode_value),
                min=safe_float(series.min()),
                max=safe_float(series.max()),
                range=safe_float(series.max() - series.min()),
                variance=safe_float(variance),
                standard_deviation=safe_float(standard_deviation),
                percentile_25=safe_float(q1),
                percentile_50=safe_float(q2),
                percentile_75=safe_float(q3),
                iqr=safe_float(iqr),
                outlier_count=outlier_count,
            )
        return statistics

    def _build_categorical_statistics(self, dataframe: pd.DataFrame) -> dict[str, CategoricalStatistics]:
        statistics: dict[str, CategoricalStatistics] = {}
        for column in dataframe.columns:
            series = dataframe[column]
            classification = classify_column(series)
            if not classification["is_categorical"] or classification["is_numeric"] or classification["is_datetime"]:
                continue

            non_null = series.dropna()
            if non_null.empty:
                continue

            counts = non_null.astype(str).value_counts(dropna=True)
            most_common_value = counts.index[0] if not counts.empty else None
            most_common_count = int(counts.iloc[0]) if not counts.empty else 0
            statistics[str(column)] = CategoricalStatistics(
                unique_count=int(non_null.nunique(dropna=True)),
                most_common_value=str(most_common_value) if most_common_value is not None else None,
                most_common_count=most_common_count,
                top_values=[
                    CategoricalValueCount(**entry)
                    for entry in build_top_values(non_null, limit=10)
                ],
            )
        return statistics

    def _build_correlation(self, dataframe: pd.DataFrame) -> CorrelationResponse:
        numeric_columns = [str(column) for column in dataframe.columns if not safe_numeric_series(dataframe[column]).empty]
        if len(numeric_columns) < 2:
            return CorrelationResponse(
                columns=numeric_columns,
                matrix=[],
                message="At least two numeric columns are required to compute correlation.",
            )

        numeric_frame = pd.DataFrame({column: pd.to_numeric(dataframe[column], errors="coerce") for column in numeric_columns})
        numeric_frame = numeric_frame.replace([np.inf, -np.inf], np.nan)
        correlation = numeric_frame.corr(method="pearson")
        matrix = correlation.round(6).where(pd.notna(correlation), None).values.tolist()
        return CorrelationResponse(columns=numeric_columns, matrix=matrix, message="Correlation matrix generated.")

    def _build_quality_warnings(self, dataframe: pd.DataFrame, profile: DatasetProfile) -> list[QualityWarning]:
        warnings: list[QualityWarning] = []
        total_rows = max(1, int(len(dataframe)))

        for column in dataframe.columns:
            series = dataframe[column]
            null_count = int(series.isna().sum())
            null_percentage = (null_count / total_rows) * 100
            if null_count > 0:
                severity = self._severity_for_ratio(null_count / total_rows)
                warnings.append(
                    QualityWarning(
                        type="missing_values",
                        severity=severity,
                        column=str(column),
                        message=f"Column '{column}' contains {round(null_percentage, 1)}% missing values.",
                    )
                )

            if series.dropna().empty:
                warnings.append(
                    QualityWarning(
                        type="empty_column",
                        severity="high",
                        column=str(column),
                        message=f"Column '{column}' is empty.",
                    )
                )
                continue

            if series.dropna().nunique(dropna=True) <= 1:
                warnings.append(
                    QualityWarning(
                        type="constant_column",
                        severity="medium",
                        column=str(column),
                        message=f"Column '{column}' contains a constant value.",
                    )
                )
                continue

            if is_high_cardinality(series):
                warnings.append(
                    QualityWarning(
                        type="high_cardinality",
                        severity="medium",
                        column=str(column),
                        message=f"Column '{column}' has high cardinality.",
                    )
                )

            if is_potential_identifier(str(column), series):
                warnings.append(
                    QualityWarning(
                        type="potential_id",
                        severity="low",
                        column=str(column),
                        message=f"Column '{column}' appears to be an identifier column.",
                    )
                )

        duplicate_rows = int(dataframe.duplicated().sum())
        if duplicate_rows > 0:
            warnings.append(
                QualityWarning(
                    type="duplicate_rows",
                    severity=self._severity_for_ratio(duplicate_rows / total_rows),
                    message=f"Dataset contains {duplicate_rows} duplicate rows.",
                )
            )

        if profile.missing_percentage >= 10:
            warnings.append(
                QualityWarning(
                    type="dataset_missing_values",
                    severity=self._severity_for_ratio(profile.missing_percentage / 100),
                    message=f"Dataset has {profile.missing_percentage}% missing values overall.",
                )
            )

        if profile.quality_score < 75:
            warnings.append(
                QualityWarning(
                    type="quality_score",
                    severity="medium" if profile.quality_score >= 50 else "high",
                    message=f"Dataset quality score is {profile.quality_score} ({profile.quality_label}).",
                )
            )

        return warnings

    def _build_kpis(self, dataframe: pd.DataFrame) -> BusinessKPIs:
        revenue_column = detect_business_metric_column(list(dataframe.columns), REVENUE_KEYWORDS)
        profit_column = detect_business_metric_column(list(dataframe.columns), PROFIT_KEYWORDS)
        quantity_column = detect_business_metric_column(list(dataframe.columns), QUANTITY_KEYWORDS)
        price_column = detect_business_metric_column(list(dataframe.columns), PRICE_KEYWORDS)

        revenue_series = safe_numeric_series(dataframe[revenue_column]) if revenue_column else pd.Series(dtype=float)
        profit_series = safe_numeric_series(dataframe[profit_column]) if profit_column else pd.Series(dtype=float)
        quantity_series = safe_numeric_series(dataframe[quantity_column]) if quantity_column else pd.Series(dtype=float)
        price_series = safe_numeric_series(dataframe[price_column]) if price_column else pd.Series(dtype=float)

        profit_margin = None
        if not profit_series.empty and not revenue_series.empty:
            revenue_sum = float(revenue_series.sum())
            if revenue_sum:
                profit_margin = safe_float(float(profit_series.sum()) / revenue_sum)

        return BusinessKPIs(
            total_revenue=safe_float(revenue_series.sum()) if not revenue_series.empty else None,
            average_revenue=safe_float(revenue_series.mean()) if not revenue_series.empty else None,
            maximum_revenue=safe_float(revenue_series.max()) if not revenue_series.empty else None,
            minimum_revenue=safe_float(revenue_series.min()) if not revenue_series.empty else None,
            total_profit=safe_float(profit_series.sum()) if not profit_series.empty else None,
            average_profit=safe_float(profit_series.mean()) if not profit_series.empty else None,
            profit_margin=profit_margin,
            total_quantity=safe_float(quantity_series.sum()) if not quantity_series.empty else None,
            average_quantity=safe_float(quantity_series.mean()) if not quantity_series.empty else None,
            average_price=safe_float(price_series.mean()) if not price_series.empty else None,
        )

    def _build_insights(
        self,
        dataframe: pd.DataFrame,
        profile: DatasetProfile,
        quality_warnings: list[QualityWarning] | None = None,
    ) -> list[InsightItem]:
        insights: list[InsightItem] = []
        quality_warnings = quality_warnings or []

        for warning in quality_warnings:
            if warning.type in {"missing_values", "duplicate_rows", "empty_column", "constant_column"}:
                insights.append(
                    InsightItem(
                        type="data_quality",
                        severity=warning.severity,
                        column=warning.column,
                        message=warning.message,
                    )
                )

        numeric_frame = pd.DataFrame({column: safe_numeric_series(dataframe[column]) for column in dataframe.columns})
        numeric_columns = [column for column in numeric_frame.columns if not numeric_frame[column].empty]
        if len(numeric_columns) >= 2:
            correlation = numeric_frame[numeric_columns].corr(method="pearson")
            for i, left_column in enumerate(numeric_columns):
                for right_column in numeric_columns[i + 1 :]:
                    value = correlation.loc[left_column, right_column]
                    if pd.notna(value) and abs(float(value)) >= STRONG_CORRELATION_THRESHOLD:
                        insights.append(
                            InsightItem(
                                type="correlation",
                                severity="medium",
                                message=f"Columns '{left_column}' and '{right_column}' have a strong {'positive' if value > 0 else 'negative'} correlation of {round(float(value), 2)}.",
                                metadata={"left_column": left_column, "right_column": right_column, "correlation": round(float(value), 4)},
                            )
                        )

        for column in dataframe.columns:
            series = dataframe[column]
            numeric_series = safe_numeric_series(series)
            if numeric_series.empty:
                continue
            q1 = float(numeric_series.quantile(0.25))
            q3 = float(numeric_series.quantile(0.75))
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_count = int(((numeric_series < lower) | (numeric_series > upper)).sum())
            if outlier_count >= OUTLIER_WARNING_THRESHOLD:
                insights.append(
                    InsightItem(
                        type="outlier_detection",
                        severity="medium",
                        column=str(column),
                        message=f"Column '{column}' contains {outlier_count} outliers detected with the IQR rule.",
                        metadata={"outlier_count": outlier_count, "iqr": round(iqr, 4)},
                    )
                )

            skewness = numeric_series.skew()
            if pd.notna(skewness) and abs(float(skewness)) >= 1.0:
                insights.append(
                    InsightItem(
                        type="distribution",
                        severity="low",
                        column=str(column),
                        message=f"Column '{column}' shows a {'right' if skewness > 0 else 'left'}-skewed numeric distribution.",
                        metadata={"skewness": round(float(skewness), 4)},
                    )
                )

        for column in dataframe.columns:
            series = dataframe[column]
            if series.dropna().empty:
                continue
            if not series.dropna().dtype == object:
                continue
            value_counts = series.dropna().astype(str).value_counts(normalize=True)
            if not value_counts.empty and float(value_counts.iloc[0]) >= 0.6:
                insights.append(
                    InsightItem(
                        type="category_concentration",
                        severity="medium",
                        column=str(column),
                        message=f"Column '{column}' is concentrated in the '{value_counts.index[0]}' category.",
                        metadata={"dominant_value": value_counts.index[0], "share": round(float(value_counts.iloc[0]) * 100, 2)},
                    )
                )
                break

        if profile.quality_score >= 90:
            insights.append(
                InsightItem(
                    type="quality_observation",
                    severity="low",
                    message=f"Dataset quality is strong with a score of {profile.quality_score} ({profile.quality_label}).",
                )
            )
        elif profile.quality_score < 75:
            insights.append(
                InsightItem(
                    type="quality_observation",
                    severity="medium" if profile.quality_score >= 50 else "high",
                    message=f"Dataset quality score is {profile.quality_score} ({profile.quality_label}) and warrants review.",
                )
            )

        return insights

    def _count_high_cardinality_columns(self, dataframe: pd.DataFrame) -> int:
        return sum(1 for column in dataframe.columns if is_high_cardinality(dataframe[column]))

    def _severity_for_ratio(self, ratio: float) -> str:
        if ratio >= 0.2:
            return "high"
        if ratio >= 0.05:
            return "medium"
        return "low"
