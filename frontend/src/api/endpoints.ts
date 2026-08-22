import { api, apiRequest } from './client'
import type { AgentWorkSummary, Customer, DashboardOverview, RequestPriority, RequestStatus, ServiceRequest, User, UserRole } from '../types/api'

export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password })
  return apiRequest<{ access_token: string; token_type: string }>('/auth/login', { method: 'POST', body })
}
export const getMe = () => api.get<User>('/auth/me')
export const getDashboard = async (role: UserRole): Promise<DashboardOverview | AgentWorkSummary> => role === 'admin' ? api.get<DashboardOverview>('/dashboard/overview') : api.get<AgentWorkSummary>('/dashboard/my-work')

export const customersApi = {
  list: () => api.get<Customer[]>('/customers'),
  create: (data: Omit<Customer, 'id'>) => api.post<Customer>('/customers', data),
  update: (id: number, data: Partial<Omit<Customer, 'id'>>) => api.patch<Customer>(`/customers/${id}`, data),
  remove: (id: number) => api.delete(`/customers/${id}`),
}

export interface RequestInput { title: string; description: string; customer_id: number; status: RequestStatus; priority: RequestPriority }
export interface RequestFilters { customer_id?: number; assigned_agent_id?: number; status?: RequestStatus; priority?: RequestPriority }
export const requestsApi = {
  list: (filters: RequestFilters = {}) => {
    const query = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => { if (value !== undefined && value !== '') query.set(key, String(value)) })
    return api.get<ServiceRequest[]>(`/service-requests${query.size ? `?${query}` : ''}`)
  },
  create: (data: RequestInput) => api.post<ServiceRequest>('/service-requests', data),
  update: (id: number, data: Partial<Omit<RequestInput, 'customer_id'>>) => api.patch<ServiceRequest>(`/service-requests/${id}`, data),
  assign: (id: number, assigned_agent_id: number | null) => api.patch<ServiceRequest>(`/service-requests/${id}/assignment`, { assigned_agent_id }),
  remove: (id: number) => api.delete(`/service-requests/${id}`),
}

export const usersApi = {
  list: () => api.get<User[]>('/users'),
  create: (data: { email: string; password: string; role: UserRole }) => api.post<User>('/users', data),
  update: (id: number, data: { role?: UserRole; is_active?: boolean }) => api.patch<User>(`/users/${id}`, data),
}
