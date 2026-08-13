import axios, { AxiosError, type AxiosRequestConfig } from 'axios'
import { ApiError, type ApiErrorPayload } from '../types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    Accept: 'application/json',
  },
})

function getErrorMessage(payload: unknown): string {
  if (!payload) {
    return 'Unable to reach the analytics service.'
  }

  if (typeof payload === 'string') {
    return payload
  }

  if (Array.isArray(payload)) {
    const first = payload[0]
    if (first && typeof first === 'object' && 'msg' in first) {
      return String((first as { msg?: unknown }).msg || 'Request failed')
    }
    return 'Request failed.'
  }

  if (typeof payload === 'object') {
    const typedPayload = payload as ApiErrorPayload & Record<string, unknown>
    const detail = typedPayload.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (first && typeof first === 'object' && 'msg' in first) {
        return String((first as { msg?: unknown }).msg || 'Request failed')
      }
    }
    if (typeof typedPayload.message === 'string') {
      return typedPayload.message
    }
    if ('detail' in typedPayload) {
      return 'Request failed.'
    }
  }

  return 'Request failed.'
}

export function normalizeApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorPayload>
    const status = axiosError.response?.status || 0
    const payload = axiosError.response?.data
    return new ApiError(getErrorMessage(payload), status, payload)
  }

  if (error instanceof Error) {
    return new ApiError(error.message, 0, error)
  }

  return new ApiError('Request failed.', 0, error)
}

export async function requestJson<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.request<T>(config)
    return response.data
  } catch (error) {
    throw normalizeApiError(error)
  }
}

export async function uploadFormData<T>(
  config: AxiosRequestConfig<FormData>,
  onProgress?: (progress: number) => void,
): Promise<T> {
  try {
    const response = await apiClient.request<T>({
      ...config,
      headers: {
        Accept: 'application/json',
        ...(config.headers || {}),
      },
      onUploadProgress(event) {
        if (!event.total) {
          return
        }
        onProgress?.(Math.round((event.loaded * 100) / event.total))
      },
    })
    return response.data
  } catch (error) {
    throw normalizeApiError(error)
  }
}