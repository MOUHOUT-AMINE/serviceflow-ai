import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { customersApi } from '../api/endpoints'
import { useAuth } from '../auth/AuthProvider'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { DataTable } from '../components/ui/DataTable'
import { EmptyState, ErrorState, LoadingState } from '../components/ui/Feedback'
import { Input } from '../components/ui/Fields'
import { Modal } from '../components/ui/Modal'
import type { Customer } from '../types/api'

const schema = z.object({ name: z.string().trim().min(1, 'Name is required').max(100), email: z.email('Enter a valid email address') })
type Values = z.infer<typeof schema>
export function CustomersPage() {
  const { user } = useAuth(); const client = useQueryClient(); const query = useQuery({ queryKey: ['customers'], queryFn: customersApi.list })
  const [selected, setSelected] = useState<Customer | null>(null); const [editing, setEditing] = useState<Customer | 'new' | null>(null); const [apiError, setApiError] = useState('')
  const { register, handleSubmit, reset, formState: { errors } } = useForm<Values>({ resolver: zodResolver(schema) })
  const save = useMutation({ mutationFn: (values: Values) => editing === 'new' ? customersApi.create(values) : customersApi.update((editing as Customer).id, values), onSuccess: () => { client.invalidateQueries({ queryKey: ['customers'] }); setEditing(null) }, onError: (error) => setApiError(error.message) })
  const remove = useMutation({ mutationFn: customersApi.remove, onSuccess: () => { client.invalidateQueries({ queryKey: ['customers'] }); setSelected(null) } })
  const openForm = (customer: Customer | 'new') => { setApiError(''); setEditing(customer); reset(customer === 'new' ? { name: '', email: '' } : customer) }
  return <div className="page"><PageHeader eyebrow="Directory" title="Customers" description="Manage customer records and contact details." action={<Button onClick={() => openForm('new')}>Add customer</Button>} />
    {query.isLoading ? <LoadingState /> : query.isError ? <ErrorState error={query.error} retry={() => query.refetch()} /> : !query.data?.length ? <EmptyState title="No customers yet" message="Add your first customer to get started." /> : <DataTable headers={['Customer', 'Email', 'ID', 'Actions']} >{query.data.map((customer) => <tr key={customer.id}><td><button className="link-button" onClick={() => setSelected(customer)}>{customer.name}</button></td><td>{customer.email}</td><td className="muted">#{customer.id}</td><td><div className="row-actions"><Button variant="ghost" onClick={() => setSelected(customer)}>Details</Button><Button variant="secondary" onClick={() => openForm(customer)}>Edit</Button>{user?.role === 'admin' && <Button variant="danger" onClick={() => { if (confirm(`Delete ${customer.name}?`)) remove.mutate(customer.id) }}>Delete</Button>}</div></td></tr>)}</DataTable>}
    {editing && <Modal title={editing === 'new' ? 'Add customer' : 'Edit customer'} onClose={() => setEditing(null)}><form className="form-stack" onSubmit={handleSubmit((values) => save.mutate(values))}>{apiError && <div className="alert" role="alert">{apiError}</div>}<Input label="Customer name" error={errors.name?.message} {...register('name')} /><Input label="Email address" type="email" error={errors.email?.message} {...register('email')} /><div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setEditing(null)}>Cancel</Button><Button type="submit" disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save customer'}</Button></div></form></Modal>}
    {selected && <Modal title="Customer details" onClose={() => setSelected(null)}><dl className="details"><div><dt>Name</dt><dd>{selected.name}</dd></div><div><dt>Email</dt><dd>{selected.email}</dd></div><div><dt>Customer ID</dt><dd>#{selected.id}</dd></div></dl><div className="modal-actions"><Button variant="secondary" onClick={() => { setSelected(null); openForm(selected) }}>Edit</Button><Button onClick={() => setSelected(null)}>Done</Button></div></Modal>}
  </div>
}
