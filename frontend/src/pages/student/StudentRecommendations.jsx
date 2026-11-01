import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { Badge, Card, EmptyState, ErrorAlert, Loading, PageHeader } from '../../components/ui'

const PRIORITY_TONE = { high: 'red', medium: 'amber', low: 'green' }

export default function StudentRecommendations() {
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

  return (
    <div>
      <PageHeader
        title="My recommendations"
        subtitle="Personalised, supportive next steps based on your attendance, assignments, engagement and marks."
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
        <EmptyState title="No recommendations yet" message="Recommendations appear once your records are available." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {items.map((item) => (
            <Card key={item.id || item.category}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-green-700">{item.category}</p>
                  <p className="mt-1 text-base font-semibold text-navy-900">{item.message}</p>
                </div>
                <Badge tone={PRIORITY_TONE[item.priority]}>{item.priority}</Badge>
              </div>
              <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs leading-relaxed text-slate-500">
                <strong className="text-slate-600">Why this suggestion:</strong> {item.rationale}
              </p>
            </Card>
          ))}
        </div>
      )}

      <p className="mt-6 text-xs leading-relaxed text-slate-500">
        These suggestions are developmental, not punitive. They are generated from transparent
        thresholds, so you can always see which record triggered each recommendation.
      </p>
    </div>
  )
}
