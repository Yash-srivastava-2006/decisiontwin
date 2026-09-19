import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card } from '../components/common/Card'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { useActiveDataset } from '../context/ActiveDatasetContext'
import { useScenarioOptions, useScenarioSimulation } from '../hooks/useScenario'
import { formatNumber, formatPercent } from '../utils/format'
import type { ScenarioChangeRequest } from '../types/scenario'

interface LocalChange extends ScenarioChangeRequest { id: number }

export function SimulatorPage() {
  const { activeDataset } = useActiveDataset()
  const datasetId = activeDataset?.id
  const options = useScenarioOptions(datasetId)
  const simulation = useScenarioSimulation(datasetId)
  const variables = options.data?.decision_variables ?? options.data?.numeric_columns ?? []
  const metrics = options.data?.target_metrics ?? options.data?.metrics ?? []
  const [changes, setChanges] = useState<LocalChange[]>([])
  const [targets, setTargets] = useState<string[]>([])
  const [nextId, setNextId] = useState(1)

  useEffect(() => {
    if (!variables.length) return
    setChanges((current) => current.length ? current : [{ id: 0, column: variables[0].name, mode: 'absolute', value: variables[0].baseline }])
    const defaultTargets = Array.from(new Map(metrics.map((metric) => [metric.column, metric])).values()).map((metric) => metric.column)
    setTargets((current) => (current.length ? current : defaultTargets.slice(0, 1)))
  }, [variables, metrics])

  const availableTargets = useMemo(
    () => Array.from(new Map(metrics.map((metric) => [metric.column, metric])).values()),
    [metrics],
  )

  if (!activeDataset) return <EmptyState title="Select a dataset" description="Select a dataset to create a scenario." />
  if (options.isLoading) return <LoadingState label="Loading simulator options..." />
  if (options.isError) return <ErrorState title="Simulator unavailable" message="The dataset options could not be loaded." onRetry={() => options.refetch()} />
  if (!variables.length) return <EmptyState title="No numeric variables available" description="No numeric variables are available for scenario analysis." />

  const updateChange = (id: number, patch: Partial<LocalChange>) => setChanges((current) => current.map((change) => change.id === id ? { ...change, ...patch } : change))
  const addChange = () => {
    const used = new Set(changes.map((change) => change.column))
    const nextVariable = variables.find((variable) => !used.has(variable.name))
    if (!nextVariable) return
    setChanges((current) => [...current, { id: nextId, column: nextVariable.name, mode: 'absolute', value: nextVariable.baseline }])
    setNextId((id) => id + 1)
  }
  const runSimulation = () => {
    if (!targets.length || changes.some((change) => !Number.isFinite(change.value))) return
    simulation.mutate({
      changes: changes.map(({ id: _id, ...change }) => change),
      target_metrics: Array.from(new Set(targets)),
    })
  }
  const result = simulation.data
  const chartData = result?.impacts.map((impact) => ({ metric: impact.metric, Baseline: impact.baseline, Scenario: impact.scenario })) || []

  return <div className="dataset-page simulator-page">
    <div className="page-titlebar"><div><span className="section-eyebrow">Phase 6 / scenario analysis</span><h1>Decision Simulator</h1><p>Explore the deterministic impact of changing values in {activeDataset.name}.</p></div></div>
    <div className="detail-grid">
      <Card title="Scenario variables" subtitle="Changes are applied to an in-memory copy of the dataset.">
        <div className="simulator-controls">{changes.map((change, index) => { const variable = variables.find((item) => item.name === change.column) || variables[0]; const calculated = change.mode === 'percentage' ? variable.baseline * (1 + change.value / 100) : variable.baseline + change.value; return <div className="scenario-row" key={change.id}>
          <div className="scenario-row__heading"><strong>Variable {index + 1}</strong>{changes.length > 1 ? <button type="button" className="text-button" onClick={() => setChanges((current) => current.filter((item) => item.id !== change.id))}>Remove</button> : null}</div>
          <label className="field"><span>Numeric column</span><select value={change.column} onChange={(event) => { const selected = variables.find((item) => item.name === event.target.value); updateChange(change.id, { column: event.target.value, value: selected?.baseline || 0 }) }}>{variables.filter((item) => !changes.some((other) => other.id !== change.id && other.column === item.name)).map((item) => <option key={item.name}>{item.name}</option>)}</select></label>
          <div className="form-grid"><label className="field"><span>Change mode</span><select value={change.mode} onChange={(event) => updateChange(change.id, { mode: event.target.value as LocalChange['mode'], value: event.target.value === 'absolute' ? variable.baseline : 10 })}><option value="absolute">Absolute value</option><option value="percentage">Percentage</option></select></label><label className="field"><span>{change.mode === 'absolute' ? 'Scenario value' : 'Change (%)'}</span><input type="number" value={change.value} onChange={(event) => updateChange(change.id, { value: Number(event.target.value) })} /></label></div>
          <div className="scenario-preview"><span>Baseline {formatNumber(variable.baseline)}</span><strong>Scenario {formatNumber(calculated)}</strong><small>Range {formatNumber(variable.minimum)} to {formatNumber(variable.maximum)}</small></div>
        </div> })}</div>
        <button type="button" className="button button--secondary" onClick={addChange} disabled={changes.length >= variables.length}>+ Add variable</button>
      </Card>
      <Card title="Target metrics" subtitle="Select the aggregate metrics to compare."><div className="metric-options">{availableTargets.map((metric) => <label className="metric-option" key={metric.column}><input type="checkbox" checked={targets.includes(metric.column)} onChange={(event) => setTargets((current) => event.target.checked ? Array.from(new Set([...current, metric.column])) : current.filter((item) => item !== metric.column))} /><span>{metric.name}</span></label>)}</div><button type="button" className="button button--primary" onClick={runSimulation} disabled={!targets.length || simulation.isPending}>{simulation.isPending ? 'Calculating...' : 'Run simulation'}</button>{simulation.isError ? <p className="form-error">Unable to calculate this scenario.</p> : null}</Card>
    </div>
    {result ? <><Card title="Baseline vs scenario" subtitle="Deterministic scenario impact based on the selected assumptions."><div className="table-scroll"><table className="analysis-table"><thead><tr><th>Metric</th><th>Baseline</th><th>Scenario</th><th>Change</th><th>Method</th></tr></thead><tbody>{result.impacts.map((impact) => <tr key={`${impact.metric}-${impact.calculation_method}`}><td>{impact.metric}</td><td>{formatNumber(impact.baseline)}</td><td>{formatNumber(impact.scenario)}</td><td className={`impact-${impact.direction}`}>{formatPercent(impact.percentage_change)}</td><td>{impact.calculation_method}</td></tr>)}</tbody></table></div></Card><div className="detail-grid"><Card title="Scenario impact"><ResponsiveContainer width="100%" height={280}><BarChart data={chartData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="metric" angle={-20} textAnchor="end" height={60} interval={0} /><YAxis /><Tooltip /><Legend /><Bar dataKey="Baseline" fill="var(--muted-foreground)" /><Bar dataKey="Scenario" fill="var(--accent)" /></BarChart></ResponsiveContainer></Card><Card title="Calculation method"><p className="method-note">{result.calculation_methods.join(', ')}. Results are deterministic scenario calculations, not ML predictions.</p></Card></div></> : null}
  </div>
}