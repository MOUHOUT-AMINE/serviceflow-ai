import type { RequestPriority, RequestStatus } from '../../types/api'
import { requestLabels } from '../../features/requestLabels'

export function Badge({ value }: { value: RequestStatus | RequestPriority }) { return <span className={`badge badge-${value}`}>{requestLabels[value]}</span> }
