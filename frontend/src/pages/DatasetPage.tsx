import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ChevronLeft, RefreshCcw, Trash2 } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card } from '../components/common/Card'
import { CategoryBarChart } from '../components/charts/CategoryBarChart'
import { CorrelationMatrix } from '../components/charts/CorrelationMatrix'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { QualityMeter } from '../components/common/QualityMeter'
import { StatCard } from '../components/common/StatCard'
import { useDeleteDataset, useDataset, useDatasetPreview } from '../hooks/useDataset'
import { useActiveDataset } from '../context/ActiveDatasetContext'
import {
  useCategoricalStatistics,
  useCorrelation,
  useDatasetColumns,
  useDatasetProfile,
  useInsights,
  useKpis,
  useNumericStatistics,
  useQualityWarnings,
} from '../hooks/useAnalytics'
import {
  formatDateTime,
  formatInteger,
  formatNumber,
  formatPercent,
  qualityTone,
  safeText,
  severityTone,
} from '../utils/format'

function chartColor(index: number): string {
  return index === 0 ? 'var(--accent)' : 'rgba(14, 116, 144, 0.58)'
}

export function DatasetPage() {
  const navigate = useNavigate()
  const { datasetId } = useParams<{ datasetId: string }>()
  const { setActiveDatasetId } = useActiveDataset()
  useEffect(() => { setActiveDatasetId(datasetId) }, [datasetId, setActiveDatasetId])
  const datasetQuery = useDataset(datasetId)
  const previewQuery = useDatasetPreview(datasetId)
  const profileQuery = useDatasetProfile(datasetId)
  const columnsQuery = useDatasetColumns(datasetId)
  const numericQuery = useNumericStatistics(datasetId)
  const categoricalQuery = useCategoricalStatistics(datasetId)
  const correlationQuery = useCorrelation(datasetId)
  const kpisQuery = useKpis(datasetId)
  const insightsQuery = useInsights(datasetId)
  const warningsQuery = useQualityWarnings(datasetId)
  const deleteMutation = useDeleteDataset()
  const [selectedNumericColumn, setSelectedNumericColumn] = useState('')
  const [selectedCategoricalColumn, setSelectedCategoricalColumn] = useState('')

  const dataset = datasetQuery.data
  const profile = profileQuery.data
  const columns = columnsQuery.data || []
  const numericStatistics = numericQuery.data || {}
  const categoricalStatistics = categoricalQuery.data || {}
  const correlation = correlationQuery.data
  const kpis = kpisQuery.data
  const insights = insightsQuery.data || []
  const warnings = warningsQuery.data || []

  const numericColumns = useMemo(
    () => columns.filter((column) => column.is_numeric).map((column) => column.name),
    [columns],
  )
  const categoricalColumns = useMemo(
    () => columns.filter((column) => column.is_categorical && !column.is_numeric && !column.is_datetime).map((column) => column.name),
    [columns],
  )

  const selectedNumeric = selectedNumericColumn || numericColumns[0] || ''
  const selectedCategorical = selectedCategoricalColumn || categoricalColumns[0] || ''
  const selectedNumericStats = selectedNumeric ? numericStatistics[selectedNumeric] : undefined
  const selectedCategoricalStats = selectedCategorical ? categoricalStatistics[selectedCategorical] : undefined

  if (datasetQuery.isLoading || profileQuery.isLoading) {
    return <LoadingState label="Loading dataset analytics..." />
  }

  if (datasetQuery.isError || profileQuery.isError) {
    return (
      <ErrorState
        title="Unable to load dataset"
        message="The dataset may have been deleted or the backend may be unavailable."
        onRetry={() => {
          void datasetQuery.refetch()
          void profileQuery.refetch()
        }}
      />
    )
  }

  if (!dataset || !profile) {
    return (
      <EmptyState
        title="Dataset not found"
        description="The requested dataset could not be loaded."
        action={<Link to="/datasets" className="button button--primary">Back to datasets</Link>}
      />
    )
  }

  async function handleDelete() {
    if (!dataset) {
      return
    }

    const confirmed = window.confirm(`Delete ${dataset.name}? This cannot be undone.`)
    if (!confirmed) {
      return
    }

    await deleteMutation.mutateAsync(dataset.id)
    navigate('/datasets')
  }

  const availableKpis = Object.entries(kpis || {}).filter(([, value]) => value !== null && value !== undefined)
  const hasNumericData = numericColumns.length > 0
  const hasCategoricalData = categoricalColumns.length > 0
  const chartSeries = selectedNumericStats
    ? [
        { label: 'Q1', value: selectedNumericStats.percentile_25 },
        { label: 'Median', value: selectedNumericStats.median },
        { label: 'Q3', value: selectedNumericStats.percentile_75 },
        { label: 'Max', value: selectedNumericStats.max },
      ].filter((item) => item.value !== null)
    : []

  const qualityClass = qualityTone(profile.quality_score)

  return (
    <div className="dataset-page">
      <div className="page-titlebar">
        <div>
          <Link to="/datasets" className="back-link">
            <ChevronLeft size={16} /> Back to datasets
          </Link>
          <h1>{dataset.name}</h1>
          <p>
            {safeText(dataset.original_filename)} Â· Uploaded {formatDateTime(dataset.uploaded_at)}
          </p>
        </div>
        <div className="page-titlebar__actions">
          <button type="button" className="button button--secondary" onClick={() => void profileQuery.refetch()}>
            <RefreshCcw size={16} /> Refresh
          </button>
          <button
            type="button"
            className="button button--ghost button--danger"
            onClick={() => void handleDelete()}
            disabled={deleteMutation.isPending}
          >
            <Trash2 size={16} /> Delete
          </button>
        </div>
      </div>

      <section className="metric-grid">
        <StatCard label="Rows" value={formatInteger(profile.total_rows)} />
        <StatCard label="Columns" value={formatInteger(profile.total_columns)} />
        <StatCard label="Missing values" value={formatInteger(profile.missing_values)} />
        <StatCard
          label="Quality score"
          value={formatInteger(profile.quality_score)}
          tone={qualityClass === 'poor' ? 'critical' : qualityClass === 'average' ? 'warning' : 'positive'}
        />
      </section>

      <section className="detail-grid">
        <Card title="Dataset profile" subtitle="Shape, completeness, and quality">
          <QualityMeter score={profile.quality_score} label={profile.quality_label} />
          <div className="profile-grid">
            <div><span>Rows</span><strong>{formatInteger(profile.total_rows)}</strong></div>
            <div><span>Columns</span><strong>{formatInteger(profile.total_columns)}</strong></div>
            <div><span>Numeric</span><strong>{formatInteger(profile.numeric_columns)}</strong></div>
            <div><span>Categorical</span><strong>{formatInteger(profile.categorical_columns)}</strong></div>
            <div><span>Datetime</span><strong>{formatInteger(profile.datetime_columns)}</strong></div>
            <div><span>Missing</span><strong>{formatInteger(profile.missing_values)}</strong></div>
            <div><span>Duplicates</span><strong>{formatInteger(profile.duplicate_rows)}</strong></div>
            <div><span>Quality label</span><strong>{profile.quality_label}</strong></div>
          </div>
        </Card>

        <Card title="Business KPIs" subtitle="Values inferred from the backend">
          {availableKpis.length === 0 ? (
            <EmptyState
              title="No KPIs available"
              description="The backend did not infer any business KPI columns for this dataset."
            />
          ) : (
            <div className="kpi-grid">
              {availableKpis.map(([key, value]) => (
                <StatCard key={key} label={key.replace(/_/g, ' ')} value={formatNumber(value as number | null)} />
              ))}
            </div>
          )}
        </Card>
      </section>

      <section className="detail-grid">
        <Card title="Column analysis" subtitle="Sortable summary of dataset columns">
          {columns.length === 0 ? (
            <EmptyState title="No columns found" description="The dataset does not contain analyzable columns." />
          ) : (
            <div className="table-scroll">
              <table className="analysis-table">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Data Type</th>
                    <th>Nulls</th>
                    <th>Null %</th>
                    <th>Unique</th>
                    <th>Unique %</th>
                    <th>Numeric</th>
                    <th>Categorical</th>
                    <th>Datetime</th>
                    <th>Potential ID</th>
                  </tr>
                </thead>
                <tbody>
                  {columns.map((column) => (
                    <tr key={column.name}>
                      <td>{column.name}</td>
                      <td>{column.dtype}</td>
                      <td>{formatInteger(column.null_count)}</td>
                      <td>{formatPercent(column.null_percentage)}</td>
                      <td>{formatInteger(column.unique_count)}</td>
                      <td>{formatPercent(column.unique_percentage)}</td>
                      <td>{column.is_numeric ? 'Yes' : 'No'}</td>
                      <td>{column.is_categorical ? 'Yes' : 'No'}</td>
                      <td>{column.is_datetime ? 'Yes' : 'No'}</td>
                      <td>{column.is_potential_id ? 'Yes' : 'No'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card title="Data quality" subtitle="Warnings generated by the backend">
          {warnings.length === 0 ? (
            <EmptyState title="No quality warnings" description="The backend did not flag any quality issues." />
          ) : (
            <div className="warning-list">
              {warnings.map((warning) => (
                <div
                  key={`${warning.type}-${warning.column ?? warning.message}`}
                  className={`warning warning--${severityTone(warning.severity)}`}
                >
                  <span className="warning__severity">{warning.severity}</span>
                  <p>{warning.message}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </section>

      <section className="detail-grid">
        <Card title="Correlation" subtitle={correlation?.message || 'Numeric relationships across columns'}>
          {correlationQuery.isLoading ? (
            <LoadingState label="Loading correlation..." />
          ) : correlationQuery.isError ? (
            <ErrorState
              title="Unable to load correlation"
              message="The correlation matrix could not be loaded."
              onRetry={() => void correlationQuery.refetch()}
            />
          ) : correlation ? (
            <CorrelationMatrix correlation={correlation} />
          ) : null}
        </Card>

        <Card title="Automated insights" subtitle="Rule-based findings from the backend">
          {insightsQuery.isLoading ? (
            <LoadingState label="Loading insights..." />
          ) : insights.length === 0 ? (
            <EmptyState title="No insights yet" description="Upload a richer dataset to surface automated insights." />
          ) : (
            <div className="insight-list">
              {insights.map((insight) => (
                <article key={`${insight.type}-${insight.message}`} className={`insight insight--${severityTone(insight.severity)}`}>
                  <div className="insight__header">
                    <span>{insight.type.replace(/_/g, ' ')}</span>
                    <span>{insight.severity}</span>
                  </div>
                  <p>{insight.message}</p>
                </article>
              ))}
            </div>
          )}
        </Card>
      </section>

      <section className="detail-grid">
        <Card title="Numeric statistics" subtitle="Select a numeric column for detailed measures">
          {!hasNumericData ? (
            <EmptyState title="No numeric columns" description="The backend did not identify numeric columns for this dataset." />
          ) : (
            <>
              <label className="field field--inline">
                <span>Numeric column</span>
                <select value={selectedNumeric} onChange={(event) => setSelectedNumericColumn(event.target.value)}>
                  {numericColumns.map((column) => (
                    <option key={column} value={column}>
                      {column}
                    </option>
                  ))}
                </select>
              </label>

              {selectedNumericStats ? (
                <div className="numeric-stats">
                  <div className="chart-shell chart-shell--compact">
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={chartSeries} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="label" tickLine={false} axisLine={false} />
                        <YAxis tickLine={false} axisLine={false} />
                        <Tooltip />
                        <Line type="monotone" dataKey="value" stroke={chartColor(0)} strokeWidth={3} dot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="stats-table">
                    <div><span>Count</span><strong>{formatInteger(selectedNumericStats.count)}</strong></div>
                    <div><span>Mean</span><strong>{formatNumber(selectedNumericStats.mean)}</strong></div>
                    <div><span>Median</span><strong>{formatNumber(selectedNumericStats.median)}</strong></div>
                    <div><span>Min</span><strong>{formatNumber(selectedNumericStats.min)}</strong></div>
                    <div><span>Max</span><strong>{formatNumber(selectedNumericStats.max)}</strong></div>
                    <div><span>Std. dev.</span><strong>{formatNumber(selectedNumericStats.standard_deviation)}</strong></div>
                    <div><span>Variance</span><strong>{formatNumber(selectedNumericStats.variance)}</strong></div>
                    <div><span>Q1</span><strong>{formatNumber(selectedNumericStats.percentile_25)}</strong></div>
                    <div><span>Q3</span><strong>{formatNumber(selectedNumericStats.percentile_75)}</strong></div>
                    <div><span>IQR</span><strong>{formatNumber(selectedNumericStats.iqr)}</strong></div>
                    <div><span>Outliers</span><strong>{formatInteger(selectedNumericStats.outlier_count)}</strong></div>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </Card>

        <Card title="Categorical statistics" subtitle="Top categories for each categorical column">
          {!hasCategoricalData ? (
            <EmptyState title="No categorical columns" description="The backend did not identify categorical columns for this dataset." />
          ) : (
            <>
              <label className="field field--inline">
                <span>Categorical column</span>
                <select value={selectedCategorical} onChange={(event) => setSelectedCategoricalColumn(event.target.value)}>
                  {categoricalColumns.map((column) => (
                    <option key={column} value={column}>
                      {column}
                    </option>
                  ))}
                </select>
              </label>

              {selectedCategoricalStats ? (
                <div className="categorical-section">
                  <div className="categorical-summary">
                    <StatCard label="Unique values" value={formatInteger(selectedCategoricalStats.unique_count)} />
                    <StatCard
                      label="Most common"
                      value={safeText(selectedCategoricalStats.most_common_value)}
                      hint={`${formatInteger(selectedCategoricalStats.most_common_count)} occurrences`}
                    />
                  </div>
                  <CategoryBarChart column={selectedCategorical} statistics={selectedCategoricalStats} />
                  <div className="top-values">
                    {selectedCategoricalStats.top_values.map((entry) => (
                      <div key={entry.value} className="top-values__item">
                        <span>{entry.value}</span>
                        <strong>{formatInteger(entry.count)}</strong>
                        <small>{formatPercent(entry.percentage)}</small>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </>
          )}
        </Card>
      </section>

      <section className="detail-grid">
        <Card title="Preview" subtitle="First 20 rows from the stored dataset">
          {previewQuery.isLoading ? (
            <LoadingState label="Loading preview..." />
          ) : previewQuery.isError ? (
            <ErrorState
              title="Unable to load preview"
              message="The dataset preview could not be loaded."
              onRetry={() => void previewQuery.refetch()}
            />
          ) : previewQuery.data ? (
            <div className="table-scroll">
              <table className="analysis-table analysis-table--preview">
                <thead>
                  <tr>
                    {previewQuery.data.columns.map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewQuery.data.preview.map((row, index) => (
                    <tr key={index}>
                      {previewQuery.data.columns.map((column) => (
                        <td key={`${index}-${column}`}>{safeText(row[column] as string | number | null | undefined)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </Card>
      </section>
    </div>
  )
}


