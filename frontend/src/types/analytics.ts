export interface ColumnProfile {
  name: string
  dtype: string
  null_count: number
  null_percentage: number
  unique_count: number
  unique_percentage: number
  is_numeric: boolean
  is_categorical: boolean
  is_datetime: boolean
  is_boolean: boolean
  is_constant: boolean
  is_potential_id: boolean
}

export interface DatasetProfile {
  total_rows: number
  total_columns: number
  file_size: number
  memory_usage: number
  missing_values: number
  missing_percentage: number
  duplicate_rows: number
  duplicate_percentage: number
  numeric_columns: number
  categorical_columns: number
  datetime_columns: number
  text_columns: number
  empty_columns: number
  constant_columns: number
  quality_score: number
  quality_label: string
}

export interface NumericStatistics {
  count: number
  sum: number | null
  mean: number | null
  median: number | null
  mode: number | null
  min: number | null
  max: number | null
  range: number | null
  variance: number | null
  standard_deviation: number | null
  percentile_25: number | null
  percentile_50: number | null
  percentile_75: number | null
  iqr: number | null
  outlier_count: number
}

export interface CategoricalValueCount {
  value: string
  count: number
  percentage: number
}

export interface CategoricalStatistics {
  unique_count: number
  most_common_value: string | null
  most_common_count: number
  top_values: CategoricalValueCount[]
}

export interface CorrelationResponse {
  columns: string[]
  matrix: Array<Array<number | null>>
  message: string | null
}

export interface QualityWarning {
  type: string
  severity: 'low' | 'medium' | 'high' | string
  column: string | null
  message: string
}

export interface BusinessKPIs {
  total_revenue: number | null
  average_revenue: number | null
  maximum_revenue: number | null
  minimum_revenue: number | null
  total_profit: number | null
  average_profit: number | null
  profit_margin: number | null
  total_quantity: number | null
  average_quantity: number | null
  average_price: number | null
}

export interface InsightItem {
  type: string
  severity: 'low' | 'medium' | 'high' | string
  message: string
  column: string | null
  metadata: Record<string, unknown>
}

export interface AnalyticsSummary {
  dataset_id: string
  dataset_name: string
  generated_at: string
  profile: DatasetProfile
  columns: ColumnProfile[]
  numeric_statistics: Record<string, NumericStatistics>
  categorical_statistics: Record<string, CategoricalStatistics>
  correlation: CorrelationResponse
  quality_warnings: QualityWarning[]
  kpis: BusinessKPIs
  insights: InsightItem[]
}