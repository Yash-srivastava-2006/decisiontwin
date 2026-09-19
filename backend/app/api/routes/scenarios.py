"""What-if scenario routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.scenario import ScenarioOptionsResponse, ScenarioSimulationRequest, ScenarioSimulationResponse
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/datasets", tags=["scenarios"])


def get_scenario_service(session: Session = Depends(get_db)) -> ScenarioService:
    return ScenarioService(session)


@router.get("/{dataset_id}/scenarios/options", response_model=ScenarioOptionsResponse)
def get_scenario_options(dataset_id: UUID, service: ScenarioService = Depends(get_scenario_service)) -> ScenarioOptionsResponse:
    return service.options(dataset_id)


@router.post("/{dataset_id}/scenarios/simulate", response_model=ScenarioSimulationResponse)
def simulate_scenario(dataset_id: UUID, request: ScenarioSimulationRequest, service: ScenarioService = Depends(get_scenario_service)) -> ScenarioSimulationResponse:
    return service.simulate(dataset_id, request)