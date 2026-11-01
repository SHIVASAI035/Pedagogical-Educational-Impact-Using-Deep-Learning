import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
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

export default function StudentDashboard() {
  const [data, setData] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [assignments, setAssignments] = useState([])
  const [submissions, setSubmissions] = useState([])
  const [prediction, setPrediction] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [analytics, recs, assignmentList, submissionList] = await Promise.all([
        api.get('/analytics/student/me'),
        api.get('/recommendations/me'),
        api.get('/academics/assignments', { params: { per_page: 50 } }),
        api.get('/academics/submissions', { params: { per_page: 50 } }),
      ])
      setData(analytics.data)
      setRecommendations(recs.data)
      setAssignments(assignmentList.data.items)
      setSubmissions(submissionList.data.items)
      setPrediction(analytics.data.prediction)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function predict() {
    setBusy(true)
    setError('')
    try {
      const { data: result } = await api.post('/dl/predict/me')
      setPrediction(result)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (loading && !data) return <Loading label="Loading your dashboard…" />
  if (!data) return <ErrorAlert message={error || 'Unable to load your dashboard.'} onRetry={load} />

  const attendance = data.attendance || {}
  const academics = data.academics || {}
  const assignmentsSummary = data.assignments || {}
  const subjects = academics.subjects || []
  const trend = academics.trend || []
  const monthly = attendance.monthly || []
  const submittedIds = new Set(
    submissions.filter((row) => row.status !== 'pending').map((row) => row.assignment_id),
  )
  const pending = assignments.filter((assignment) => !submittedIds.has(assignment.id)).slice(0, 4)

  return (
    <div>
      <PageHeader
        title={`Hello, ${data.student?.full_name || 'student'}`}
        subtitle={`${data.student?.class_name || 'Class not assigned'} · Roll ${data.student?.roll_number || '—'}`}
        actions={
          <>
            <Link to="/student/performance" className="btn-ghost">
              Full performance
            </Link>
            <button type="button" className="btn-green" onClick={predict} disabled={busy}>
              {busy ? 'Predicting…' : 'Predict my score'}
            </button>
          </>
        }
      />
      <ErrorAlert message={error} onRetry={load} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Average score" value={academics.average_pct != null ? `${academics.average_pct}%` : '—'} icon="chart" hint={`Latest exam average ${academics.latest_exam_average ?? '—'}%`} />
        <StatCard label="Attendance" value={`${attendance.overall_pct ?? 0}%`} icon="check" tone="green" hint={`${attendance.absent ?? 0} absence(s) recorded`} />
        <StatCard label="Assignments" value={`${assignmentsSummary.completion_pct ?? 0}%`} icon="book" hint={`${assignmentsSummary.pending ?? 0} pending of ${assignmentsSummary.total ?? 0}`} />
        <StatCard label="Predicted score" value={prediction ? `${prediction.predicted_score}%` : '—'} icon="brain" tone={prediction?.risk_level === 'high' ? 'red' : 'navy'} hint={prediction ? `Support level: ${prediction.risk_level}` : 'Run a prediction'} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Academic progress" subtitle="Average percentage across exam dates" className="xl:col-span-2">
          {trend.length ? (
            <LineChart
              data={{
                labels: trend.map((item) => item.period),
                datasets: [
                  {
                    label: 'Score (%)',
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
            <p className="py-10 text-center text-sm text-slate-500">Marks will appear here once recorded.</p>
          )}
        </Card>

        <Card title="Prediction & support" subtitle="Model estimate, not a final grade">
          {prediction ? (
            <>
              <div className="flex items-center justify-between">
                <p className="text-3xl font-bold text-navy-900">{prediction.predicted_score}%</p>
                <RiskBadge level={prediction.risk_level} />
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Generated {prediction.created_at ? new Date(prediction.created_at).toLocaleDateString() : 'recently'}
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
                      <span className="font-semibold">{value != null ? Math.round(value) : '—'}</span>
                    </div>
                    <ProgressBar value={value || 0} tone="navy" />
                  </div>
                ))}
              </div>
              <p className="mt-4 rounded-lg bg-green-50 p-3 text-xs text-green-800">
                A higher predicted score is associated with consistent attendance, completed
                assignments and active participation. Small consistent habits matter most.
              </p>
            </>
          ) : (
            <p className="py-8 text-center text-sm text-slate-500">
              Click “Predict my score” to see your model estimate.
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

        <Card title="Attendance by month">
          {monthly.length ? (
            <BarChart
              data={{
                labels: monthly.map((item) => item.period),
                datasets: [
                  {
                    label: 'Attendance (%)',
                    data: monthly.map((item) => item.attendance_pct),
                    backgroundColor: COLORS.green,
                    borderRadius: 6,
                    maxBarThickness: 38,
                  },
                ],
              }}
              options={{ plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } }}
              height={260}
            />
          ) : (
            <p className="py-8 text-center text-sm text-slate-500">No attendance records yet.</p>
          )}
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card
          title="My recommendations"
          subtitle="Personalised and explainable"
          actions={
            <Link to="/student/recommendations" className="text-xs font-semibold text-navy-700 hover:underline">
              View all →
            </Link>
          }
        >
          <ul className="space-y-3">
            {recommendations.slice(0, 3).map((item) => (
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

        <Card
          title="Pending assignments"
          subtitle="Submitted work is detected automatically"
          actions={
            <Link to="/student/performance" className="text-xs font-semibold text-navy-700 hover:underline">
              All work →
            </Link>
          }
        >
          {pending.length ? (
            <ul className="space-y-3">
              {pending.map((assignment) => (
                <li key={assignment.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 p-3">
                  <div>
                    <p className="text-sm font-semibold text-navy-900">{assignment.title}</p>
                    <p className="text-xs text-slate-500">
                      {assignment.subject_name} · due {assignment.due_date}
                    </p>
                  </div>
                  <Badge tone="amber">pending</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-8 text-center text-sm text-slate-500">Everything is submitted. Nice work!</p>
          )}
        </Card>
      </div>
    </div>
  )
}
