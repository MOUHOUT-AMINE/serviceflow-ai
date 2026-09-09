import type { RequestPriority, RequestStatus } from '../types/api'

// Display text only. API payloads, filters, and CSS classes use the enum keys.
export const requestLabels: Record<RequestStatus | RequestPriority, string> = {
  low: 'faible',
  medium: 'moyenne',
  high: 'élevée',
  open: 'ouvert',
  in_progress: 'en cours',
  resolved: 'résolu',
  closed: 'fermé',
}
