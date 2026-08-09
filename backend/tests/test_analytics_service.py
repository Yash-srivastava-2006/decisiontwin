from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pandas as pd
import pytest
from fastapi import HTTPException

from app.models.dataset import Dataset
from app.schemas.analytics import QualityWarning
from app.services.analytics_service import AnalyticsService


@pytest.fixture()
def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "revenue": [100.0, 150.0, 200.0, 1000.0, 125.0],
            "profit": [20.0, 30.0, 40.0, 250.0, 25.0],
            "quantity": [1, 2, 3, 4, 5],
            "price": [10.0, 12.0, 14.0, 16.0, 18.0],
            "category": ["A", "A", "B", "A", "A"],
            "discount": [1.0, None, 2.0, None, 3.0],
            "constant": ["same", "same", "same", "same", "same"],
            "identifier": [1, 2, 3, 4, 5],
        }
    )


@pytest.fixture()
def duplicate_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "value": [1, 1, 1, 10],
            "label": ["x", "x", "x", "y"],
        }
    )


@pytest.fixture()
def analytics_service() -> AnalyticsService:
    return AnalyticsService(session=SimpleNamespace())


@pytest.fixture()
def dataset() -> Dataset:
    return Dataset(
        id=uuid4(),
        name="Sample",
        original_filename="sample.csv",
        description=None,
        file_type="csv",
        file_size=1234,
        total_rows=5,
        total_columns=8,
        file_path="/tmp/sample.csv",
        columns=[],
        dtypes={},
        missing_values={},
    )


@pytest.fixture()
def loaded_service(analytics_service: AnalyticsService, dataset: Dataset, sample_dataframe: pd.DataFrame, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)
    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: sample_dataframe)
    return analytics_service


def test_profile_calculation(loaded_service: AnalyticsService, dataset: Dataset):
    _, _, profile = loaded_service.profile_dataset(dataset.id)

    assert profile.total_rows == 5
    assert profile.total_columns == 8
    assert profile.file_size == 1234
    assert profile.quality_score <= 100
    assert profile.quality_label in {"Excellent", "Good", "Average", "Poor"}


def test_missing_values_and_duplicates(sample_dataframe: pd.DataFrame, duplicate_dataframe: pd.DataFrame, analytics_service: AnalyticsService, dataset: Dataset, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)
    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: sample_dataframe)
    warnings = analytics_service.data_quality_warnings(dataset.id)

    missing_warning = next((warning for warning in warnings if warning.type == "missing_values" and warning.column == "discount"), None)
    constant_warning = next((warning for warning in warnings if warning.type == "constant_column" and warning.column == "constant"), None)
    assert missing_warning is not None
    assert constant_warning is not None

    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: duplicate_dataframe)
    duplicate_warnings = analytics_service.data_quality_warnings(dataset.id)
    assert any(warning.type == "duplicate_rows" for warning in duplicate_warnings)


def test_quality_score(sample_dataframe: pd.DataFrame, analytics_service: AnalyticsService, dataset: Dataset, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)
    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: sample_dataframe)
    _, _, profile = analytics_service.profile_dataset(dataset.id)

    assert 0 <= profile.quality_score <= 100
    assert profile.quality_label == "Average" or profile.quality_label in {"Excellent", "Good", "Poor"}


def test_numeric_statistics_and_outliers(sample_dataframe: pd.DataFrame, analytics_service: AnalyticsService, dataset: Dataset, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)
    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: sample_dataframe)
    stats = analytics_service.numeric_statistics(dataset.id)

    assert "revenue" in stats
    assert stats["revenue"].count == 5
    assert stats["revenue"].outlier_count >= 0
    assert stats["profit"].median is not None


def test_categorical_statistics(sample_dataframe: pd.DataFrame, analytics_service: AnalyticsService, dataset: Dataset, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)
    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: sample_dataframe)
    stats = analytics_service.categorical_statistics(dataset.id)

    assert "category" in stats
    assert stats["category"].unique_count == 2
    assert stats["category"].top_values[0].count >= 1
    assert len(stats["category"].top_values) <= 10


def test_correlation(sample_dataframe: pd.DataFrame, analytics_service: AnalyticsService, dataset: Dataset, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)
    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: sample_dataframe)
    response = analytics_service.correlation(dataset.id)

    assert response.columns
    assert response.message == "Correlation matrix generated."
    assert len(response.columns) >= 2


def test_kpi_detection(sample_dataframe: pd.DataFrame, analytics_service: AnalyticsService, dataset: Dataset, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)
    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: sample_dataframe)
    kpis = analytics_service.kpis(dataset.id)

    assert kpis.total_revenue is not None
    assert kpis.average_revenue is not None
    assert kpis.total_profit is not None
    assert kpis.total_quantity is not None
    assert kpis.average_price is not None


def test_insight_generation(sample_dataframe: pd.DataFrame, analytics_service: AnalyticsService, dataset: Dataset, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)
    monkeypatch.setattr(analytics_service, "_load_dataframe", lambda stored_dataset: sample_dataframe)
    insights = analytics_service.insights(dataset.id)

    assert insights
    assert any(insight.type in {"data_quality", "quality_observation", "correlation", "outlier_detection", "distribution", "category_concentration"} for insight in insights)


def test_missing_dataset(analytics_service: AnalyticsService):
    analytics_service.repository.get = lambda dataset_id: None

    with pytest.raises(HTTPException) as exc_info:
        analytics_service.get_dataset(uuid4())

    assert exc_info.value.status_code == 404


def test_invalid_dataset(sample_dataframe: pd.DataFrame, analytics_service: AnalyticsService, dataset: Dataset, monkeypatch):
    monkeypatch.setattr(analytics_service, "get_dataset", lambda dataset_id: dataset)

    def raise_bad_csv(_: Dataset):
        raise HTTPException(status_code=400, detail="Malformed CSV file")

    monkeypatch.setattr(analytics_service, "_load_dataframe", raise_bad_csv)

    with pytest.raises(HTTPException) as exc_info:
        analytics_service.profile_dataset(dataset.id)

    assert exc_info.value.status_code == 400
