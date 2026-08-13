import { useQuery } from '@tanstack/react-query'
import {
  getCategoricalStatistics,
  getCorrelation,
  getDatasetAnalytics,
  getDatasetColumns,
  getDatasetProfile,
  getInsights,
  getKpis,
  getNumericStatistics,
  getQualityWarnings,
} from '../services/analyticsApi'

const analyticsKeys = {
  all: ['analytics'] as const,
  dataset: (datasetId: string) => [...analyticsKeys.all, datasetId] as const,
  profile: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'profile'] as const,
  columns: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'columns'] as const,
  numeric: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'numeric'] as const,
  categorical: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'categorical'] as const,
  correlation: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'correlation'] as const,
  warnings: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'warnings'] as const,
  kpis: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'kpis'] as const,
  insights: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'insights'] as const,
  summary: (datasetId: string) => [...analyticsKeys.dataset(datasetId), 'summary'] as const,
}

export function useDatasetProfile(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.profile(datasetId) : analyticsKeys.profile('missing'),
    queryFn: () => getDatasetProfile(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useDatasetColumns(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.columns(datasetId) : analyticsKeys.columns('missing'),
    queryFn: () => getDatasetColumns(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useNumericStatistics(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.numeric(datasetId) : analyticsKeys.numeric('missing'),
    queryFn: () => getNumericStatistics(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useCategoricalStatistics(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.categorical(datasetId) : analyticsKeys.categorical('missing'),
    queryFn: () => getCategoricalStatistics(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useCorrelation(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.correlation(datasetId) : analyticsKeys.correlation('missing'),
    queryFn: () => getCorrelation(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useQualityWarnings(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.warnings(datasetId) : analyticsKeys.warnings('missing'),
    queryFn: () => getQualityWarnings(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useKpis(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.kpis(datasetId) : analyticsKeys.kpis('missing'),
    queryFn: () => getKpis(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useInsights(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.insights(datasetId) : analyticsKeys.insights('missing'),
    queryFn: () => getInsights(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useDatasetAnalytics(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? analyticsKeys.summary(datasetId) : analyticsKeys.summary('missing'),
    queryFn: () => getDatasetAnalytics(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}