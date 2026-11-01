import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../../api/client'
import { BarChart, COLORS, DoughnutChart } from '../../components/charts'
import {
  Card,
  ErrorAlert,
  Loading,
  PageHeader,
  ProgressBar,
  StatCard,
} from '../../components/ui'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [model, setModel] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [training, setTraining] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [statsResponse, modelResponse] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/model-metrics'),
      ])
      setStats(statsResponse.data)
      setModel(modelResponse.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function trainModel() {
    setTraining(true)
    setError('')
    try {
      await api.post('/dl/train')
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setTraining(false)
    }
  }

  if (loading && !stats) return <Loading label="Loading institution analytics…" />

  const totals = stats?.totals || {}
  const academics = stats?.academics || {}
  const feedback = stats?.feedback || {}
  const risk = stats?.predictions || {}
  const methodologies = stats?.methodology_comparison || []

  return (
    <div>
      <PageHeader
        title="Institution overview"
        subtitle="Student performance, teaching practice and pedagogical impact in one view."
        actions={
          <>
            <Link to="/impact" className="btn-ghost">
              Impact analysis
            </Link>
            <Link to="/admin/model" className="btn-primary">
              Model performance
            </Link>
          </>
        }
      />
      <ErrorAlert message={error} onRetry={load} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Students" value={totals.students} icon="users" hint={`${totals.classes ?? 0} classes · ${totals.subjects ?? 0} subjects`} />
        <StatCard label="Teachers" value={totals.teachers} icon="user" hint={`${totals.users ?? 0} total accounts`} tone="green" />
        <StatCard label="Average academic score" value={academics.average_score != null ? `${academics.average_score}%` : '—'} icon="chart" hint="Mean across all recorded marks" />
        <StatCard label="Average attendance" value={stats?.attendance?.average_pct != null ? `${stats.attendance.average_pct}%` : '—'} icon="check" tone="green" hint={`${stats?.attendance?.records ?? 0} attendance records`} />
        <StatCard label="Learning engagement" value={stats?.engagement?.average_pct != null ? `${stats.engagement.average_pct}%` : '—'} icon="brain" hint={`Participation ${stats?.engagement?.participation_pct ?? '—'}%`} />
        <StatCard label="Model status" value={model?.ready ? 'Trained' : 'Not trained'} icon="brain" tone={model?.ready ? 'green' : 'amber'} hint={model?.ready ? `R² ${model.test_metrics?.r2} · MAE ${model.test_metrics?.mae}` : 'Train the ANN to enable predictions'} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Score distribution" subtitle="Students grouped by average academic percentage" className="xl:col-span-2">
          <BarChart
            data={{
              labels: (academics.score_distribution || []).map((item) => item.band),
              datasets: [
                {
                  label: 'Students',
                  data: (academics.score_distribution || []).map((item) => item.students),
                  backgroundColor: COLORS.navy,
                  borderRadius: 6,
                  maxBarThickness: 42,
                },
              ],
            }}
            options={{ plugins: { legend: { display: false } } }}
            height={280}
          />
        </Card>

        <Card title="Feedback sentiment" subtitle={`${feedback.total ?? 0} responses analysed with NLP`}>
          <DoughnutChart
            data={{
              labels: ['Positive', 'Neutral', 'Negative'],
              datasets: [
                {
                  data: [feedback.positive || 0, feedback.neutral || 0, feedback.negative || 0],
                  backgroundColor: [COLORS.green, COLORS.slate, COLORS.red],
                  borderWidth: 0,
                },
              ],
            }}
          />
          <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="rounded-lg bg-green-50 p-2">
              <p className="font-bold text-green-700">{feedback.positive ?? 0}</p>
              <p className="text-green-700/70">Positive</p>
            </div>
            <div className="rounded-lg bg-slate-100 p-2">
              <p className="font-bold text-slate-600">{feedback.neutral ?? 0}</p>
              <p className="text-slate-500">Neutral</p>
            </div>
            <div className="rounded-lg bg-red-50 p-2">
              <p className="font-bold text-red-700">{feedback.negative ?? 0}</p>
              <p className="text-red-700/70">Negative</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card
          title="Teaching methodology comparison"
          subtitle="Average academic score by dominant methodology"
          className="xl:col-span-2"
          actions={
            <Link to="/impact" className="text-xs font-semibold text-navy-700 hover:underline">
              Full analysis →
            </Link>
          }
        >
          {methodologies.length ? (
            <BarChart
              horizontal
              data={{
                labels: methodologies.map((item) => item.methodology),
                datasets: [
                  {
                    label: 'Average score (%)',
                    data: methodologies.map((item) => item.average_score),
                    backgroundColor: COLORS.green,
                    borderRadius: 6,
                    maxBarThickness: 26,
                  },
                ],
              }}
              options={{
                plugins: { legend: { display: false } },
                scales: { x: { min: 0, max: 100 } },
              }}
              height={280}
            />
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">
              No teaching methodology records yet.
            </p>
          )}
          <p className="mt-3 text-xs text-slate-500">
            Association only — class composition and prior attainment are not controlled.
          </p>
        </Card>

        <Card title="Prediction risk profile" subtitle="Latest stored predictions">
          <DoughnutChart
            data={{
              labels: ['Low risk', 'Moderate', 'High risk'],
              datasets: [
                {
                  data: [risk.low || 0, risk.moderate || 0, risk.high || 0],
                  backgroundColor: [COLORS.green, COLORS.amber, COLORS.red],
                  borderWidth: 0,
                },
              ],
            }}
          />
          <div className="mt-4 space-y-3">
            {[
              ['Low', risk.low || 0, 'green'],
              ['Moderate', risk.moderate || 0, 'amber'],
              ['High', risk.high || 0, 'red'],
            ].map(([label, value, tone]) => (
              <div key={label}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-slate-600">{label} risk</span>
                  <span className="font-semibold text-slate-800">{value}</span>
                </div>
                <ProgressBar value={value} tone={tone} />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card
        className="mt-6"
        title="Model evaluation"
        subtitle="Metrics come from a real held-out test split"
        actions={
          <button type="button" className="btn-green" onClick={trainModel} disabled={training}>
            {training ? 'Training…' : 'Retrain ANN'}
          </button>
        }
      >
        {model?.ready ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ['MAE', model.test_metrics?.mae],
              ['RMSE', model.test_metrics?.rmse],
              ['R²', model.test_metrics?.r2],
              ['Epochs', model.training?.epochs_run],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-slate-200 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                <p className="mt-1 text-xl font-bold text-navy-900">{value ?? '—'}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            No trained model found. Run the training job to enable student score prediction.
          </p>
        )}
      </Card>
    </div>
  )
}
