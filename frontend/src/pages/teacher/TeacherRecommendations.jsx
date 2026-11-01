import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { Badge, Card, EmptyState, ErrorAlert, Loading, PageHeader } from '../../components/ui'

const PRIORITY_TONE = { high: 'red', medium: 'amber', low: 'green' }

export default function TeacherRecommendations() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/recommendations/me')
      setItems(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function refresh() {
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/recommendations/generate', {})
      setItems(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const grouped = ['high', 'medium', 'low'].map((priority) => ({
    priority,
    items: items.filter((item) => item.priority === priority),
  }))

  return (
    <div>
      <PageHeader
        title="Teaching improvement recommendations"
        subtitle="Supportive, evidence-linked suggestions. Each one explains the data behind it."
        actions={
          <button type="button" className="btn-green" onClick={refresh} disabled={busy}>
            {busy ? 'Refreshing…' : 'Refresh recommendations'}
          </button>
        }
      />
      <ErrorAlert message={error} onRetry={load} />

      {loading ? (
        <Loading />
      ) : !items.length ? (
        <EmptyState title="No recommendations yet" message="Record feedback and observations to generate suggestions." />
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          {grouped.map((group) => (
            <div key={group.priority}>
              <h2 className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-600">
                <Badge tone={PRIORITY_TONE[group.priority]}>{group.priority}</Badge>
                Priority
              </h2>
              <div className="space-y-3">
                {group.items.map((item) => (
                  <Card key={item.id || item.category}>
                    <p className="text-sm font-bold text-navy-900">{item.category}</p>
                    <p className="mt-1 text-sm text-slate-700">{item.message}</p>
                    <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs leading-relaxed text-slate-500">
                      <strong className="text-slate-600">Why:</strong> {item.rationale}
                    </p>
                  </Card>
                ))}
                {!group.items.length && (
                  <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-xs text-slate-400">
                    Nothing at this priority.
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="mt-6 text-xs leading-relaxed text-slate-500">
        Recommendations are generated from transparent thresholds on your own feedback and
        observation data. They are developmental suggestions, not performance judgements, and
        should be discussed with your academic coordinator.
      </p>
    </div>
  )
}
