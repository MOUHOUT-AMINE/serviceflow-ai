import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './AuthProvider'
import type { UserRole } from '../types/api'

export function RoleRoute({ allow }: { allow: UserRole[] }) {
  const { user } = useAuth()
  return user && allow.includes(user.role) ? <Outlet /> : <Navigate to="/dashboard" replace />
}
