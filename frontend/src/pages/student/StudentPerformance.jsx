import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { BarChart, COLORS, LineChart } from '../../components/charts'
import { Badge, Card, EmptyState, ErrorAlert, Loading, PageHeader, StatCard } from '../../components/ui'

export default function StudentPerformance() {
  const [data, setData] = useState(null)
  const [records, setRecords] = useState([])
  const [assignments, setAssignments] = useState([])
  const [submissions, setSubmissions] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [analytics, recordList, assignmentList, submissionList] = await Promise.all([
        api.get('/analytics/student/me'),
        api.get('/academics/records', { params: { per_page: 100 } }),
        api.get('/academics/assignments', { params: { per_page: 50 } }),
        api.get('/academics/submissions', { params: { per_page: 50 } }),
      ])
      setData(analytics.data)
      setRecords(recordList.data.items)
      setAssignments(assignmentList.data.items)
      setSubmissions(submissionList.data.items)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function submitAssignment(assignment) {
    setBusyId(assignment.id)
    setError('')
    try {
      await api.post('/academics/submissions', { assignment_id: assignment.id })
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusyId(null)
    }
  }

  if (loading && !data) return <Loading label="Loading your performance…" />
  if (!data) return <ErrorAlert message={error || 'Unable to load performance.'} onRetry={load} />

  const academics = data.academics || {}
  const attendance = data.attendance || {}
  const subjects = academics.subjects || []
  const trend = academics.trend || []
  const submissionMap = new Map(submissions.map((row) => [row.assignment_id, row]))

  return (
    <div>
      <PageHeader
        title="My performance"
        subtitle="Marks, attendance, assignments and learning progress in one place."
      />
      <ErrorAlert message={error} onRetry={load} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Average score" value={`${academics.average_pct ?? 0}%`} icon="chart" hint="Across all exams" />
        <StatCard label="Attendance" value={`${attendance.overall_pct ?? 0}%`} icon="check" tone="green" hint={`${attendance.present ?? 0} present · ${attendance.late ?? 0} late`} />
        <StatCard label="Assignments" value={`${data.assignments?.completion_pct ?? 0}%`} icon="book" hint={`${data.assignments?.submitted ?? 0}/${data.assignments?.total ?? 0} submitted`} />
        <StatCard label="Study hours/day" value={data.learning?.study_hours_per_day ?? '—'} icon="clock" tone="amber" hint={`Engagement ${data.learning?.engagement_pct ?? 0}%`} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Progress over time" className="xl:col-span-2">
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
                  },
                ],
              }}
              options={{ scales: { y: { min: 0, max: 100 } } }}
              height={280}
            />
          ) : (
            <EmptyState title="No marks yet" message="Your exam results will appear here." />
          )}
        </Card>

        <Card title="Subject averages">
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
                    maxBarThickness: 22,
                  },
                ],
              }}
              options={{ plugins: { legend: { display: false } }, scales: { x: { min: 0, max: 100 } } }}
              height={280}
            />
          ) : (
            <EmptyState title="No subject data" />
          )}
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card title="Exam records" subtitle={`${records.length} records`}>
          {records.length ? (
            <div className="-mx-5 max-h-[420px] overflow-auto">
              <table className="min-w-full">
                <thead className="table-head">
                  <tr>
                    <th className="px-4 py-3">Subject</th>
                    <th className="px-4 py-3">Exam</th>
                    <th className="px-4 py-3">Marks</th>
                    <th className="px-4 py-3">%</th>
                    <th className="px-4 py-3">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => (
                    <tr key={record.id} className="hover:bg-slate-50">
                      <td className="table-cell font-medium text-navy-900">{record.subject_name}</td>
                      <td className="table-cell text-slate-600">{record.exam_name}</td>
                      <td className="table-cell">
                        {record.marks_obtained}/{record.max_marks}
                      </td>
                      <td className="table-cell font-semibold">{record.percentage}%</td>
                      <td className="table-cell text-slate-500">{record.exam_date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState title="No exam records" />
          )}
        </Card>

        <Card title="Assignments" subtitle="Submit work directly from here">
          {assignments.length ? (
            <ul className="space-y-3">
              {assignments.map((assignment) => {
                const submission = submissionMap.get(assignment.id)
                const done = submission && submission.status !== 'pending'
                return (
                  <li key={assignment.id} className="rounded-lg border border-slate-200 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-navy-900">{assignment.title}</p>
                        <p className="text-xs text-slate-500">
                          {assignment.subject_name} · due {assignment.due_date}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge tone={done ? 'green' : 'amber'}>{done ? submission.status : 'pending'}</Badge>
                        {!done && (
                          <button
                            type="button"
                            className="text-xs font-semibold text-green-700 hover:underline disabled:opacity-50"
                            onClick={() => submitAssignment(assignment)}
                            disabled={busyId === assignment.id}
                          >
                            {busyId === assignment.id ? 'Submitting…' : 'Mark submitted'}
                          </button>
                        )}
                      </div>
                    </div>
                  </li>
                )
              })}
            </ul>
          ) : (
            <EmptyState title="No assignments yet" />
          )}
        </Card>
      </div>
    </div>
  )
}
