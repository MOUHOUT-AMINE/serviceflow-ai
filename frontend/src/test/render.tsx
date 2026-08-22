import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { ReactElement } from 'react'
import { AuthProvider } from '../auth/AuthProvider'

export function renderApp(ui: ReactElement, route = '/') {
  window.history.pushState({}, '', route)
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[route]}><AuthProvider>{ui}</AuthProvider></MemoryRouter></QueryClientProvider>)
}
