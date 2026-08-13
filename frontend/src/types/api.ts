export interface ApiResponse<T> {
  status: string
  message: string
  data: T
}

export interface ApiErrorPayload {
  detail?: unknown
  message?: string
}

export class ApiError extends Error {
  readonly status: number

  readonly payload: unknown

  constructor(message: string, status: number, payload: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}