import type { APIResponse } from './types'

const API_BASE = '/api'

// Response wrapper that includes data field
interface ApiResponseWithData<T> extends APIResponse {
  data?: T
}

class ApiError extends Error {
  constructor(
    message: string,
    public status?: number
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  }

  const response = await fetch(url, config)
  const result: ApiResponseWithData<T> = await response.json()

  if (!result.success) {
    throw new ApiError(result.error || 'Unknown error', response.status)
  }

  return result.data as T
}

// GET request helper
export async function get<T>(endpoint: string): Promise<T> {
  return request<T>(endpoint)
}

// POST request helper
export async function post<T>(
  endpoint: string,
  data?: unknown
): Promise<T> {
  return request<T>(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

// PUT request helper
export async function put<T>(
  endpoint: string,
  data: unknown
): Promise<T> {
  return request<T>(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

// DELETE request helper
export async function del<T>(
  endpoint: string,
  data?: unknown
): Promise<T> {
  return request<T>(endpoint, {
    method: 'DELETE',
    body: data ? JSON.stringify(data) : undefined,
  })
}

// POST file upload helper (multipart/form-data)
export async function postFile(
  endpoint: string,
  file: File,
  fieldName: string = 'file'
): Promise<{ message?: string }> {
  const url = `${API_BASE}${endpoint}`
  const formData = new FormData()
  formData.append(fieldName, file)

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    // Note: Don't set Content-Type header - browser sets it with boundary
  })

  const result: ApiResponseWithData<{ message?: string }> = await response.json()

  if (!result.success) {
    throw new ApiError(result.error || 'Upload failed', response.status)
  }

  return result.data || { message: result.message ?? undefined }
}

export { ApiError }
