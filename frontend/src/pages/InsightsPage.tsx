import { Link } from 'react-router-dom'
import { Card } from '../components/common/Card'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { useActiveDataset } from '../context/ActiveDatasetContext'
import { useInsights, useQualityWarnings } from '../hooks/useAnalytics'
import { severityTone } from '../utils/format'

export function InsightsPage() {
  const { activeDataset } = useActiveDataset()
  const insightsQuery = useInsights(activeDataset?.id)
  const warningsQuery = useQualityWarnings(activeDataset?.id)
  if (!activeDataset) return <EmptyState title="Choose a dataset" description="Upload or select a dataset to see automated findings." action={<Link to="/upload" className="button button--primary">Upload Dataset</Link>} />
  if (insightsQuery.isLoading || warningsQuery.isLoading) return <LoadingState label="Loading insights..." />
  if (insightsQuery.isError || warningsQuery.isError) return <ErrorState title="Unable to load insights" message="The backend findings could not be loaded." onRetry={() => { void insightsQuery.refetch(); void warningsQuery.refetch() }} />
  const insights = insightsQuery.data || []; const warnings = warningsQuery.data || []
  return <div className="dataset-page"><div className="page-titlebar"><div><span className="section-eyebrow">Insights</span><h1>{activeDataset.name}</h1><p>Automated observations and data-quality findings from the backend.</p></div></div><section className="detail-grid"><Card title="Automated insights" subtitle="Findings generated from your data">{insights.length ? <div className="insight-list">{insights.map((item) => <article key={`${item.type}-${item.message}`} className={`insight insight--${severityTone(item.severity)}`}><div className="insight__header"><span>{item.type.replace(/_/g, ' ')}</span><span>{item.severity}</span></div><p>{item.message}</p></article>)}</div> : <EmptyState title="No insights yet" description="The backend did not return automated observations." />}</Card><Card title="Quality warnings" subtitle="Items that may need attention">{warnings.length ? <div className="warning-list">{warnings.map((warning) => <div key={`${warning.type}-${warning.message}`} className={`warning warning--${severityTone(warning.severity)}`}><span className="warning__severity">{warning.severity}</span><p>{warning.message}</p></div>)}</div> : <EmptyState title="No quality warnings" description="The backend did not flag any quality issues." />}</Card></section></div>
}

