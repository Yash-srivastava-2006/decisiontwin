import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  deleteDataset,
  getDataset,
  getDatasetPreview,
  listDatasets,
  uploadDataset,
} from '../services/datasetApi'
import type { DatasetUploadInput } from '../types/dataset'

const datasetKeys = {
  all: ['datasets'] as const,
  list: () => [...datasetKeys.all, 'list'] as const,
  detail: (datasetId: string) => [...datasetKeys.all, datasetId] as const,
  preview: (datasetId: string) => [...datasetKeys.detail(datasetId), 'preview'] as const,
}

export function useDatasets() {
  return useQuery({
    queryKey: datasetKeys.list(),
    queryFn: listDatasets,
  })
}

export function useDataset(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? datasetKeys.detail(datasetId) : datasetKeys.detail('missing'),
    queryFn: () => getDataset(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useDatasetPreview(datasetId?: string) {
  return useQuery({
    queryKey: datasetId ? datasetKeys.preview(datasetId) : datasetKeys.preview('missing'),
    queryFn: () => getDatasetPreview(datasetId || ''),
    enabled: Boolean(datasetId),
  })
}

export function useUploadDataset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ input, onProgress }: { input: DatasetUploadInput; onProgress?: (progress: number) => void }) =>
      uploadDataset(input, onProgress),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: datasetKeys.all })
    },
  })
}

export function useDeleteDataset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (datasetId: string) => deleteDataset(datasetId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: datasetKeys.all })
    },
  })
}