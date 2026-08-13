import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ExternalLink, Trash2 } from 'lucide-react'
import { useQueries } from '@tanstack/react-query'
import { Card } from '../components/common/Card'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { useDeleteDataset, useDatasets } from '../hooks/useDataset'
import { useActiveDataset } from '../context/ActiveDatasetContext'
import { getDatasetProfile } from '../services/analyticsApi'
import { formatBytes, formatDateTime, formatInteger, qualityTone } from '../utils/format'

export function DatasetListPage() {
  const datasetsQuery = useDatasets()
  const deleteMutation = useDeleteDataset()
  const datasets = datasetsQuery.data || []
  const { setActiveDatasetId } = useActiveDataset()

  const profileQueries = useQueries({
    queries: datasets.map((dataset) => ({
      queryKey: ['analytics', dataset.id, 'profile'],
      queryFn: () => getDatasetProfile(dataset.id),
      enabled: datasetsQuery.isSuccess,
      staleTime: 60_000,
    })),
  })

  const qualityByDatasetId = useMemo(() => {
    const entries = datasets.map((dataset, index) => [dataset.id, profileQueries[index]?.data?.quality_score] as const)
    return Object.fromEntries(entries) as Record<string, number | undefined>
  }, [datasets, profileQueries])

  if (datasetsQuery.isLoading) {
    return <LoadingState label="Loading datasets..." />
  }

  if (datasetsQuery.isError) {
    return (
      <ErrorState
        title="Unable to load datasets"
        message="The dataset list could not be loaded right now."
        onRetry={() => datasetsQuery.refetch()}
      />
    )
  }

  async function handleDelete(datasetId: string) {
    const confirmed = window.confirm('Delete this dataset? This cannot be undone.')
    if (!confirmed) {
      return
    }

    await deleteMutation.mutateAsync(datasetId)
  }

  return (
    <div className="datasets-page">
      <Card
        title="Datasets"
        subtitle="Browse uploaded CSV files, view analytics, or remove datasets you no longer need."
        actions={<Link to="/upload" className="button button--primary">Upload Dataset</Link>}
      >
        {datasets.length === 0 ? (
          <EmptyState
            title="No datasets yet"
            description="Upload your first CSV to begin analyzing your business data."
            action={
              <Link to="/upload" className="button button--primary">
                Upload Dataset
              </Link>
            }
          />
        ) : (
          <div className="table-scroll">
            <table className="dataset-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Original file</th>
                  <th>Rows</th>
                  <th>Columns</th>
                  <th>File size</th>
                  <th>Uploaded</th>
                  <th>Quality</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset, index) => {
                  const qualityScore = qualityByDatasetId[dataset.id]
                  const profileQuery = profileQueries[index]

                  return (
                    <tr key={dataset.id}>
                      <td>
                        <strong>{dataset.name}</strong>
                        <div className="table-subtext">{dataset.description || 'No description'}</div>
                      </td>
                      <td>{dataset.original_filename}</td>
                      <td>{formatInteger(dataset.total_rows)}</td>
                      <td>{formatInteger(dataset.total_columns)}</td>
                      <td>{formatBytes(dataset.file_size)}</td>
                      <td>{formatDateTime(dataset.uploaded_at)}</td>
                      <td>
                        {profileQuery?.isLoading ? (
                          'Loading...'
                        ) : typeof qualityScore === 'number' ? (
                          <span className={`quality-pill quality-pill--${qualityTone(qualityScore)}`}>
                            {qualityScore}
                          </span>
                        ) : (
                          'â€”'
                        )}
                      </td>
                      <td>
                        <div className="table-actions">
                          <Link to={`/datasets/${dataset.id}`} className="icon-button" onClick={() => setActiveDatasetId(dataset.id)} aria-label={`View ${dataset.name}`}>
                            <ExternalLink size={16} />
                          </Link>
                          <button
                            type="button"
                            className="icon-button icon-button--danger"
                            aria-label={`Delete ${dataset.name}`}
                            onClick={() => void handleDelete(dataset.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}


