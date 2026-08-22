import type { RequestPriority, RequestStatus } from '../../types/api'

const labels = { open: 'Open', in_progress: 'In progress', resolved: 'Resolved', closed: 'Closed', low: 'Low', medium: 'Medium', high: 'High' }
export function Badge({ value }: { value: RequestStatus | RequestPriority }) { return <span className={`badge badge-${value}`}>{labels[value]}</span> }
