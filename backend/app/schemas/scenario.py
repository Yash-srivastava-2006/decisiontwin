"""Schemas for non-destructive what-if scenario analysis."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ScenarioChangeRequest(BaseModel):
    column: str = Field(min_length=1)
    mode: Literal["absolute", "percentage"] = "absolute"
    value: float

    @field_validator("value")
    @classmethod
    def validate_finite_value(cls, value: float) -> float:
        if value != value or value in {float("inf"), float("-inf")}:
            raise ValueError("Scenario value must be a finite number")
        return value


class ScenarioSimulationRequest(BaseModel):
    changes: list[ScenarioChangeRequest] = Field(min_length=1)
    target_metrics: list[str] = Field(min_length=1)


class ScenarioVariableOption(BaseModel):
    name: str
    baseline: float
    minimum: float
    maximum: float
    mean: float


class ScenarioMetricOption(BaseModel):
    name: str
    column: str
    aggregation: Literal["sum", "mean", "median", "min", "max"]
    baseline: float


class ScenarioOptionsResponse(BaseModel):
    dataset_id: UUID
    numeric_columns: list[ScenarioVariableOption] = Field(default_factory=list)
    metrics: list[ScenarioMetricOption] = Field(default_factory=list)
    decision_variables: list[ScenarioVariableOption] = Field(default_factory=list)
    target_metrics: list[ScenarioMetricOption] = Field(default_factory=list)
    excluded_columns: list[str] = Field(default_factory=list)


class NormalizedScenarioChange(BaseModel):
    column: str
    mode: Literal["absolute", "percentage"]
    input_value: float
    baseline_value: float
    scenario_value: float


class ScenarioImpact(BaseModel):
    metric: str
    baseline: float
    scenario: float | None
    absolute_change: float | None
    percentage_change: float | None
    direction: Literal["increase", "decrease", "unchanged", "unavailable"]
    calculation_method: str


class ScenarioSimulationResponse(BaseModel):
    dataset_id: UUID
    changes: list[NormalizedScenarioChange]
    impacts: list[ScenarioImpact]
    calculation_methods: list[str]