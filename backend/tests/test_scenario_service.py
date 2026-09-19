from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pandas as pd
import pytest
from fastapi import HTTPException

from app.schemas.scenario import ScenarioChangeRequest, ScenarioSimulationRequest
from app.services.scenario_service import ScenarioService


@pytest.fixture()
def scenario_setup(monkeypatch):
    dataset_id = uuid4()
    dataset = SimpleNamespace(id=dataset_id)
    dataframe = pd.DataFrame({"sales": [100.0, 200.0], "quantity": [2.0, 4.0], "category": ["A", "B"]})
    service = ScenarioService(SimpleNamespace())
    monkeypatch.setattr(service.repository, "get", lambda requested_id: dataset if requested_id == dataset_id else None)
    monkeypatch.setattr(service.dataset_service, "load_dataset_dataframe", lambda _: dataframe)
    return service, dataset_id, dataframe


def test_absolute_scenario_recalculates_changed_metric_without_mutating_source(scenario_setup):
    service, dataset_id, dataframe = scenario_setup
    result = service.simulate(
        dataset_id,
        ScenarioSimulationRequest(
            changes=[ScenarioChangeRequest(column="sales", mode="absolute", value=160)],
            target_metrics=["sales"],
        ),
    )

    assert result.changes[0].scenario_value == 160
    assert result.impacts[0].baseline == 300
    assert result.impacts[0].scenario == 320
    assert dataframe["sales"].tolist() == [100.0, 200.0]


def test_percentage_and_multiple_changes(scenario_setup):
    service, dataset_id, _ = scenario_setup
    result = service.simulate(
        dataset_id,
        ScenarioSimulationRequest(
            changes=[
                ScenarioChangeRequest(column="sales", mode="percentage", value=10),
                ScenarioChangeRequest(column="quantity", mode="absolute", value=2),
            ],
            target_metrics=["sales", "quantity"],
        ),
    )

    assert [change.scenario_value for change in result.changes] == [165, 2]
    assert [impact.scenario for impact in result.impacts] == [330, 4]


@pytest.mark.parametrize(
    ("changes", "metrics", "message"),
    [
        ([ScenarioChangeRequest(column="missing", value=1)], ["sales"], "not found"),
        ([ScenarioChangeRequest(column="category", value=1)], ["sales"], "not numeric"),
        ([ScenarioChangeRequest(column="sales", value=1), ScenarioChangeRequest(column="sales", value=2)], ["sales"], "duplicate"),
        ([ScenarioChangeRequest(column="sales", value=1)], ["category"], "not numeric"),
    ],
)
def test_invalid_scenarios_raise_http_400(scenario_setup, changes, metrics, message):
    service, dataset_id, _ = scenario_setup
    with pytest.raises(HTTPException) as error:
        service.simulate(dataset_id, ScenarioSimulationRequest(changes=changes, target_metrics=metrics))
    assert error.value.status_code == 400
    assert message in str(error.value.detail)


def test_options_exclude_identifier_and_helper_columns():
    dataset_id = uuid4()
    dataset = SimpleNamespace(id=dataset_id)
    dataframe = pd.DataFrame(
        {
            "Transaction ID": [101, 102, 103],
            "Day_Sort": [1, 2, 3],
            "Month_sort": [1, 1, 2],
            "Quantity": [2.0, 4.0, 6.0],
            "Price per Unit": [10.0, 11.0, 12.0],
            "Total Amount": [20.0, 44.0, 72.0],
        }
    )
    service = ScenarioService(SimpleNamespace())
    service.repository.get = lambda requested_id: dataset if requested_id == dataset_id else None
    service.dataset_service.load_dataset_dataframe = lambda _: dataframe

    result = service.options(dataset_id)

    assert [option.name for option in result.decision_variables] == ["Quantity", "Price per Unit", "Total Amount"]
    assert [metric.column for metric in result.target_metrics][:3] == ["Quantity", "Quantity", "Quantity"]
    assert result.excluded_columns == ["Transaction ID", "Day_Sort", "Month_sort"]


def test_duplicate_target_metrics_are_deduplicated_and_unique_impacts(scenario_setup):
    service, dataset_id, _ = scenario_setup
    result = service.simulate(
        dataset_id,
        ScenarioSimulationRequest(
            changes=[ScenarioChangeRequest(column="sales", mode="percentage", value=10)],
            target_metrics=["sales", "sales", "sales"],
        ),
    )

    assert [impact.metric for impact in result.impacts] == ["sales"]
    assert len(result.impacts) == 1


def test_identifier_columns_are_rejected_for_changes_and_targets():
    dataset_id = uuid4()
    dataset = SimpleNamespace(id=dataset_id)
    dataframe = pd.DataFrame(
        {
            "Transaction ID": [101, 102, 103],
            "sales": [100.0, 200.0, 300.0],
        }
    )
    service = ScenarioService(SimpleNamespace())
    service.repository.get = lambda requested_id: dataset if requested_id == dataset_id else None
    service.dataset_service.load_dataset_dataframe = lambda _: dataframe

    with pytest.raises(HTTPException) as error:
        service.simulate(
            dataset_id,
            ScenarioSimulationRequest(
                changes=[ScenarioChangeRequest(column="Transaction ID", mode="absolute", value=10)],
                target_metrics=["sales"],
            ),
        )
    assert "identifier" in str(error.value.detail).lower()

    with pytest.raises(HTTPException) as error:
        service.simulate(
            dataset_id,
            ScenarioSimulationRequest(
                changes=[ScenarioChangeRequest(column="sales", mode="absolute", value=10)],
                target_metrics=["Transaction ID"],
            ),
        )
    assert "identifier" in str(error.value.detail).lower()


def test_missing_dataset_returns_404(scenario_setup):
    service, _, _ = scenario_setup
    with pytest.raises(HTTPException) as error:
        service.options(uuid4())
    assert error.value.status_code == 404