import { useMutation, useQuery } from '@tanstack/react-query'
import { getScenarioOptions, simulateScenario } from '../services/scenarioApi'
import type { ScenarioSimulationRequest } from '../types/scenario'

export function useScenarioOptions(datasetId?: string) {
  return useQuery({
    queryKey: ['scenarios', datasetId, 'options'],
    queryFn: () => getScenarioOptions(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useScenarioSimulation(datasetId?: string) {
  return useMutation({
    mutationFn: (request: ScenarioSimulationRequest) => simulateScenario(datasetId || '', request),
  })
}