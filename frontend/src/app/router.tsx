import { createBrowserRouter, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '../auth/ProtectedRoute'
import { RoleRoute } from '../auth/RoleRoute'
import { AppLayout } from '../components/layout/AppLayout'
import { CustomersPage } from '../pages/CustomersPage'
import { DashboardPage } from '../pages/DashboardPage'
import { LoginPage } from '../pages/LoginPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { ServiceRequestsPage } from '../pages/ServiceRequestsPage'
import { UsersPage } from '../pages/UsersPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { element: <ProtectedRoute />, children: [{ element: <AppLayout />, children: [
    { index: true, element: <Navigate to="/dashboard" replace /> },
    { path: '/dashboard', element: <DashboardPage /> },
    { path: '/customers', element: <CustomersPage /> },
    { path: '/service-requests', element: <ServiceRequestsPage /> },
    { element: <RoleRoute allow={['admin']} />, children: [{ path: '/users', element: <UsersPage /> }] },
  ] }] },
  { path: '*', element: <NotFoundPage /> },
])
