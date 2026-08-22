import { NavLink, Outlet } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../../auth/AuthProvider'
import { Button } from '../ui/Button'

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: '⌂' },
  { to: '/customers', label: 'Customers', icon: '◇' },
  { to: '/service-requests', label: 'Service Requests', icon: '□' },
]
export function AppLayout() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  return <div className="app-shell">
    {open && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setOpen(false)} />}
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <div className="brand"><span className="brand-mark">S</span><div><strong>ServiceFlow</strong><small>AI Operations</small></div></div>
      <nav aria-label="Primary navigation">
        {nav.map((item) => <NavLink key={item.to} to={item.to} onClick={() => setOpen(false)}><span>{item.icon}</span>{item.label}</NavLink>)}
        {user?.role === 'admin' && <NavLink to="/users" onClick={() => setOpen(false)}><span>○</span>Users</NavLink>}
      </nav>
      <div className="sidebar-profile"><div className="avatar">{user?.email[0].toUpperCase()}</div><div><strong>{user?.email}</strong><small>{user?.role}</small></div></div>
    </aside>
    <div className="app-main">
      <header className="topbar"><button className="menu-button" onClick={() => setOpen(true)} aria-label="Open navigation">☰</button><div className="topbar-spacer" /><span className="role-pill">{user?.role}</span><Button variant="ghost" onClick={logout}>Sign out</Button></header>
      <main><Outlet /></main>
    </div>
  </div>
}
