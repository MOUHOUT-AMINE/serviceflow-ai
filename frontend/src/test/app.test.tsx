import { HttpResponse, http } from 'msw'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Navigate, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { ProtectedRoute } from '../auth/ProtectedRoute'
import { RoleRoute } from '../auth/RoleRoute'
import { LoginPage } from '../pages/LoginPage'
import { DashboardPage } from '../pages/DashboardPage'
import { ServiceRequestsPage } from '../pages/ServiceRequestsPage'
import { UsersPage } from '../pages/UsersPage'
import { API_URL, agent, server } from './server'
import { renderApp } from './render'

function TestRoutes() {
  return <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<ProtectedRoute />}><Route element={<AppLayout />}>
      <Route index element={<Navigate to="/dashboard" />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/service-requests" element={<ServiceRequestsPage />} />
      <Route element={<RoleRoute allow={['admin']} />}><Route path="/users" element={<UsersPage />} /></Route>
    </Route></Route>
  </Routes>
}

describe('authentication and routing', () => {
  it('validates the login form before requesting the API', async () => {
    const loginSpy = vi.fn()
    server.use(http.post(`${API_URL}/auth/login`, () => { loginSpy(); return HttpResponse.json({ access_token: 'x' }) }))
    renderApp(<TestRoutes />, '/login')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Enter a valid email address')).toBeVisible()
    expect(screen.getByText('Password must be at least 8 characters')).toBeVisible()
    expect(loginSpy).not.toHaveBeenCalled()
  })

  it('redirects protected pages to login without a token', async () => {
    renderApp(<TestRoutes />, '/dashboard')
    expect(await screen.findByRole('heading', { name: 'Sign in to your workspace' })).toBeVisible()
  })

  it('normalizes authorization API errors', async () => {
    server.use(http.get(`${API_URL}/forbidden`, () => HttpResponse.json({ detail: 'Insufficient permissions' }, { status: 403 })))
    await expect(api.get('/forbidden')).rejects.toMatchObject({ status: 403, message: 'Insufficient permissions' })
  })
})

describe('role workflows', () => {
  it('prevents an administrator from changing their own role', async () => {
    sessionStorage.setItem('serviceflow_access_token', 'admin-token')
    renderApp(<TestRoutes />, '/users')

    const currentUserRole = await screen.findByLabelText('Role for admin@example.com')
    expect(currentUserRole).toBeDisabled()
    const currentUserRow = currentUserRole.closest('tr')
    expect(within(currentUserRow!).getByRole('button', { name: 'Deactivate' })).toBeDisabled()
    const agentRole = screen.getByLabelText('Role for agent@example.com')
    expect(agentRole).toBeEnabled()
    const agentRow = agentRole.closest('tr')
    expect(within(agentRow!).getByRole('button', { name: 'Deactivate' })).toBeEnabled()
  })

  it('shows admin navigation and assigns a request', async () => {
    sessionStorage.setItem('serviceflow_access_token', 'admin-token')
    let assigned: unknown
    server.use(http.patch(`${API_URL}/service-requests/1/assignment`, async ({ request }) => { assigned = await request.json(); return HttpResponse.json({ id: 1, title: 'Printer offline', description: 'Cannot connect', status: 'open', priority: 'medium', customer_id: 1, assigned_agent_id: 2, created_by_user_id: 1, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' }) }))
    renderApp(<TestRoutes />, '/service-requests')
    expect(await screen.findByRole('link', { name: /Users/ })).toBeVisible()
    await userEvent.click(await screen.findByRole('button', { name: 'Printer offline' }))
    await userEvent.selectOptions(screen.getByLabelText('Assign active agent'), '2')
    await waitFor(() => expect(assigned).toEqual({ assigned_agent_id: 2 }))
  })

  it('hides admin controls and lets an agent update request status', async () => {
    sessionStorage.setItem('serviceflow_access_token', 'agent-token')
    server.use(http.get(`${API_URL}/auth/me`, () => HttpResponse.json(agent)))
    const usersSpy = vi.fn()
    server.use(
      http.get(`${API_URL}/users`, () => { usersSpy(); return HttpResponse.json([]) }),
      http.get(`${API_URL}/service-requests`, () => HttpResponse.json([{ id: 1, title: 'Printer offline', description: 'Cannot connect', status: 'open', priority: 'medium', customer_id: 1, assigned_agent_id: 2, assigned_agent_email: 'agent@example.com', created_by_user_id: 1, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' }])),
    )
    let updated: unknown
    server.use(http.patch(`${API_URL}/service-requests/1`, async ({ request }) => { updated = await request.json(); return HttpResponse.json({ id: 1 }) }))
    renderApp(<TestRoutes />, '/service-requests')
    expect(await screen.findByText('Service requests')).toBeVisible()
    expect(screen.queryByRole('link', { name: /Users/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument()
    expect(screen.getByText('agent@example.com')).toBeVisible()
    expect(usersSpy).not.toHaveBeenCalled()
    await userEvent.click(await screen.findByRole('button', { name: 'Edit' }))
    const dialog = screen.getByRole('dialog')
    await userEvent.selectOptions(within(dialog).getByLabelText('Status'), 'resolved')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Save request' }))
    await waitFor(() => expect(updated).toMatchObject({ status: 'resolved' }))
  })
})
