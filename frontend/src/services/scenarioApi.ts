import { requestJson } from './api'
import type { ScenarioOptionsResponse, ScenarioSimulationRequest, ScenarioSimulationResponse } from '../types/scenario'

export function getScenarioOptions(datasetId: string): Promise<ScenarioOptionsResponse> {
  return requestJson<ScenarioOptionsResponse>({ method: 'GET', url: `/api/v1/datasets/${datasetId}/scenarios/options` })
}

export function simulateScenario(datasetId: string, request: ScenarioSimulationRequest): Promise<ScenarioSimulationResponse> {
  return requestJson<ScenarioSimulationResponse>({
    method: 'POST',
    url: `/api/v1/datasets/${datasetId}/scenarios/simulate`,
    data: request,
  })
}