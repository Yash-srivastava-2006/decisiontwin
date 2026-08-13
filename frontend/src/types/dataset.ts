export interface DatasetBase {
  id: string
  name: string
  original_filename: string
  description: string | null
  file_type: string
  file_size: number
  total_rows: number
  total_columns: number
  file_path: string
  uploaded_at: string
  updated_at: string
}

export interface DatasetUploadResponse extends DatasetBase {
  columns: string[]
  dtypes: Record<string, string>
  missing_values: Record<string, number>
}

export interface DatasetListItem extends DatasetBase {}

export interface DatasetDetailResponse extends DatasetUploadResponse {}

export interface DatasetPreviewResponse {
  columns: string[]
  dtypes: Record<string, string>
  preview: Array<Record<string, unknown>>
  summary: {
    rows: number
    columns: number
  }
}

export interface DatasetUploadInput {
  name: string
  description?: string
  file: File
}