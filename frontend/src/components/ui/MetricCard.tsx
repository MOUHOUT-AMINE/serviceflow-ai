export function MetricCard({ label, value, tone = 'default' }: { label: string; value: number; tone?: 'default' | 'accent' | 'warning' }) {
  return <article className={`metric-card metric-${tone}`}><span>{label}</span><strong>{value.toLocaleString()}</strong></article>
}
