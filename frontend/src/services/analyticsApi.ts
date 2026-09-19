import { requestJson } from './api'
import type {
  AnalyticsSummary,
  BusinessKPIs,
  CategoricalStatistics,
  ColumnProfile,
  CorrelationResponse,
  DatasetProfile,
  InsightItem,
  NumericStatistics,
  QualityWarning,
} from '../types/analytics'
import type { ApiResponse } from '../types/api'

async function unwrapResponse<T>(request: Promise<ApiResponse<T>>): Promise<T> {
  const response = await request
  return response.data
}

export function getDatasetProfile(datasetId: string): Promise<DatasetProfile> {
  return unwrapResponse(
    requestJson<ApiResponse<DatasetProfile>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/profile`,
    }),
  )
}

export function getDatasetColumns(datasetId: string): Promise<ColumnProfile[]> {
  return unwrapResponse(
    requestJson<ApiResponse<ColumnProfile[]>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/columns`,
    }),
  )
}

export function getNumericStatistics(datasetId: string): Promise<Record<string, NumericStatistics>> {
  return unwrapResponse(
    requestJson<ApiResponse<Record<string, NumericStatistics>>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/statistics/numeric`,
    }),
  )
}

export function getCategoricalStatistics(datasetId: string): Promise<Record<string, CategoricalStatistics>> {
  return unwrapResponse(
    requestJson<ApiResponse<Record<string, CategoricalStatistics>>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/statistics/categorical`,
    }),
  )
}

export function getCorrelation(datasetId: string): Promise<CorrelationResponse> {
  return unwrapResponse(
    requestJson<ApiResponse<CorrelationResponse>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/correlation`,
    }),
  )
}

export function getQualityWarnings(datasetId: string): Promise<QualityWarning[]> {
  return unwrapResponse(
    requestJson<ApiResponse<QualityWarning[]>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/quality-warnings`,
    }),
  )
}

export function getKpis(datasetId: string): Promise<BusinessKPIs> {
  return unwrapResponse(
    requestJson<ApiResponse<BusinessKPIs>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/kpis`,
    }),
  )
}

export function getInsights(datasetId: string): Promise<InsightItem[]> {
  return unwrapResponse(
    requestJson<ApiResponse<InsightItem[]>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/insights`,
    }),
  )
}

export function getDatasetAnalytics(datasetId: string): Promise<AnalyticsSummary> {
  return unwrapResponse(
    requestJson<ApiResponse<AnalyticsSummary>>({
      method: 'GET',
      url: `/api/v1/datasets/${datasetId}/analytics`,
    }),
  )
}
export function getDistributions(id:string){return unwrapResponse(requestJson<ApiResponse<import('../types/analytics').DistributionAnalysis[]>>({method:'GET',url:`/api/v1/datasets/${id}/distributions`}))}
export function getOutliers(id:string){return unwrapResponse(requestJson<ApiResponse<import('../types/analytics').OutlierAnalysis[]>>({method:'GET',url:`/api/v1/datasets/${id}/outliers`}))}
export function getCategoryPerformance(id:string,category?:string,metric?:string){return unwrapResponse(requestJson<ApiResponse<import('../types/analytics').CategoryPerformanceResponse>>({method:'GET',url:`/api/v1/datasets/${id}/category-performance`,params:{category_column:category,metric_column:metric}}))}
export function getTrends(id:string,granularity:string){return unwrapResponse(requestJson<ApiResponse<import('../types/analytics').TrendResponse>>({method:'GET',url:`/api/v1/datasets/${id}/trends`,params:{granularity}}))}
export function getRankings(id:string,direction:string,topN:number){return unwrapResponse(requestJson<ApiResponse<import('../types/analytics').RankingResponse>>({method:'GET',url:`/api/v1/datasets/${id}/rankings`,params:{direction,top_n:topN}}))}
export function getCorrelationPairs(id:string){return unwrapResponse(requestJson<ApiResponse<import('../types/analytics').CorrelationPair[]>>({method:'GET',url:`/api/v1/datasets/${id}/correlation-pairs`}))}
