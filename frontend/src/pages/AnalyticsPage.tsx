import { Link } from 'react-router-dom'
import { Card } from '../components/common/Card'
import { CorrelationMatrix } from '../components/charts/CorrelationMatrix'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { QualityMeter } from '../components/common/QualityMeter'
import { StatCard } from '../components/common/StatCard'
import { useActiveDataset } from '../context/ActiveDatasetContext'
import { useDatasetAnalytics } from '../hooks/useAnalytics'
import { formatInteger, formatNumber } from '../utils/format'

export function AnalyticsPage() {
  const { activeDataset } = useActiveDataset()
  const query = useDatasetAnalytics(activeDataset?.id)
  if (!activeDataset) return <EmptyState title="Choose a dataset" description="Upload or select a dataset to view its analytics." action={<Link to="/upload" className="button button--primary">Upload Dataset</Link>} />
  if (query.isLoading) return <LoadingState label="Loading analytics..." />
  if (query.isError) return <ErrorState title="Unable to load analytics" message="The backend analytics request failed." onRetry={() => query.refetch()} />
  const analytics = query.data
  if (!analytics) return <EmptyState title="Analytics unavailable" description="No analytics were returned for this dataset." />
  const kpis = Object.entries(analytics.kpis).filter(([, value]) => value !== null)
  return <div className="dataset-page"><div className="page-titlebar"><div><span className="section-eyebrow">Analytics</span><h1>{activeDataset.name}</h1><p>Backend-generated profile, statistics, KPIs, and relationships.</p></div><Link to={`/datasets/${activeDataset.id}`} className="button button--secondary">Open dataset</Link></div><section className="metric-grid"><StatCard label="Rows" value={formatInteger(analytics.profile.total_rows)} /><StatCard label="Columns" value={formatInteger(analytics.profile.total_columns)} /><StatCard label="Missing values" value={formatInteger(analytics.profile.missing_values)} /><StatCard label="Quality score" value={formatInteger(analytics.profile.quality_score)} /></section><section className="detail-grid"><Card title="Dataset profile" subtitle="Completeness and column composition"><QualityMeter score={analytics.profile.quality_score} label={analytics.profile.quality_label} /><div className="profile-grid"><div><span>Numeric columns</span><strong>{formatInteger(analytics.profile.numeric_columns)}</strong></div><div><span>Categorical columns</span><strong>{formatInteger(analytics.profile.categorical_columns)}</strong></div><div><span>Duplicate rows</span><strong>{formatInteger(analytics.profile.duplicate_rows)}</strong></div><div><span>Quality label</span><strong>{analytics.profile.quality_label}</strong></div></div></Card><Card title="Business KPIs" subtitle="Inferred by the backend">{kpis.length ? <div className="kpi-grid">{kpis.map(([key, value]) => <StatCard key={key} label={key.replace(/_/g, ' ')} value={formatNumber(value as number)} />)}</div> : <EmptyState title="No KPIs available" description="No matching business measures were found." />}</Card></section><section className="detail-grid"><Card title="Correlation" subtitle={analytics.correlation.message || 'Numeric relationships'}><CorrelationMatrix correlation={analytics.correlation} /></Card><Card title="Column statistics" subtitle="Numeric and categorical fields">{analytics.columns.length ? <div className="profile-grid">{analytics.columns.map((column) => <div key={column.name}><span>{column.name}</span><strong>{column.dtype}</strong><small>{column.unique_count} unique · {column.null_count} nulls</small></div>)}</div> : <EmptyState title="No columns found" description="No column profile was returned." />}</Card></section></div>
}

