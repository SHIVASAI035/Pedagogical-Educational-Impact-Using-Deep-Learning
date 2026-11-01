import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { BarChart, COLORS } from '../../components/charts'
import { Badge, Card, ErrorAlert, Loading, PageHeader, StatCard } from '../../components/ui'

export default function ImpactAnalysis() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const { data: impact } = await api.get('/analytics/impact')
      setData(impact)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading && !data) return <Loading label="Running pedagogical impact analysis…" />
  if (!data) return <ErrorAlert message={error || 'Unable to load impact analysis.'} onRetry={load} />

  const correlations = data.correlations || []
  const comparison = data.methodology_comparison?.methodologies || []
  const anova = data.methodology_comparison?.anova || {}
  const engagement = data.engagement?.engagement_by_methodology || []
  const patterns = data.learning_patterns || {}
  const strongest = [...correlations]
    .filter((item) => item.r !== null)
    .sort((a, b) => Math.abs(b.r) - Math.abs(a.r))[0]

  return (
    <div>
      <PageHeader
        title="Pedagogical & educational impact"
        subtitle="How teaching approaches, engagement and learning behaviour relate to academic outcomes."
      />
      <ErrorAlert message={error} onRetry={load} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Students analysed" value={data.students_analysed} icon="users" hint="With marks and activity data" />
        <StatCard label="Methodologies compared" value={comparison.length} icon="book" tone="green" hint={`${data.engagement?.engagement_by_methodology?.length ?? 0} with observation data`} />
        <StatCard label="Strongest association" value={strongest ? `r = ${strongest.r}` : '—'} icon="chart" tone="amber" hint={strongest?.label || 'Not enough data'} />
        <StatCard label="ANOVA p-value" value={anova.p ?? '—'} icon="brain" hint={anova.p != null && anova.p < 0.05 ? 'Group means differ' : 'No clear difference detected'} />
      </div>

      <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
        <p className="text-sm font-semibold text-amber-900">Correlation is not causation</p>
        <p className="mt-1 text-xs leading-relaxed text-amber-800">{data.causality_statement}</p>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Correlations with academic score" subtitle="Pearson r across students" className="xl:col-span-2">
          <BarChart
            horizontal
            data={{
              labels: correlations.map((item) => item.label),
              datasets: [
                {
                  label: 'Pearson r',
                  data: correlations.map((item) => item.r || 0),
                  backgroundColor: correlations.map((item) =>
                    (item.r || 0) >= 0 ? COLORS.green : COLORS.red,
                  ),
                  borderRadius: 6,
                  maxBarThickness: 24,
                },
              ],
            }}
            options={{ plugins: { legend: { display: false } }, scales: { x: { min: -1, max: 1 } } }}
            height={300}
          />
        </Card>

        <Card title="Association detail">
          <div className="-mx-5 overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead className="table-head">
                <tr>
                  <th className="px-3 py-2">Feature</th>
                  <th className="px-3 py-2">r</th>
                  <th className="px-3 py-2">p</th>
                  <th className="px-3 py-2">n</th>
                </tr>
              </thead>
              <tbody>
                {correlations.map((item) => (
                  <tr key={item.feature} className="hover:bg-slate-50">
                    <td className="table-cell px-3 py-2">{item.label}</td>
                    <td className="table-cell px-3 py-2 font-semibold">{item.r ?? '—'}</td>
                    <td className="table-cell px-3 py-2">{item.p ?? '—'}</td>
                    <td className="table-cell px-3 py-2">{item.n}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">
            Strength labels: very weak &lt;0.2, weak &lt;0.4, moderate &lt;0.6, strong ≥0.6.
          </p>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card title="Outcomes by teaching methodology" subtitle="Average academic score and observed engagement">
          {comparison.length ? (
            <>
              <BarChart
                data={{
                  labels: comparison.map((item) => item.methodology),
                  datasets: [
                    {
                      label: 'Average score (%)',
                      data: comparison.map((item) => item.average_score),
                      backgroundColor: COLORS.navy,
                      borderRadius: 6,
                    },
                    {
                      label: 'Observed engagement (0-10)',
                      data: comparison.map((item) => item.average_engagement),
                      backgroundColor: COLORS.green,
                      borderRadius: 6,
                    },
                  ],
                }}
                options={{ scales: { y: { min: 0, max: 100 } } }}
                height={300}
              />
              <p className="mt-2 text-xs text-slate-500">
                Engagement is measured on a 0–10 observation scale and is plotted on the same
                axis only for visual comparison. ANOVA p = {anova.p ?? '—'}.
              </p>
            </>
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">No methodology data available.</p>
          )}
        </Card>

        <Card title="Engagement by methodology" subtitle="Classroom observation averages">
          {engagement.length ? (
            <BarChart
              horizontal
              data={{
                labels: engagement.map((item) => item.methodology),
                datasets: [
                  {
                    label: 'Average engagement (0-10)',
                    data: engagement.map((item) => item.average_engagement),
                    backgroundColor: COLORS.green,
                    borderRadius: 6,
                    maxBarThickness: 24,
                  },
                ],
              }}
              options={{ plugins: { legend: { display: false } }, scales: { x: { min: 0, max: 10 } } }}
              height={300}
            />
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">No observation data available.</p>
          )}
        </Card>
      </div>

      <Card className="mt-6" title="Learning patterns" subtitle={patterns.method || ''}>
        {patterns.available ? (
          <div className="grid gap-4 lg:grid-cols-3">
            {patterns.clusters.map((cluster) => (
              <div key={cluster.cluster} className="rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-navy-900">{cluster.label}</h3>
                  <Badge tone="navy">{cluster.students} students</Badge>
                </div>
                <dl className="mt-3 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Average score</dt>
                    <dd className="font-semibold">{cluster.average_score}%</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Attendance</dt>
                    <dd className="font-semibold">{cluster.average_attendance}%</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Study hours</dt>
                    <dd className="font-semibold">{cluster.average_study_hours}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Engagement</dt>
                    <dd className="font-semibold">{cluster.average_engagement}%</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Assignment completion</dt>
                    <dd className="font-semibold">{cluster.average_assignment_completion}%</dd>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        ) : (
          <p className="py-6 text-sm text-slate-500">
            {patterns.reason} Currently analysed: {patterns.students_analysed ?? 0} students.
          </p>
        )}
      </Card>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card title="Evidence-based insights">
          <ul className="space-y-3">
            {(data.insights || []).map((insight) => (
              <li key={insight} className="flex gap-3 rounded-lg bg-green-50 p-3 text-xs leading-relaxed text-green-900">
                <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                {insight}
              </li>
            ))}
            {!data.insights?.length && (
              <li className="text-sm text-slate-500">Not enough data to generate insights yet.</li>
            )}
          </ul>
        </Card>

        <Card title="Limitations">
          <ul className="list-disc space-y-2 pl-4 text-xs leading-relaxed text-slate-600">
            {(data.limitations || []).map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
          <div className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">
            <p className="font-semibold text-slate-700">Methodology comparison notes</p>
            <p className="mt-1">{data.methodology_comparison?.note}</p>
          </div>
        </Card>
      </div>
    </div>
  )
}
