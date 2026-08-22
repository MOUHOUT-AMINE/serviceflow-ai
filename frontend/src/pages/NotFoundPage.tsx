import { Link } from 'react-router-dom'
export function NotFoundPage() { return <main className="not-found"><span className="eyebrow">404 error</span><h1>Page not found</h1><p>The page you’re looking for doesn’t exist or has moved.</p><Link className="button button-primary" to="/dashboard">Back to dashboard</Link></main> }
