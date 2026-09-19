export interface ScenarioVariableOption {
  name: string
  baseline: number
  minimum: number
  maximum: number
  mean: number
}

export interface ScenarioMetricOption {
  name: string
  column: string
  aggregation: string
  baseline: number
}

export interface ScenarioOptionsResponse {
  dataset_id: string
  numeric_columns: ScenarioVariableOption[]
  metrics: ScenarioMetricOption[]
  decision_variables?: ScenarioVariableOption[]
  target_metrics?: ScenarioMetricOption[]
  excluded_columns?: string[]
}

export interface ScenarioChangeRequest {
  column: string
  mode: 'absolute' | 'percentage'
  value: number
}

export interface ScenarioSimulationRequest {
  changes: ScenarioChangeRequest[]
  target_metrics: string[]
}

export interface NormalizedScenarioChange {
  column: string
  mode: 'absolute' | 'percentage'
  input_value: number
  baseline_value: number
  scenario_value: number
}

export interface ScenarioImpact {
  metric: string
  baseline: number
  scenario: number | null
  absolute_change: number | null
  percentage_change: number | null
  direction: 'increase' | 'decrease' | 'unchanged' | 'unavailable'
  calculation_method: string
}

export interface ScenarioSimulationResponse {
  dataset_id: string
  changes: NormalizedScenarioChange[]
  impacts: ScenarioImpact[]
  calculation_methods: string[]
}