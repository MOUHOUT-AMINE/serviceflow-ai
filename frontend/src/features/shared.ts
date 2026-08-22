import type { Customer, ServiceRequest, User } from '../types/api'
export const customerName = (customers: Customer[] | undefined, id: number) => customers?.find((item) => item.id === id)?.name ?? `Customer #${id}`
export const userEmail = (users: User[] | undefined, id: number | null, email?: string | null) => id ? users?.find((item) => item.id === id)?.email ?? email ?? `User #${id}` : 'Unassigned'
export const formatDate = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
export const matchesText = (request: ServiceRequest, text: string) => `${request.title} ${request.description}`.toLowerCase().includes(text.toLowerCase())
