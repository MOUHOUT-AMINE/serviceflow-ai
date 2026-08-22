import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthProvider'
import { LoadingState } from '../components/ui/Feedback'

export function ProtectedRoute() {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <div className="centered-page"><LoadingState label="Loading your workspace…" /></div>
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return <Outlet />
}
