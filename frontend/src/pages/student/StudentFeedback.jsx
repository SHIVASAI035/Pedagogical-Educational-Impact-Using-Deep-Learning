import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import { Badge, Card, EmptyState, ErrorAlert, Loading, PageHeader } from '../../components/ui'

const DIMENSIONS = [
  { key: 'clarity_rating', label: 'Clarity of explanation' },
  { key: 'interaction_rating', label: 'Classroom interaction' },
  { key: 'methodology_rating', label: 'Teaching methodology' },
  { key: 'practical_rating', label: 'Practical demonstrations' },
  { key: 'difficulty_rating', label: 'Pace / difficulty (1 = easy, 5 = hard)' },
  { key: 'overall_rating', label: 'Overall learning experience' },
]

const EMPTY_RATINGS = {
  clarity_rating: 3,
  interaction_rating: 3,
  methodology_rating: 3,
  practical_rating: 3,
  difficulty_rating: 3,
  overall_rating: 3,
}

export default function StudentFeedback() {
  const { user } = useAuth()
  const [teachers, setTeachers] = useState([])
  const [subjects, setSubjects] = useState([])
  const [history, setHistory] = useState([])
  const [form, setForm] = useState({
    teacher_id: '',
    subject_id: '',
    comments: '',
    is_anonymous: true,
    ...EMPTY_RATINGS,
  })
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [teachersResponse, subjectsResponse, historyResponse] = await Promise.all([
        api.get('/teachers', { params: { per_page: 100 } }),
        api.get('/subjects'),
        api.get('/feedback/mine'),
      ])
      setTeachers(teachersResponse.data.items)
      setSubjects(
        user?.class_id
          ? subjectsResponse.data.filter((subject) => subject.class_id === user.class_id)
          : subjectsResponse.data,
      )
      setHistory(historyResponse.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [user?.class_id])

  useEffect(() => {
    load()
  }, [load])

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setAnalysis(null)
    try {
      const payload = {
        teacher_id: Number(form.teacher_id),
        comments: form.comments.trim(),
        is_anonymous: form.is_anonymous,
      }
      if (form.subject_id) payload.subject_id = Number(form.subject_id)
      DIMENSIONS.forEach((dimension) => {
        payload[dimension.key] = Number(form[dimension.key])
      })
      const { data } = await api.post('/feedback', payload)
      setAnalysis(data.analysis)
      setForm({ ...form, comments: '', ...EMPTY_RATINGS })
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Teaching feedback"
        subtitle="Your feedback is anonymised before teachers see summaries. Be honest and constructive."
      />
      <ErrorAlert message={error} onRetry={load} />

      {loading ? (
        <Loading />
      ) : (
        <div className="grid gap-6 xl:grid-cols-5">
          <Card title="Submit feedback" className="xl:col-span-3">
            {teachers.length ? (
              <form className="space-y-4" onSubmit={submit}>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="label">Teacher</label>
                    <select
                      className="input"
                      required
                      value={form.teacher_id}
                      onChange={(event) => setForm({ ...form, teacher_id: event.target.value })}
                    >
                      <option value="">Select teacher</option>
                      {teachers.map((teacher) => (
                        <option key={teacher.id} value={teacher.id}>
                          {teacher.full_name} · {teacher.department || 'General'}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">Subject (optional)</label>
                    <select
                      className="input"
                      value={form.subject_id}
                      onChange={(event) => setForm({ ...form, subject_id: event.target.value })}
                    >
                      <option value="">General feedback</option>
                      {subjects.map((subject) => (
                        <option key={subject.id} value={subject.id}>
                          {subject.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-3">
                  {DIMENSIONS.map((dimension) => (
                    <div key={dimension.key} className="flex flex-col gap-2 rounded-lg bg-slate-50 p-3 sm:flex-row sm:items-center sm:justify-between">
                      <span className="text-sm text-slate-700">{dimension.label}</span>
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((value) => (
                          <button
                            key={value}
                            type="button"
                            onClick={() => setForm({ ...form, [dimension.key]: value })}
                            className={`h-8 w-8 rounded-md text-xs font-bold transition ${
                              form[dimension.key] === value
                                ? 'bg-navy-800 text-white'
                                : 'bg-white text-slate-500 ring-1 ring-slate-200 hover:bg-slate-100'
                            }`}
                            aria-label={`${dimension.label}: ${value}`}
                          >
                            {value}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                <div>
                  <label className="label">Comments</label>
                  <textarea
                    className="input min-h-[110px]"
                    maxLength={1000}
                    placeholder="What worked well? What could be improved?"
                    value={form.comments}
                    onChange={(event) => setForm({ ...form, comments: event.target.value })}
                  />
                </div>

                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={form.is_anonymous}
                    onChange={(event) => setForm({ ...form, is_anonymous: event.target.checked })}
                  />
                  Keep my feedback anonymous in teacher summaries
                </label>

                <button type="submit" className="btn-primary" disabled={busy}>
                  {busy ? 'Submitting…' : 'Submit feedback'}
                </button>
              </form>
            ) : (
              <EmptyState title="No teachers available" message="Feedback can be submitted once teachers are assigned." />
            )}

            {analysis && (
              <div className="mt-5 rounded-lg border border-green-200 bg-green-50 p-4">
                <p className="text-sm font-semibold text-green-800">
                  Feedback submitted · detected sentiment: {analysis.label}
                </p>
                <p className="mt-1 text-xs text-green-700">
                  Text score {analysis.text_score} · rating score {analysis.rating_score ?? '—'} · method{' '}
                  {analysis.method}
                </p>
              </div>
            )}
          </Card>

          <Card title="My previous feedback" subtitle="Only you can see these entries" className="xl:col-span-2">
            {history.length ? (
              <ul className="space-y-3">
                {history.map((entry) => (
                  <li key={entry.id} className="rounded-lg border border-slate-200 p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <Badge
                        tone={
                          entry.sentiment_label === 'positive'
                            ? 'green'
                            : entry.sentiment_label === 'negative'
                              ? 'red'
                              : 'slate'
                        }
                      >
                        {entry.sentiment_label}
                      </Badge>
                      <span className="text-[11px] text-slate-400">
                        {entry.created_at ? new Date(entry.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {entry.subject_name || 'General'} · overall {entry.overall_rating}/5
                    </p>
                    {entry.comments && (
                      <p className="mt-1 text-sm text-slate-600">“{entry.comments}”</p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No feedback submitted" message="Your submitted feedback will be listed here." />
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
