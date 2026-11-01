import { useCallback, useEffect, useMemo, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { Card, EmptyState, ErrorAlert, Loading, PageHeader } from '../../components/ui'

function today() {
  return new Date().toISOString().slice(0, 10)
}

const STATUSES = ['present', 'late', 'absent']

export default function AttendanceEntry() {
  const [students, setStudents] = useState([])
  const [subjects, setSubjects] = useState([])
  const [subjectId, setSubjectId] = useState('')
  const [date, setDate] = useState(today())
  const [statuses, setStatuses] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [studentsResponse, subjectsResponse] = await Promise.all([
        api.get('/students', { params: { per_page: 100 } }),
        api.get('/subjects', { params: { mine: 1 } }),
      ])
      setStudents(studentsResponse.data.items)
      setSubjects(subjectsResponse.data)
      if (!subjectId && subjectsResponse.data.length) {
        setSubjectId(String(subjectsResponse.data[0].id))
      }
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [subjectId])

  useEffect(() => {
    load()
  }, [load])

  const selectedSubject = useMemo(
    () => subjects.find((subject) => String(subject.id) === String(subjectId)),
    [subjects, subjectId],
  )
  const roster = useMemo(
    () => (selectedSubject ? students.filter((student) => student.class_id === selectedSubject.class_id) : []),
    [students, selectedSubject],
  )

  useEffect(() => {
    let cancelled = false
    async function fetchExisting() {
      if (!subjectId) return
      try {
        const { data } = await api.get('/academics/attendance', {
          params: { subject_id: subjectId, date_from: date, date_to: date },
        })
        if (cancelled) return
        const map = {}
        data.forEach((row) => {
          map[row.student_id] = row.status
        })
        setStatuses(map)
      } catch {
        if (!cancelled) setStatuses({})
      }
    }
    fetchExisting()
    return () => {
      cancelled = true
    }
  }, [subjectId, date])

  function setStatus(studentId, status) {
    setStatuses((current) => ({ ...current, [studentId]: status }))
  }

  async function save() {
    if (!roster.length) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const records = roster.map((student) => ({
        student_id: student.id,
        subject_id: Number(subjectId),
        date,
        status: statuses[student.id] || 'present',
      }))
      const { data } = await api.post('/academics/attendance', { records })
      setNotice(`Attendance saved (${data.created} created, ${data.updated} updated).`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Attendance"
        subtitle="Record daily attendance for a class. Existing entries are updated automatically."
      />
      <ErrorAlert message={error} onRetry={load} />
      {notice && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {notice}
        </div>
      )}

      {loading ? (
        <Loading />
      ) : !subjects.length ? (
        <EmptyState title="No subjects assigned" message="Ask an administrator to assign subjects to you." />
      ) : (
        <Card
          title="Class register"
          subtitle={selectedSubject ? `${selectedSubject.name} · ${selectedSubject.class_name}` : ''}
          actions={
            <div className="flex flex-wrap gap-2">
              <select className="input w-52" value={subjectId} onChange={(event) => setSubjectId(event.target.value)}>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name} · {subject.class_name}
                  </option>
                ))}
              </select>
              <input type="date" className="input w-40" value={date} onChange={(event) => setDate(event.target.value)} />
            </div>
          }
        >
          {roster.length ? (
            <>
              <div className="-mx-5 overflow-x-auto">
                <table className="min-w-full">
                  <thead className="table-head">
                    <tr>
                      <th className="px-4 py-3">Student</th>
                      <th className="px-4 py-3">Roll no.</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {roster.map((student) => (
                      <tr key={student.id} className="hover:bg-slate-50">
                        <td className="table-cell font-medium text-navy-900">{student.full_name}</td>
                        <td className="table-cell text-slate-600">{student.roll_number}</td>
                        <td className="table-cell">
                          <div className="flex gap-1">
                            {STATUSES.map((status) => {
                              const active = (statuses[student.id] || 'present') === status
                              const tone =
                                status === 'present'
                                  ? 'bg-green-600'
                                  : status === 'late'
                                    ? 'bg-amber-500'
                                    : 'bg-red-600'
                              return (
                                <button
                                  key={status}
                                  type="button"
                                  onClick={() => setStatus(student.id, status)}
                                  className={`rounded-md px-3 py-1 text-xs font-semibold capitalize transition ${
                                    active ? `${tone} text-white` : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                                  }`}
                                >
                                  {status}
                                </button>
                              )
                            })}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-5 flex items-center justify-between">
                <p className="text-xs text-slate-500">
                  {roster.length} students · saved entries for {date} are pre-selected.
                </p>
                <button type="button" className="btn-primary" onClick={save} disabled={busy}>
                  {busy ? 'Saving…' : 'Save attendance'}
                </button>
              </div>
            </>
          ) : (
            <EmptyState title="No students in this class" message="Assign students to the class first." />
          )}
        </Card>
      )}
    </div>
  )
}
