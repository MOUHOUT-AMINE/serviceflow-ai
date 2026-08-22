import type { ApiValidationIssue } from '../types/api'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
const TOKEN_KEY = 'serviceflow_access_token'

export class ApiError extends Error {
  constructor(public status: number, message: string, public issues: ApiValidationIssue[] = []) {
    super(message)
    this.name = 'ApiError'
  }
}

export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
}

let unauthorizedHandler: (() => void) | undefined
export const setUnauthorizedHandler = (handler?: () => void) => { unauthorizedHandler = handler }

async function readError(response: Response): Promise<ApiError> {
  let body: { detail?: string | ApiValidationIssue[] } = {}
  try { body = await response.json() as typeof body } catch { /* non-JSON response */ }
  const issues = Array.isArray(body.detail) ? body.detail : []
  const message = typeof body.detail === 'string'
    ? body.detail
    : issues[0]?.msg || (response.status === 403 ? 'You do not have permission to perform this action.' : 'Something went wrong. Please try again.')
  return new ApiError(response.status, message, issues)
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (!(options.body instanceof URLSearchParams) && options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const error = await readError(response)
    if (response.status === 401) {
      tokenStore.clear()
      unauthorizedHandler?.()
    }
    throw error
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => apiRequest<T>(path),
  post: <T>(path: string, data: unknown) => apiRequest<T>(path, { method: 'POST', body: JSON.stringify(data) }),
  patch: <T>(path: string, data: unknown) => apiRequest<T>(path, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (path: string) => apiRequest<void>(path, { method: 'DELETE' }),
}
