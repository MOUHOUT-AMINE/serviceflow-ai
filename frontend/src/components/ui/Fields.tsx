import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'

interface FieldProps { label: string; error?: string }
export const Input = forwardRef<HTMLInputElement, FieldProps & InputHTMLAttributes<HTMLInputElement>>(({ label, error, ...props }, ref) => (
  <label className="field"><span>{label}</span><input ref={ref} aria-invalid={Boolean(error)} {...props} />{error && <small role="alert">{error}</small>}</label>
))
export const Select = forwardRef<HTMLSelectElement, FieldProps & SelectHTMLAttributes<HTMLSelectElement>>(({ label, error, children, ...props }, ref) => (
  <label className="field"><span>{label}</span><select ref={ref} aria-invalid={Boolean(error)} {...props}>{children}</select>{error && <small role="alert">{error}</small>}</label>
))
export const Textarea = forwardRef<HTMLTextAreaElement, FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>>(({ label, error, ...props }, ref) => (
  <label className="field"><span>{label}</span><textarea ref={ref} aria-invalid={Boolean(error)} {...props} />{error && <small role="alert">{error}</small>}</label>
))
