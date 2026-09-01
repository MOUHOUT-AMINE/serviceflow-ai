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

describe('AI ticket suggestions', () => {
  it('shows loading and renders suggestions for review', async () => {
    sessionStorage.setItem('serviceflow_access_token', 'admin-token')
    let release: (() => void) | undefined
    server.use(http.post(`${API_URL}/service-requests/1/ai-suggestions`, async () => {
      await new Promise<void>((resolve) => { release = resolve })
      return HttpResponse.json({ summary: 'The printer is unreachable.', suggested_priority: 'high', recommended_action: 'Check power and network connectivity.' })
    }))
    renderApp(<TestRoutes />, '/service-requests')
    await userEvent.click(await screen.findByRole('button', { name: 'Printer offline' }))
    await userEvent.click(screen.getByRole('button', { name: 'Generate suggestions' }))
    expect(screen.getByRole('button', { name: 'Generating…' })).toBeDisabled()
    release?.()
    expect(await screen.findByText('The printer is unreachable.')).toBeVisible()
    expect(screen.getByText('Check power and network connectivity.')).toBeVisible()
    expect(screen.getByText('AI-generated · Review before applying')).toBeVisible()
    expect(within(screen.getByRole('dialog')).getByText('High')).toBeVisible()
  })

  it('shows a small fallback when AI is unavailable', async () => {
    sessionStorage.setItem('serviceflow_access_token', 'admin-token')
    server.use(http.post(`${API_URL}/service-requests/1/ai-suggestions`, () => HttpResponse.json({ detail: 'AI suggestions are temporarily unavailable' }, { status: 503 })))
    renderApp(<TestRoutes />, '/service-requests')
    await userEvent.click(await screen.findByRole('button', { name: 'Printer offline' }))
    await userEvent.click(screen.getByRole('button', { name: 'Generate suggestions' }))
    expect(await screen.findByText('AI suggestions are unavailable right now.')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Done' })).toBeEnabled()
  })

  it('clears previous suggestions when regeneration fails', async () => {
    sessionStorage.setItem('serviceflow_access_token', 'admin-token')
    let requestCount = 0
    let releaseRetry: (() => void) | undefined
    server.use(http.post(`${API_URL}/service-requests/1/ai-suggestions`, async () => {
      requestCount += 1
      if (requestCount === 1) {
        return HttpResponse.json({ summary: 'Old generated summary', suggested_priority: 'high', recommended_action: 'Old recommended action' })
      }
      await new Promise<void>((resolve) => { releaseRetry = resolve })
      return HttpResponse.json({ detail: 'AI suggestions are temporarily unavailable' }, { status: 503 })
    }))
    renderApp(<TestRoutes />, '/service-requests')
    await userEvent.click(await screen.findByRole('button', { name: 'Printer offline' }))
    await userEvent.click(screen.getByRole('button', { name: 'Generate suggestions' }))
    expect(await screen.findByText('Old generated summary')).toBeVisible()

    await userEvent.click(screen.getByRole('button', { name: 'Generate suggestions' }))
    expect(screen.queryByText('Old generated summary')).not.toBeInTheDocument()
    expect(screen.queryByText('Old recommended action')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Generating/ })).toBeDisabled()

    releaseRetry?.()
    expect(await screen.findByText('AI suggestions are unavailable right now.')).toBeVisible()
    expect(screen.queryByText('Old generated summary')).not.toBeInTheDocument()
    expect(screen.queryByText('Old recommended action')).not.toBeInTheDocument()
  })

  it('does not automatically update ticket priority', async () => {
    sessionStorage.setItem('serviceflow_access_token', 'admin-token')
    const patchSpy = vi.fn()
    server.use(
      http.post(`${API_URL}/service-requests/1/ai-suggestions`, () => HttpResponse.json({ summary: 'Generated summary', suggested_priority: 'high', recommended_action: 'Action' })),
      http.patch(`${API_URL}/service-requests/1`, () => { patchSpy(); return HttpResponse.json({}) }),
    )
    renderApp(<TestRoutes />, '/service-requests')
    await userEvent.click(await screen.findByRole('button', { name: 'Printer offline' }))
    await userEvent.click(screen.getByRole('button', { name: 'Generate suggestions' }))
    expect(await screen.findByText('Generated summary')).toBeVisible()
    expect(patchSpy).not.toHaveBeenCalled()
  })

  it('ignores a completed suggestion request after switching tickets', async () => {
    sessionStorage.setItem('serviceflow_access_token', 'admin-token')
    let releaseFirst: (() => void) | undefined
    server.use(
      http.get(`${API_URL}/service-requests`, () => HttpResponse.json([
        { id: 1, title: 'Printer offline', description: 'Cannot connect', status: 'open', priority: 'medium', customer_id: 1, assigned_agent_id: null, assigned_agent_email: null, created_by_user_id: 1, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
        { id: 2, title: 'VPN unavailable', description: 'Cannot sign in', status: 'open', priority: 'high', customer_id: 1, assigned_agent_id: null, assigned_agent_email: null, created_by_user_id: 1, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
      ])),
      http.post(`${API_URL}/service-requests/1/ai-suggestions`, async () => {
        await new Promise<void>((resolve) => { releaseFirst = resolve })
        return HttpResponse.json({ summary: 'Printer-only result', suggested_priority: 'low', recommended_action: 'Restart printer' })
      }),
    )
    renderApp(<TestRoutes />, '/service-requests')
    await userEvent.click(await screen.findByRole('button', { name: 'Printer offline' }))
    await userEvent.click(screen.getByRole('button', { name: 'Generate suggestions' }))
    await userEvent.click(screen.getByRole('button', { name: 'Done' }))
    await userEvent.click(screen.getByRole('button', { name: 'VPN unavailable' }))

    releaseFirst?.()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Generate suggestions' })).toBeEnabled())
    expect(screen.getByRole('heading', { name: 'VPN unavailable' })).toBeVisible()
    expect(screen.queryByText('Printer-only result')).not.toBeInTheDocument()
  })
})
