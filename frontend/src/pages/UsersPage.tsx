import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { usersApi } from '../api/endpoints'
import { useAuth } from '../auth/AuthProvider'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { DataTable } from '../components/ui/DataTable'
import { EmptyState, ErrorState, LoadingState } from '../components/ui/Feedback'
import { Input, Select } from '../components/ui/Fields'
import { Modal } from '../components/ui/Modal'
import { formatDate } from '../features/shared'
import type { UserRole } from '../types/api'

const schema = z.object({ email: z.email('Enter a valid email address'), password: z.string().min(8, 'Password must be at least 8 characters').max(128), role: z.enum(['admin', 'agent']) })
type Values = z.infer<typeof schema>
export function UsersPage() {
  const { user } = useAuth(); const client = useQueryClient(); const query = useQuery({ queryKey: ['users'], queryFn: usersApi.list }); const [creating, setCreating] = useState(false); const [apiError, setApiError] = useState('')
  const { register, handleSubmit, reset, formState: { errors } } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { role: 'agent' } })
  const refresh = () => client.invalidateQueries({ queryKey: ['users'] })
  const create = useMutation({ mutationFn: usersApi.create, onSuccess: () => { refresh(); setCreating(false); reset() }, onError: (error) => setApiError(error.message) })
  const update = useMutation({ mutationFn: ({ id, data }: { id: number; data: { role?: UserRole; is_active?: boolean } }) => usersApi.update(id, data), onSuccess: refresh })
  return <div className="page"><PageHeader eyebrow="Administration" title="Users" description="Manage team access, roles, and account status." action={<Button onClick={() => { setApiError(''); setCreating(true) }}>Add user</Button>} />
    {query.isLoading ? <LoadingState /> : query.isError ? <ErrorState error={query.error} retry={() => query.refetch()} /> : !query.data?.length ? <EmptyState title="No users" message="Create a user to build your team." /> : <DataTable headers={['User', 'Role', 'Status', 'Created', 'Controls']}>{query.data.map((item) => <tr key={item.id}><td><div className="user-cell"><span className="avatar">{item.email[0].toUpperCase()}</span><div><strong>{item.email}</strong><small>User #{item.id}</small></div></div></td><td><Select aria-label={`Role for ${item.email}`} label="" value={item.role} disabled={item.id === user?.id} onChange={(e) => update.mutate({ id: item.id, data: { role: e.target.value as UserRole } })}><option value="agent">Agent</option><option value="admin">Admin</option></Select></td><td><span className={`status-dot ${item.is_active ? 'active' : ''}`}>{item.is_active ? 'Active' : 'Inactive'}</span></td><td className="muted">{formatDate(item.created_at)}</td><td><Button variant={item.is_active ? 'danger' : 'secondary'} disabled={item.id === user?.id} onClick={() => update.mutate({ id: item.id, data: { is_active: !item.is_active } })}>{item.is_active ? 'Deactivate' : 'Activate'}</Button></td></tr>)}</DataTable>}
    {creating && <Modal title="Create user" onClose={() => setCreating(false)}><form className="form-stack" onSubmit={handleSubmit((values) => create.mutate(values))}>{apiError && <div className="alert" role="alert">{apiError}</div>}<Input label="Email address" type="email" error={errors.email?.message} {...register('email')} /><Input label="Temporary password" type="password" error={errors.password?.message} {...register('password')} /><Select label="Role" {...register('role')}><option value="agent">Agent</option><option value="admin">Admin</option></Select><div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setCreating(false)}>Cancel</Button><Button type="submit" disabled={create.isPending}>{create.isPending ? 'Creating…' : 'Create user'}</Button></div></form></Modal>}
  </div>
}
