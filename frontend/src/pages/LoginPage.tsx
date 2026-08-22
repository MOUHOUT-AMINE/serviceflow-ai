import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { useAuth } from '../auth/AuthProvider'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Fields'

const schema = z.object({ email: z.email('Enter a valid email address'), password: z.string().min(8, 'Password must be at least 8 characters') })
type LoginValues = z.infer<typeof schema>
export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [apiError, setApiError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginValues>({ resolver: zodResolver(schema) })
  if (user) return <Navigate to="/dashboard" replace />
  const submit = async (values: LoginValues) => {
    setApiError('')
    try { await login(values.email, values.password); navigate((location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/dashboard', { replace: true }) }
    catch (error) { setApiError(error instanceof Error ? error.message : 'Unable to sign in.') }
  }
  return <main className="login-page">
    <section className="login-brand"><div className="brand brand-light"><span className="brand-mark">S</span><div><strong>ServiceFlow</strong><small>AI Operations</small></div></div><div className="login-copy"><span className="eyebrow">Service operations, simplified</span><h1>Keep every customer request moving.</h1><p>A focused workspace for support teams to track demand, prioritize work, and deliver excellent service.</p></div></section>
    <section className="login-panel"><form className="login-card" onSubmit={handleSubmit(submit)} noValidate><div><span className="eyebrow">Welcome back</span><h2>Sign in to your workspace</h2><p>Use your ServiceFlow account credentials.</p></div>{apiError && <div className="alert" role="alert">{apiError}</div>}<Input label="Email address" type="email" autoComplete="email" placeholder="you@company.com" error={errors.email?.message} {...register('email')} /><Input label="Password" type="password" autoComplete="current-password" placeholder="At least 8 characters" error={errors.password?.message} {...register('password')} /><Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Signing in…' : 'Sign in'}</Button></form>
    </section>
  </main>
}
