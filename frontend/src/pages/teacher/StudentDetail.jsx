import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { errorMessage } from '../../api/client'
import { BarChart, COLORS, LineChart } from '../../components/charts'
import {
  Badge,
  Card,
  ErrorAlert,
  Loading,
  PageHeader,
  ProgressBar,
  RiskBadge,
  StatCard,
} from '../../components/ui'

export default function StudentDetail() {
  const { studentId } = useParams()
  const [data, setData] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [prediction, setPrediction] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [analytics, recs, predictions] = await Promise.all([
        api.get(`/analytics/student/${studentId}`),
        api.get(`/recommendations/student/${studentId}`),
        api.get(`/dl/predictions?student_id=${studentId}`),
      ])
      setData(analytics.data)
      setRecommendations(recs.data)
      setPrediction(predictions.data[0] || analytics.data.prediction)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [studentId])

  useEffect(() => {
    load()
  }, [load])

  async function runPrediction() {
    setBusy(true)
    setError('')
    try {
      const { data: result } = await api.post(`/dl/predict/${studentId}`)
      setPrediction(result)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (loading && !data) return <Loading label="Loading student analytics…" />
  if (!data) return <ErrorAlert message={error || 'Student not found.'} onRetry={load} />

  const attendance = data.attendance || {}
  const academics = data.academics || {}
  const assignments = data.assignments || {}
  const learning = data.learning || {}
  const subjects = academics.subjects || []
  const trend = academics.trend || []

  return (
    <div>
      <PageHeader
        title={data.student?.full_name || 'Student'}
        subtitle={`Roll ${data.student?.roll_number} · ${data.student?.class_name || 'Unassigned'}`}
        actions={
          <>
            <Link to="/teacher/students" className="btn-ghost">
              Back to students
            </Link>
            <button type="button" className="btn-green" onClick={runPrediction} disabled={busy}>
              {busy ? 'Predicting…' : 'Run prediction'}
            </button>
          </>
        }
      />
      <ErrorAlert message={error} onRetry={load} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Average score" value={academics.average_pct != null ? `${academics.average_pct}%` : '—'} icon="chart" hint="Across all recorded exams" />
        <StatCard label="Attendance" value={`${attendance.overall_pct ?? 0}%`} icon="check" tone="green" hint={`${attendance.records ?? 0} records · ${attendance.absent ?? 0} absences`} />
        <StatCard label="Assignments" value={`${assignments.completion_pct ?? 0}%`} icon="book" hint={`${assignments.submitted ?? 0}/${assignments.total ?? 0} submitted`} />
        <StatCard label="Predicted score" value={prediction ? `${prediction.predicted_score}%` : '—'} icon="brain" tone={prediction?.risk_level === 'high' ? 'red' : 'navy'} hint={prediction ? `Risk: ${prediction.risk_level}` : 'No prediction yet'} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Academic progress" subtitle="Average percentage per exam date" className="xl:col-span-2">
          {trend.length ? (
            <LineChart
              data={{
                labels: trend.map((item) => item.period),
                datasets: [
                  {
                    label: 'Average score (%)',
                    data: trend.map((item) => item.score),
                    borderColor: COLORS.navy,
                    backgroundColor: 'rgba(22,57,90,0.08)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                  },
                ],
              }}
              options={{ scales: { y: { min: 0, max: 100 } } }}
              height={280}
            />
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">No marks recorded yet.</p>
          )}
        </Card>

        <Card title="Prediction" subtitle="Latest model output">
          {prediction ? (
            <>
              <div className="flex items-center justify-between">
                <p className="text-3xl font-bold text-navy-900">{prediction.predicted_score}%</p>
                <RiskBadge level={prediction.risk_level} />
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Model {prediction.model_version} ·{' '}
                {prediction.created_at ? new Date(prediction.created_at).toLocaleString() : ''}
              </p>
              <div className="mt-4 space-y-3">
                {[
                  ['Attendance', data.features?.attendance_pct],
                  ['Study hours (×10)', (data.features?.study_hours || 0) * 10],
                  ['Assignment completion', data.features?.assignment_completion],
                  ['Engagement', data.features?.learning_engagement],
                ].map(([label, value]) => (
                  <div key={label}>
                    <div className="mb-1 flex justify-between text-xs">
                      <span className="text-slate-600">{label}</span>
                      <span className="font-semibold text-slate-800">{value != null ? Math.round(value) : '—'}</span>
                    </div>
                    <ProgressBar value={value || 0} tone="navy" />
                  </div>
                ))}
              </div>
              <p className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">
                Data confidence: <strong>{data.data_quality?.confidence}</strong> · completeness{' '}
                {Math.round((data.data_quality?.completeness || 0) * 100)}%
              </p>
            </>
          ) : (
            <p className="py-8 text-center text-sm text-slate-500">
              Run a prediction to see the model estimate.
            </p>
          )}
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card title="Subject performance">
          {subjects.length ? (
            <BarChart
              horizontal
              data={{
                labels: subjects.map((subject) => subject.subject_name),
                datasets: [
                  {
                    label: 'Average (%)',
                    data: subjects.map((subject) => subject.average_pct),
                    backgroundColor: subjects.map((subject) =>
                      subject.average_pct < 50 ? COLORS.red : subject.average_pct < 65 ? COLORS.amber : COLORS.green,
                    ),
                    borderRadius: 6,
                    maxBarThickness: 24,
                  },
                ],
              }}
              options={{ plugins: { legend: { display: false } }, scales: { x: { min: 0, max: 100 } } }}
              height={260}
            />
          ) : (
            <p className="py-8 text-center text-sm text-slate-500">No subject marks yet.</p>
          )}
        </Card>

        <Card title="Personalised support" subtitle="Explainable recommendations">
          <ul className="space-y-3">
            {recommendations.slice(0, 5).map((item) => (
              <li key={item.id || item.category} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-navy-900">{item.message}</p>
                  <Badge tone={item.priority === 'high' ? 'red' : item.priority === 'medium' ? 'amber' : 'green'}>
                    {item.priority}
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-slate-500">{item.rationale}</p>
              </li>
            ))}
            {!recommendations.length && (
              <p className="py-6 text-center text-sm text-slate-500">No recommendations yet.</p>
            )}
          </ul>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Card title="Learning habits">
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Study hours/day</dt><dd className="font-semibold">{learning.study_hours_per_day ?? '—'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Participation</dt><dd className="font-semibold">{learning.participation_pct ?? '—'}%</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Engagement</dt><dd className="font-semibold">{learning.engagement_pct ?? '—'}%</dd></div>
          </dl>
        </Card>
        <Card title="Attendance">
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Present</dt><dd className="font-semibold">{attendance.present ?? 0}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Late</dt><dd className="font-semibold">{attendance.late ?? 0}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Absent</dt><dd className="font-semibold">{attendance.absent ?? 0}</dd></div>
          </dl>
        </Card>
        <Card title="Focus subjects">
          <p className="text-sm text-slate-600">
            Strongest: <strong>{academics.strongest_subject?.subject_name || '—'}</strong>
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Needs support: <strong>{academics.weakest_subject?.subject_name || '—'}</strong>
          </p>
        </Card>
      </div>
    </div>
  )
}
