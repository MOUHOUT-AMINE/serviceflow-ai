import { useEffect, type ReactNode } from 'react'

export function Modal({ title, children, onClose, closeLabel = 'Close' }: { title: string; closeLabel?: string; children: ReactNode; onClose: () => void }) {
  useEffect(() => { const close = (event: KeyboardEvent) => event.key === 'Escape' && onClose(); document.addEventListener('keydown', close); return () => document.removeEventListener('keydown', close) }, [onClose])
  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal-header"><h2 id="modal-title">{title}</h2><button className="icon-button" aria-label={closeLabel} onClick={onClose}>×</button></div>
      {children}
    </section>
  </div>
}
