import Icon from './Icon'

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-navy-900">{title}</h1>
        {subtitle && <p className="mt-1 max-w-2xl text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

export function Card({ title, subtitle, actions, children, className = '' }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="flex flex-col gap-2 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            {title && <h2 className="text-sm font-bold uppercase tracking-wide text-navy-800">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  )
}

const TONES = {
  navy: 'bg-navy-50 text-navy-700',
  green: 'bg-green-50 text-green-700',
  amber: 'bg-amber-50 text-amber-700',
  red: 'bg-red-50 text-red-700',
  slate: 'bg-slate-100 text-slate-600',
}

export function StatCard({ label, value, hint, tone = 'navy', icon = 'chart' }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-bold text-navy-900">{value ?? '—'}</p>
          {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
        </div>
        <span className={`rounded-lg p-2 ${TONES[tone] || TONES.navy}`}>
          <Icon name={icon} className="h-5 w-5" />
        </span>
      </div>
    </div>
  )
}

export function Badge({ children, tone = 'slate' }) {
  return <span className={`badge ${TONES[tone] || TONES.slate}`}>{children}</span>
}

export function RiskBadge({ level }) {
  const tone = level === 'high' ? 'red' : level === 'moderate' ? 'amber' : 'green'
  return <Badge tone={tone}>{level ? level.toUpperCase() : 'UNKNOWN'}</Badge>
}

export function ProgressBar({ value = 0, tone = 'green' }) {
  const colors = {
    green: 'bg-green-500',
    navy: 'bg-navy-700',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
  }
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div
        className={`h-full rounded-full ${colors[tone] || colors.green}`}
        style={{ width: `${Math.max(0, Math.min(100, Number(value) || 0))}%` }}
      />
    </div>
  )
}

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-sm text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-navy-700" />
      {label}
    </div>
  )
}

export function ErrorAlert({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="mb-4 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">{message}</div>
      {onRetry && (
        <button type="button" className="font-semibold underline" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title = 'Nothing here yet', message }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      {message && <p className="mt-1 text-xs text-slate-500">{message}</p>}
    </div>
  )
}

export function Tabs({ tabs, active, onChange }) {
  return (
    <div className="flex flex-wrap gap-1 rounded-lg bg-slate-100 p-1">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          onClick={() => onChange(tab.value)}
          className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
            active === tab.value
              ? 'bg-white text-navy-800 shadow-sm'
              : 'text-slate-500 hover:text-navy-700'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
