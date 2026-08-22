export type UserRole = 'admin' | 'agent'
export type RequestStatus = 'open' | 'in_progress' | 'resolved' | 'closed'
export type RequestPriority = 'low' | 'medium' | 'high'

export interface User {
  id: number
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Customer { id: number; name: string; email: string }

export interface ServiceRequest {
  id: number
  title: string
  description: string
  status: RequestStatus
  priority: RequestPriority
  customer_id: number
  assigned_agent_id: number | null
  assigned_agent_email: string | null
  created_by_user_id: number
  created_at: string
  updated_at: string
}

export interface DashboardCounts {
  total_service_requests?: number
  total_assigned_service_requests?: number
  service_requests_by_status: Record<RequestStatus, number>
  service_requests_by_priority: Record<RequestPriority, number>
}

export interface DashboardOverview extends DashboardCounts {
  total_service_requests: number
  total_customers: number
  unassigned_service_requests: number
  service_requests_by_assignee: Array<{ agent_id: number; email: string; is_active: boolean; count: number }>
}

export interface AgentWorkSummary extends DashboardCounts {
  total_assigned_service_requests: number
}

export interface ApiValidationIssue { loc?: Array<string | number>; msg?: string }
