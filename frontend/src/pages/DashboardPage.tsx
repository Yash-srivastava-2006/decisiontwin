import { Link } from 'react-router-dom'
import { ArrowRight, Upload } from 'lucide-react'
import { Card } from '../components/common/Card'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { QualityMeter } from '../components/common/QualityMeter'
import { StatCard } from '../components/common/StatCard'
import { useDatasets } from '../hooks/useDataset'
import { useActiveDataset } from '../context/ActiveDatasetContext'
import { useDatasetAnalytics } from '../hooks/useAnalytics'
import { formatBytes, formatDateTime, formatInteger, safeText } from '../utils/format'

export function DashboardPage() {
  const datasetsQuery = useDatasets()
  const datasets = datasetsQuery.data || []
  const { activeDataset } = useActiveDataset()
  const latestDataset = activeDataset
  const analyticsQuery = useDatasetAnalytics(latestDataset?.id)
  const latestAnalytics = analyticsQuery.data

  if (datasetsQuery.isLoading) {
    return <LoadingState label="Loading datasets..." />
  }

  if (datasetsQuery.isError) {
    return (
      <ErrorState
        title="Unable to load datasets"
        message="Please try again. The backend may be unavailable."
        onRetry={() => datasetsQuery.refetch()}
      />
    )
  }

  const totalRows = datasets.reduce((sum, dataset) => sum + dataset.total_rows, 0)
  const totalColumns = datasets.reduce((sum, dataset) => sum + dataset.total_columns, 0)
  const averageColumns = datasets.length ? totalColumns / datasets.length : 0

  return (
    <div className="dashboard-page">
      <section className="hero-panel">
        <div className="hero-panel__copy">
          <span className="section-eyebrow">Decision intelligence dashboard</span>
          <h1>Analyze your data. Discover patterns. Make better decisions.</h1>
          <p>
            DecisionTwin AI turns uploaded CSV files into structured analytics, business KPIs, and automated insights.
          </p>
          <div className="hero-panel__actions">
            <Link to="/upload" className="button button--primary">
              <Upload size={16} />
              Upload Dataset
            </Link>
            <Link to="/datasets" className="button button--secondary">
              View datasets
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>

        <div className="hero-panel__summary">
          <StatCard label="Datasets" value={formatInteger(datasets.length)} hint="Uploaded CSV files" />
          <StatCard label="Rows" value={formatInteger(totalRows)} hint="Across all datasets" />
          <StatCard label="Columns" value={formatInteger(averageColumns)} hint="Average columns per dataset" />
          <StatCard
            label="Latest quality"
            value={latestDataset && latestAnalytics ? `${latestAnalytics.profile.quality_score}` : 'â€”'}
            hint={latestDataset && latestAnalytics ? latestAnalytics.profile.quality_label : 'Upload a dataset'}
          />
        </div>
      </section>

      <section className="dashboard-grid">
        <Card title="Quick analytics summary" subtitle={latestDataset ? latestDataset.name : 'No dataset selected'}>
          {!latestDataset ? (
            <EmptyState
              title="No datasets yet"
              description="Upload your first CSV to begin analyzing your business data."
              action={
                <Link to="/upload" className="button button--primary">
                  Upload Dataset
                </Link>
              }
            />
          ) : analyticsQuery.isLoading ? (
            <LoadingState label="Loading analytics..." />
          ) : analyticsQuery.isError ? (
            <ErrorState
              title="Unable to load analytics"
              message="The latest dataset analytics could not be loaded right now."
              onRetry={() => analyticsQuery.refetch()}
            />
          ) : latestAnalytics ? (
            <>
              <div className="metric-row">
                <StatCard label="Rows" value={formatInteger(latestAnalytics.profile.total_rows)} />
                <StatCard label="Columns" value={formatInteger(latestAnalytics.profile.total_columns)} />
                <StatCard label="Missing values" value={formatInteger(latestAnalytics.profile.missing_values)} />
                <StatCard label="Quality score" value={formatInteger(latestAnalytics.profile.quality_score)} />
              </div>
              <QualityMeter
                score={latestAnalytics.profile.quality_score}
                label={latestAnalytics.profile.quality_label}
              />
              <div className="summary-meta">
                <span>Uploaded {formatDateTime(latestDataset.uploaded_at)}</span>
                <span>{formatBytes(latestDataset.file_size)}</span>
              </div>
            </>
          ) : (
            <EmptyState title="Analytics unavailable" description="The latest dataset analytics could not be loaded." />
          )}
        </Card>

        <Card title="Recent datasets" subtitle="Most recently uploaded files">
          {datasets.length === 0 ? (
            <EmptyState
              title="No datasets yet"
              description="Upload your first CSV to see analytics here."
              action={
                <Link to="/upload" className="button button--primary">
                  Upload Dataset
                </Link>
              }
            />
          ) : (
            <div className="recent-list">
              {datasets.slice(0, 5).map((dataset) => (
                <Link key={dataset.id} to={`/datasets/${dataset.id}`} className="recent-list__item">
                  <div>
                    <strong>{dataset.name}</strong>
                    <span>{safeText(dataset.original_filename)}</span>
                  </div>
                  <div>
                    <span>{formatInteger(dataset.total_rows)} rows</span>
                    <span>{formatDateTime(dataset.uploaded_at)}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </section>
    </div>
  )
}


