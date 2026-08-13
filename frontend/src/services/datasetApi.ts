import { requestJson, uploadFormData } from './api'
import type {
  DatasetDetailResponse,
  DatasetListItem,
  DatasetPreviewResponse,
  DatasetUploadInput,
  DatasetUploadResponse,
} from '../types/dataset'

export function listDatasets(): Promise<DatasetListItem[]> {
  return requestJson<DatasetListItem[]>({
    method: 'GET',
    url: '/api/v1/datasets',
  })
}

export function getDataset(datasetId: string): Promise<DatasetDetailResponse> {
  return requestJson<DatasetDetailResponse>({
    method: 'GET',
    url: `/api/v1/datasets/${datasetId}`,
  })
}

export function getDatasetPreview(datasetId: string): Promise<DatasetPreviewResponse> {
  return requestJson<DatasetPreviewResponse>({
    method: 'GET',
    url: `/api/v1/datasets/${datasetId}/preview`,
  })
}

export function deleteDataset(datasetId: string): Promise<void> {
  return requestJson<void>({
    method: 'DELETE',
    url: `/api/v1/datasets/${datasetId}`,
  })
}

export function uploadDataset(
  input: DatasetUploadInput,
  onProgress?: (progress: number) => void,
): Promise<DatasetUploadResponse> {
  const formData = new FormData()
  formData.append('file', input.file)
  formData.append('name', input.name)
  if (input.description) {
    formData.append('description', input.description)
  }

  return uploadFormData<DatasetUploadResponse>(
    {
      method: 'POST',
      url: '/api/v1/datasets/upload',
      data: formData,
    },
    onProgress,
  )
}