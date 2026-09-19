"""Transparent, non-destructive what-if scenario calculations."""

from __future__ import annotations

import math
import re
from uuid import UUID

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import DatasetRepository
from app.schemas.scenario import (
    NormalizedScenarioChange,
    ScenarioChangeRequest,
    ScenarioImpact,
    ScenarioMetricOption,
    ScenarioOptionsResponse,
    ScenarioSimulationResponse,
    ScenarioSimulationRequest,
    ScenarioVariableOption,
)
from app.services.dataset_service import DatasetService
from app.utils.analytics import safe_numeric_series


AGGREGATIONS = ("sum", "mean", "median", "min", "max")
IDENTIFIER_KEYWORDS = (
    "id",
    "transaction",
    "customer",
    "order",
    "product",
    "user",
    "account",
    "record",
    "uuid",
    "key",
)
HELPER_KEYWORDS = ("sort", "day_sort", "month_sort", "year_sort")


class ScenarioService:
    """Calculate dataset-aware scenarios without persisting hypothetical data."""

    def __init__(self, session: Session) -> None:
        self.repository = DatasetRepository(session)
        self.dataset_service = DatasetService(session)

    @staticmethod
    def _normalize_column_name(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")

    @classmethod
    def _is_helper_sort_column(cls, column_name: str) -> bool:
        normalized = cls._normalize_column_name(column_name)
        if not normalized:
            return False
        if normalized == "sort":
            return True
        if normalized.endswith("_sort"):
            return True
        return any(keyword in normalized for keyword in ("day_sort", "month_sort", "year_sort"))

    @classmethod
    def _is_identifier_name(cls, column_name: str) -> bool:
        normalized = cls._normalize_column_name(column_name)
        if not normalized:
            return False
        if normalized in {"id", "uuid", "key"}:
            return True
        if normalized.endswith("_id") or normalized.startswith("id_"):
            return True
        if any(keyword in normalized for keyword in IDENTIFIER_KEYWORDS):
            if "_id" in normalized or "id" in normalized or normalized.endswith("_key"):
                return True
        return False

    @staticmethod
    def _is_sequential_identifier_candidate(series: pd.Series) -> bool:
        numeric = safe_numeric_series(series)
        if numeric.empty:
            return False
        unique_values = pd.Series(pd.unique(numeric.round().astype(float))).sort_values().tolist()
        if len(unique_values) < 2 or len(unique_values) != len(numeric):
            return False
        if unique_values[0] not in {0, 1}:
            return False
        expected = list(range(unique_values[0], unique_values[0] + len(unique_values)))
        return unique_values == expected

    @classmethod
    def _classify_excluded_column(cls, column_name: str, series: pd.Series | None = None) -> str | None:
        if cls._is_helper_sort_column(column_name):
            return "helper"
        if cls._is_identifier_name(column_name):
            return "identifier"
        if series is not None and cls._is_sequential_identifier_candidate(series):
            return "identifier"
        return None

    def _load_dataframe(self, dataset_id: UUID) -> tuple[object, pd.DataFrame]:
        dataset = self.repository.get(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        dataframe = self.dataset_service.load_dataset_dataframe(dataset)
        if len(dataframe) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset must contain at least one row")
        return dataset, dataframe

    @staticmethod
    def _numeric_columns(dataframe: pd.DataFrame) -> list[str]:
        return [str(column) for column in dataframe.columns if not safe_numeric_series(dataframe[column]).empty]

    @staticmethod
    def _aggregate(series: pd.Series, aggregation: str) -> float | None:
        numeric = safe_numeric_series(series)
        if numeric.empty:
            return None
        value = getattr(numeric, aggregation)()
        return float(value) if math.isfinite(float(value)) else None

    @staticmethod
    def _deduplicate_preserve_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        return ordered

    def options(self, dataset_id: UUID) -> ScenarioOptionsResponse:
        dataset, dataframe = self._load_dataframe(dataset_id)
        excluded_columns: list[str] = []
        variables: list[ScenarioVariableOption] = []
        metrics: list[ScenarioMetricOption] = []

        for column in dataframe.columns:
            numeric = safe_numeric_series(dataframe[column])
            if numeric.empty:
                continue
            reason = self._classify_excluded_column(str(column), numeric)
            if reason is not None:
                excluded_columns.append(str(column))
                continue
            variables.append(
                ScenarioVariableOption(
                    name=str(column),
                    baseline=round(float(numeric.mean()), 12),
                    minimum=round(float(numeric.min()), 12),
                    maximum=round(float(numeric.max()), 12),
                    mean=round(float(numeric.mean()), 12),
                )
            )
            for aggregation in AGGREGATIONS:
                baseline = self._aggregate(numeric, aggregation)
                if baseline is not None:
                    metrics.append(
                        ScenarioMetricOption(
                            name=f"{column} ({aggregation})",
                            column=str(column),
                            aggregation=aggregation,
                            baseline=round(float(baseline), 12),
                        )
                    )

        response = ScenarioOptionsResponse(
            dataset_id=dataset.id,
            numeric_columns=variables,
            metrics=metrics,
            decision_variables=variables,
            target_metrics=metrics,
            excluded_columns=excluded_columns,
        )
        return response

    def _validate_change_columns(self, dataframe: pd.DataFrame, requested_columns: list[str]) -> list[str]:
        valid_numeric = self._numeric_columns(dataframe)
        for column in requested_columns:
            if column not in dataframe.columns:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Scenario column not found: {column}")
            reason = self._classify_excluded_column(column, dataframe[column])
            if reason == "identifier":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{column} is not a valid scenario variable because it is classified as an identifier.",
                )
            if reason == "helper":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{column} is not a valid scenario variable because it is classified as a helper/sort column.",
                )
            if column not in valid_numeric:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Scenario column is not numeric: {column}")
        return valid_numeric

    def simulate(self, dataset_id: UUID, request: ScenarioSimulationRequest) -> ScenarioSimulationResponse:
        dataset, dataframe = self._load_dataframe(dataset_id)
        valid_numeric = self._numeric_columns(dataframe)
        requested_columns = [change.column for change in request.changes]
        if len(set(requested_columns)) != len(requested_columns):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scenario changes must not contain duplicate columns")
        self._validate_change_columns(dataframe, requested_columns)

        unique_metrics = self._deduplicate_preserve_order(request.target_metrics)
        scenario = dataframe.copy(deep=True)
        normalized: list[NormalizedScenarioChange] = []
        for change in request.changes:
            numeric = safe_numeric_series(dataframe[change.column])
            baseline = float(numeric.mean())
            scenario_value = change.value if change.mode == "absolute" else baseline * (1 + change.value / 100)
            if not math.isfinite(scenario_value):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scenario value must be a finite number")
            scenario[change.column] = pd.to_numeric(scenario[change.column], errors="coerce")
            if change.mode == "absolute":
                scenario[change.column] = scenario[change.column] + (change.value - baseline)
            else:
                scenario[change.column] = scenario[change.column] * (1 + change.value / 100)
            normalized.append(NormalizedScenarioChange(column=change.column, mode=change.mode, input_value=change.value, baseline_value=baseline, scenario_value=scenario_value))

        impacts: list[ScenarioImpact] = []
        methods: set[str] = set()
        for metric in unique_metrics:
            if metric not in dataframe.columns:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Target metric not found: {metric}")
            reason = self._classify_excluded_column(metric, dataframe[metric])
            if reason == "identifier":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{metric} is not a valid target metric because it is classified as an identifier.",
                )
            if reason == "helper":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{metric} is not a valid target metric because it is classified as a helper/sort column.",
                )
            if metric not in valid_numeric:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Target metric is not numeric: {metric}")
            baseline = self._aggregate(dataframe[metric], "sum")
            scenario_value = self._aggregate(scenario[metric], "sum")
            if baseline is None or scenario_value is None:
                impacts.append(
                    ScenarioImpact(
                        metric=metric,
                        baseline=baseline if baseline is not None else 0.0,
                        scenario=None,
                        absolute_change=None,
                        percentage_change=None,
                        direction="unavailable",
                        calculation_method="unavailable",
                    )
                )
                methods.add("unavailable")
                continue
            change = scenario_value - baseline
            percentage = (change / baseline) * 100 if baseline else None
            direction = "increase" if change > 0 else "decrease" if change < 0 else "unchanged"
            method = "direct_recalculation" if metric in requested_columns else "baseline_unchanged"
            methods.add(method)
            impacts.append(
                ScenarioImpact(
                    metric=metric,
                    baseline=round(float(baseline), 12),
                    scenario=round(float(scenario_value), 12) if metric in requested_columns else round(float(baseline), 12),
                    absolute_change=round(float(change), 12) if metric in requested_columns else 0.0,
                    percentage_change=round(float(percentage), 12) if metric in requested_columns and percentage is not None else 0.0,
                    direction=direction if metric in requested_columns else "unchanged",
                    calculation_method=method,
                )
            )
        return ScenarioSimulationResponse(dataset_id=dataset.id, changes=normalized, impacts=impacts, calculation_methods=sorted(methods))