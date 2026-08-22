import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

export const API_URL = 'http://localhost:8000'
export const admin = { id: 1, email: 'admin@example.com', role: 'admin', is_active: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' }
export const agent = { ...admin, id: 2, email: 'agent@example.com', role: 'agent' }
export const server = setupServer(
  http.get(`${API_URL}/auth/me`, () => HttpResponse.json(admin)),
  http.post(`${API_URL}/auth/login`, () => HttpResponse.json({ access_token: 'test-token', token_type: 'bearer' })),
  http.get(`${API_URL}/dashboard/overview`, () => HttpResponse.json({ total_service_requests: 1, total_customers: 1, unassigned_service_requests: 1, service_requests_by_status: { open: 1, in_progress: 0, resolved: 0, closed: 0 }, service_requests_by_priority: { low: 0, medium: 1, high: 0 }, service_requests_by_assignee: [] })),
  http.get(`${API_URL}/dashboard/my-work`, () => HttpResponse.json({ total_assigned_service_requests: 1, service_requests_by_status: { open: 1, in_progress: 0, resolved: 0, closed: 0 }, service_requests_by_priority: { low: 0, medium: 1, high: 0 } })),
  http.get(`${API_URL}/customers`, () => HttpResponse.json([{ id: 1, name: 'Acme Corp', email: 'ops@acme.test' }])),
  http.get(`${API_URL}/users`, () => HttpResponse.json([admin, agent])),
  http.get(`${API_URL}/service-requests`, () => HttpResponse.json([{ id: 1, title: 'Printer offline', description: 'Cannot connect', status: 'open', priority: 'medium', customer_id: 1, assigned_agent_id: null, assigned_agent_email: null, created_by_user_id: 1, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' }])),
)
