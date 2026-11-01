import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../../api/client'
import { Badge, Card, ErrorAlert, Loading, PageHeader, RiskBadge } from '../../components/ui'

export default function TeacherStudents() {
  const [students, setStudents] = useState([])
  const [predictions, setPredictions] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [studentsResponse, predictionsResponse] = await Promise.all([
        api.get('/students', { params: { per_page: 100 } }),
        api.get('/dl/predictions'),
      ])
      setStudents(studentsResponse.data.items)
      setPredictions(predictionsResponse.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const latest = useMemo(() => {
    const map = new Map()
    predictions.forEach((prediction) => {
      if (!map.has(prediction.student_id)) map.set(prediction.student_id, prediction)
    })
    return map
  }, [predictions])

  const filtered = students.filter((student) => {
    const query = search.toLowerCase()
    return (
      !query ||
      student.full_name?.toLowerCase().includes(query) ||
      student.roll_number?.toLowerCase().includes(query)
    )
  })

  async function predict(student) {
    setBusyId(student.id)
    setError('')
    try {
      await api.post(`/dl/predict/${student.id}`)
      const { data } = await api.get('/dl/predictions')
      setPredictions(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="My students"
        subtitle="Assigned students with the latest deep-learning score prediction."
        actions={
          <input
            className="input w-64"
            placeholder="Search name or roll number"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        }
      />
      <ErrorAlert message={error} onRetry={load} />

      <Card title={`Students (${filtered.length})`}>
        {loading ? (
          <Loading label="Loading students…" />
        ) : (
          <div className="-mx-5 overflow-x-auto">
            <table className="min-w-full">
              <thead className="table-head">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Roll no.</th>
                  <th className="px-4 py-3">Class</th>
                  <th className="px-4 py-3">Predicted score</th>
                  <th className="px-4 py-3">Risk</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((student) => {
                  const prediction = latest.get(student.id)
                  return (
                    <tr key={student.id} className="hover:bg-slate-50">
                      <td className="table-cell font-medium text-navy-900">{student.full_name}</td>
                      <td className="table-cell text-slate-600">{student.roll_number}</td>
                      <td className="table-cell text-slate-600">{student.class_name || 'Unassigned'}</td>
                      <td className="table-cell font-semibold">
                        {prediction ? `${prediction.predicted_score}%` : <span className="text-slate-400">Not predicted</span>}
                      </td>
                      <td className="table-cell">
                        {prediction ? <RiskBadge level={prediction.risk_level} /> : <Badge>—</Badge>}
                      </td>
                      <td className="table-cell text-right">
                        <div className="flex justify-end gap-3">
                          <button
                            type="button"
                            className="text-xs font-semibold text-green-700 hover:underline disabled:opacity-50"
                            onClick={() => predict(student)}
                            disabled={busyId === student.id}
                          >
                            {busyId === student.id ? 'Predicting…' : 'Predict'}
                          </button>
                          <Link
                            to={`/teacher/students/${student.id}`}
                            className="text-xs font-semibold text-navy-700 hover:underline"
                          >
                            View analytics
                          </Link>
                        </div>
                      </td>
                    </tr>
                  )
                })}
                {!filtered.length && (
                  <tr>
                    <td className="table-cell text-center text-slate-500" colSpan={6}>
                      No students found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-3 text-xs text-slate-500">
        Predictions are generated by an ANN trained on synthetic data. They are a support
        signal for targeted help, not a final academic judgement.
      </p>
    </div>
  )
}
