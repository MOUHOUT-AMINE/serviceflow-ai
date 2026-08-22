import { Button } from './Button'

export function LoadingState({ label = 'Loading…' }: { label?: string }) { return <div className="state"><span className="spinner" /> <span>{label}</span></div> }
export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  const message = error instanceof Error ? error.message : 'Something went wrong.'
  return <div className="state state-error"><strong>Unable to load</strong><span>{message}</span>{retry && <Button variant="secondary" onClick={retry}>Try again</Button>}</div>
}
export function EmptyState({ title, message }: { title: string; message: string }) { return <div className="state"><strong>{title}</strong><span>{message}</span></div> }
