import { useQuery } from '@tanstack/react-query'
import { getDashboard } from '../api/endpoints'
import { useAuth } from '../auth/AuthProvider'
import { PageHeader } from '../components/layout/PageHeader'
import { Badge } from '../components/ui/Badge'
import { ErrorState, LoadingState } from '../components/ui/Feedback'
import { MetricCard } from '../components/ui/MetricCard'
import type { AgentWorkSummary, DashboardOverview, RequestPriority, RequestStatus } from '../types/api'

export function DashboardPage() {
  const { user } = useAuth()
  const query = useQuery<DashboardOverview | AgentWorkSummary>({ queryKey: ['dashboard', user?.role], queryFn: () => getDashboard(user!.role), enabled: Boolean(user) })
  if (query.isLoading) return <LoadingState label="Loading dashboard…" />
  if (query.isError) return <ErrorState error={query.error} retry={() => query.refetch()} />
  const data = query.data!
  const admin = user?.role === 'admin'
  const overview = admin ? data as DashboardOverview : null
  const total = data.total_service_requests ?? data.total_assigned_service_requests ?? 0
  return <div className="page"><PageHeader eyebrow="Operations" title={admin ? 'Dashboard overview' : 'My work'} description={admin ? 'A clear view of demand and team workload.' : 'Requests currently assigned to you.'} />
    <section className="metric-grid"><MetricCard label={admin ? 'Total requests' : 'Assigned to me'} value={total} tone="accent" />{admin && <><MetricCard label="Customers" value={overview!.total_customers} /><MetricCard label="Unassigned" value={overview!.unassigned_service_requests} tone="warning" /></>}<MetricCard label="Open & active" value={data.service_requests_by_status.open + data.service_requests_by_status.in_progress} /></section>
    <section className="dashboard-grid"><article className="panel"><div className="panel-heading"><div><h2>Requests by status</h2><p>Current workflow distribution</p></div></div><div className="breakdown">{(Object.entries(data.service_requests_by_status) as [RequestStatus, number][]).map(([key, value]) => <div className="breakdown-row" key={key}><Badge value={key} /><div className="progress"><span style={{ width: `${total ? Math.max(4, value / total * 100) : 0}%` }} /></div><strong>{value}</strong></div>)}</div></article>
      <article className="panel"><div className="panel-heading"><div><h2>Requests by priority</h2><p>Workload urgency</p></div></div><div className="breakdown">{(Object.entries(data.service_requests_by_priority) as [RequestPriority, number][]).map(([key, value]) => <div className="breakdown-row" key={key}><Badge value={key} /><div className="progress"><span style={{ width: `${total ? Math.max(4, value / total * 100) : 0}%` }} /></div><strong>{value}</strong></div>)}</div></article>
      {overview && <article className="panel panel-wide"><div className="panel-heading"><div><h2>Agent workload</h2><p>Requests by current assignee</p></div></div>{overview.service_requests_by_assignee.length ? <div className="agent-list">{overview.service_requests_by_assignee.map((agent) => <div key={agent.agent_id}><span className="avatar">{agent.email[0].toUpperCase()}</span><div><strong>{agent.email}</strong><small>{agent.is_active ? 'Active agent' : 'Inactive'}</small></div><b>{agent.count}</b></div>)}</div> : <p className="muted">No assigned requests yet.</p>}</article>}
    </section>
  </div>
}
