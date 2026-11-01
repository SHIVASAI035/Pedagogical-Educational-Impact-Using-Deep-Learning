import { useCallback, useEffect, useMemo, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { Card, EmptyState, ErrorAlert, Loading, PageHeader } from '../../components/ui'

function today() {
  return new Date().toISOString().slice(0, 10)
}

export default function MarksEntry() {
  const [students, setStudents] = useState([])
  const [subjects, setSubjects] = useState([])
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({
    student_id: '',
    subject_id: '',
    exam_name: 'Unit Test',
    marks_obtained: '',
    max_marks: 100,
    exam_date: today(),
  })

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [studentsResponse, subjectsResponse, recordsResponse] = await Promise.all([
        api.get('/students', { params: { per_page: 100 } }),
        api.get('/subjects', { params: { mine: 1 } }),
        api.get('/academics/records', { params: { per_page: 100 } }),
      ])
      setStudents(studentsResponse.data.items)
      setSubjects(subjectsResponse.data)
      setRecords(recordsResponse.data.items)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const selectedSubject = useMemo(
    () => subjects.find((subject) => String(subject.id) === String(form.subject_id)),
    [subjects, form.subject_id],
  )
  const eligibleStudents = selectedSubject
    ? students.filter((student) => student.class_id === selectedSubject.class_id)
    : students

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await api.post('/academics/records', {
        ...form,
        student_id: Number(form.student_id),
        subject_id: Number(form.subject_id),
        marks_obtained: Number(form.marks_obtained),
        max_marks: Number(form.max_marks),
      })
      setNotice('Marks recorded.')
      setForm({ ...form, marks_obtained: '' })
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function removeRecord(record) {
    if (!window.confirm(`Delete ${record.exam_name} marks for ${record.student_name}?`)) return
    try {
      await api.delete(`/academics/records/${record.id}`)
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Marks entry"
        subtitle="Record exam marks for students in the subjects you teach."
      />
      <ErrorAlert message={error} onRetry={load} />
      {notice && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {notice}
        </div>
      )}

      {loading ? (
        <Loading />
      ) : (
        <div className="grid gap-6 xl:grid-cols-3">
          <Card title="Add marks" className="xl:col-span-1">
            {subjects.length ? (
              <form className="space-y-3" onSubmit={submit}>
                <div>
                  <label className="label">Subject</label>
                  <select
                    className="input"
                    required
                    value={form.subject_id}
                    onChange={(event) => setForm({ ...form, subject_id: event.target.value, student_id: '' })}
                  >
                    <option value="">Select subject</option>
                    {subjects.map((subject) => (
                      <option key={subject.id} value={subject.id}>
                        {subject.name} · {subject.class_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Student</label>
                  <select
                    className="input"
                    required
                    value={form.student_id}
                    onChange={(event) => setForm({ ...form, student_id: event.target.value })}
                  >
                    <option value="">Select student</option>
                    {eligibleStudents.map((student) => (
                      <option key={student.id} value={student.id}>
                        {student.full_name} ({student.roll_number})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Exam name</label>
                  <input
                    className="input"
                    required
                    value={form.exam_name}
                    onChange={(event) => setForm({ ...form, exam_name: event.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label">Marks</label>
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      className="input"
                      required
                      value={form.marks_obtained}
                      onChange={(event) => setForm({ ...form, marks_obtained: event.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Max marks</label>
                    <input
                      type="number"
                      min="1"
                      className="input"
                      required
                      value={form.max_marks}
                      onChange={(event) => setForm({ ...form, max_marks: event.target.value })}
                    />
                  </div>
                </div>
                <div>
                  <label className="label">Exam date</label>
                  <input
                    type="date"
                    className="input"
                    required
                    value={form.exam_date}
                    onChange={(event) => setForm({ ...form, exam_date: event.target.value })}
                  />
                </div>
                <button type="submit" className="btn-primary w-full" disabled={busy}>
                  {busy ? 'Saving…' : 'Save marks'}
                </button>
              </form>
            ) : (
              <EmptyState
                title="No subjects assigned"
                message="Ask an administrator to assign subjects to your teacher account."
              />
            )}
          </Card>

          <Card title="Recent marks" subtitle="Latest records for your subjects" className="xl:col-span-2">
            {records.length ? (
              <div className="-mx-5 max-h-[560px] overflow-auto">
                <table className="min-w-full">
                  <thead className="table-head">
                    <tr>
                      <th className="px-4 py-3">Student</th>
                      <th className="px-4 py-3">Subject</th>
                      <th className="px-4 py-3">Exam</th>
                      <th className="px-4 py-3">Score</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.id} className="hover:bg-slate-50">
                        <td className="table-cell font-medium text-navy-900">{record.student_name}</td>
                        <td className="table-cell text-slate-600">{record.subject_name}</td>
                        <td className="table-cell text-slate-600">{record.exam_name}</td>
                        <td className="table-cell font-semibold">
                          {record.marks_obtained} / {record.max_marks}
                          <span className="ml-2 text-xs text-slate-500">({record.percentage}%)</span>
                        </td>
                        <td className="table-cell text-slate-500">{record.exam_date}</td>
                        <td className="table-cell text-right">
                          <button
                            type="button"
                            className="text-xs font-semibold text-red-600 hover:underline"
                            onClick={() => removeRecord(record)}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState title="No marks recorded yet" message="Use the form to add the first record." />
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
