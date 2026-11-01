import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import { BarChart, COLORS, DoughnutChart } from '../../components/charts'
import {
  Badge,
  Card,
  ErrorAlert,
  Loading,
  PageHeader,
  ProgressBar,
  StatCard,
} from '../../components/ui'

const RATING_LABELS = {
  clarity_rating: 'Clarity',
  interaction_rating: 'Interaction',
  methodology_rating: 'Methodology',
  practical_rating: 'Practical',
  difficulty_rating: 'Difficulty',
  overall_rating: 'Overall',
}

export default function TeacherDashboard({ teacherId }) {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const endpoint = teacherId
        ? `/analytics/teacher/${teacherId}`
        : '/analytics/teacher/me'
      const { data: analytics } = await api.get(endpoint)
      setData(analytics)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [teacherId])

  useEffect(() => {
    load()
  }, [load])

  if (loading && !data) return <Loading label="Loading your teaching analytics…" />

  const feedback = data?.feedback || {}
  const sentiment = feedback.sentiment || {}
  const averages = feedback.averages || {}
  const observations = data?.observations || {}
  const sufficiency = data?.data_sufficiency || {}
  const subjectPerformance = data?.subject_performance || []
  const mix = data?.methodology_mix || []

  return (
    <div>
      <PageHeader
        title={
          teacherId && user?.role === 'admin'
            ? `${data?.teacher?.full_name || 'Teacher'} · analytics`
            : `Welcome, ${data?.teacher?.full_name || 'teacher'}`
        }
        subtitle="A multi-indicator view of classroom practice — not a single performance score."
        actions={
          teacherId && user?.role === 'admin' ? (
            <Link to="/admin/reports" className="btn-ghost">
              Back to reports
            </Link>
          ) : (
            <>
              <Link to="/teacher/feedback" className="btn-ghost">
                Feedback insights
              </Link>
              <Link to="/teacher/recommendations" className="btn-primary">
                My recommendations
              </Link>
            </>
          )
        }
      />
      <ErrorAlert message={error} onRetry={load} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Assigned students" value={data?.students?.count} icon="users" hint={`${data?.students?.classes ?? 0} classes · ${data?.subjects?.length ?? 0} subjects`} />
        <StatCard label="Average attendance" value={data?.students?.average_attendance != null ? `${data.students.average_attendance}%` : '—'} icon="check" tone="green" hint="Across your assigned students" />
        <StatCard label="Feedback responses" value={feedback.count} icon="feedback" hint={`${sentiment.positive_pct ?? 0}% positive sentiment`} />
        <StatCard label="Classroom observations" value={observations.count} icon="star" tone="amber" hint={`${data?.methodology_mix?.reduce((sum, item) => sum + item.sessions, 0) ?? 0} teaching sessions logged`} />
      </div>

      {!sufficiency.adequate && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <strong>Interpret with care.</strong> {sufficiency.note} Currently: {sufficiency.feedback_observations}{' '}
          feedback responses and {sufficiency.classroom_observations} observations.
        </div>
      )}

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Subject performance" subtitle="Average marks in the subjects you teach" className="xl:col-span-2">
          {subjectPerformance.length ? (
            <BarChart
              data={{
                labels: subjectPerformance.map((subject) => `${subject.subject_name} · ${subject.class_name || ''}`),
                datasets: [
                  {
                    label: 'Average score (%)',
                    data: subjectPerformance.map((subject) => subject.average_pct),
                    backgroundColor: COLORS.navy,
                    borderRadius: 6,
                    maxBarThickness: 40,
                  },
                ],
              }}
              options={{ plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } }}
              height={280}
            />
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">No subjects assigned yet.</p>
          )}
        </Card>

        <Card title="Student feedback sentiment" subtitle={`${feedback.count ?? 0} anonymous responses`}>
          <DoughnutChart
            data={{
              labels: ['Positive', 'Neutral', 'Negative'],
              datasets: [
                {
                  data: [sentiment.positive || 0, sentiment.neutral || 0, sentiment.negative || 0],
                  backgroundColor: [COLORS.green, COLORS.slate, COLORS.red],
                  borderWidth: 0,
                },
              ],
            }}
          />
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Feedback dimensions" subtitle="Average rating out of 5" className="xl:col-span-2">
          <div className="space-y-4">
            {Object.entries(RATING_LABELS).map(([key, label]) => (
              <div key={key}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-slate-600">{label}</span>
                  <span className="font-semibold text-slate-800">
                    {averages[key] != null ? `${averages[key]} / 5` : '—'}
                  </span>
                </div>
                <ProgressBar
                  value={averages[key] != null ? (averages[key] / 5) * 100 : 0}
                  tone={averages[key] >= 4 ? 'green' : averages[key] >= 3.5 ? 'navy' : 'amber'}
                />
              </div>
            ))}
          </div>
        </Card>

        <Card title="Methodology mix" subtitle="Logged teaching approaches">
          {mix.length ? (
            <>
              <BarChart
                horizontal
                data={{
                  labels: mix.map((item) => item.methodology),
                  datasets: [
                    {
                      label: 'Sessions',
                      data: mix.map((item) => item.sessions),
                      backgroundColor: COLORS.green,
                      borderRadius: 6,
                      maxBarThickness: 22,
                    },
                  ],
                }}
                options={{ plugins: { legend: { display: false } } }}
                height={220}
              />
              <p className="mt-3 text-xs text-slate-500">
                A narrow mix is not automatically a weakness — it depends on the topic and class.
              </p>
            </>
          ) : (
            <p className="py-8 text-center text-sm text-slate-500">No teaching sessions logged.</p>
          )}
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Effectiveness indicators" subtitle="Contextual indicators, interpreted together" className="xl:col-span-2">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="table-head">
                <tr>
                  <th className="px-3 py-2">Indicator</th>
                  <th className="px-3 py-2">Value</th>
                  <th className="px-3 py-2">Benchmark</th>
                  <th className="px-3 py-2">Signal</th>
                  <th className="px-3 py-2">Evidence</th>
                </tr>
              </thead>
              <tbody>
                {(data?.indicators || []).map((indicator) => {
                  const lowerIsBetter = indicator.indicator.toLowerCase().includes('negative')
                  const good =
                    indicator.value == null
                      ? null
                      : lowerIsBetter
                        ? indicator.value <= indicator.benchmark
                        : indicator.value >= indicator.benchmark
                  return (
                    <tr key={indicator.indicator} className="align-top hover:bg-slate-50">
                      <td className="table-cell">
                        <p className="font-medium text-navy-900">{indicator.indicator}</p>
                        <p className="mt-0.5 text-xs text-slate-500">{indicator.interpretation}</p>
                      </td>
                      <td className="table-cell font-semibold">{indicator.value ?? '—'}</td>
                      <td className="table-cell text-slate-500">{indicator.benchmark}</td>
                      <td className="table-cell">
                        {good == null ? (
                          <Badge>no data</Badge>
                        ) : (
                          <Badge tone={good ? 'green' : 'amber'}>{good ? 'at/above' : 'review'}</Badge>
                        )}
                      </td>
                      <td className="table-cell text-xs text-slate-500">
                        {indicator.observations} · {indicator.source}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Recent comments" subtitle="Anonymised student feedback">
          {data?.recent_comments?.length ? (
            <ul className="space-y-3">
              {data.recent_comments.slice(0, 5).map((comment, index) => (
                <li key={`${comment.date}-${index}`} className="rounded-lg border border-slate-200 p-3">
                  <div className="mb-1 flex items-center justify-between">
                    <Badge
                      tone={
                        comment.sentiment === 'positive'
                          ? 'green'
                          : comment.sentiment === 'negative'
                            ? 'red'
                            : 'slate'
                      }
                    >
                      {comment.sentiment || 'neutral'}
                    </Badge>
                    <span className="text-[11px] text-slate-400">{comment.date}</span>
                  </div>
                  <p className="text-xs leading-relaxed text-slate-600">“{comment.comment}”</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-8 text-center text-sm text-slate-500">No written comments yet.</p>
          )}
        </Card>
      </div>

      <Card className="mt-6" title="How to read these indicators">
        <ul className="grid gap-2 text-xs leading-relaxed text-slate-600 sm:grid-cols-2">
          {(data?.caveats || []).map((caveat) => (
            <li key={caveat} className="rounded-lg bg-slate-50 px-3 py-2">
              {caveat}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
