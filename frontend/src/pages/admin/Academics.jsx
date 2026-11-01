import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { Card, EmptyState, ErrorAlert, Loading, PageHeader } from '../../components/ui'

export default function Academics() {
  const [classes, setClasses] = useState([])
  const [subjects, setSubjects] = useState([])
  const [teachers, setTeachers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [classForm, setClassForm] = useState({ name: '', section: 'A', academic_year: '2025-2026', class_teacher_id: '' })
  const [subjectForm, setSubjectForm] = useState({ name: '', code: '', class_id: '', teacher_id: '' })
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [classesResponse, subjectsResponse, teachersResponse] = await Promise.all([
        api.get('/classes'),
        api.get('/subjects'),
        api.get('/teachers', { params: { per_page: 100 } }),
      ])
      setClasses(classesResponse.data)
      setSubjects(subjectsResponse.data)
      setTeachers(teachersResponse.data.items)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function createClass(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await api.post('/classes', {
        name: classForm.name.trim(),
        section: classForm.section.trim(),
        academic_year: classForm.academic_year.trim(),
        class_teacher_id: classForm.class_teacher_id ? Number(classForm.class_teacher_id) : null,
      })
      setClassForm({ name: '', section: 'A', academic_year: '2025-2026', class_teacher_id: '' })
      setNotice('Class created.')
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function createSubject(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await api.post('/subjects', {
        name: subjectForm.name.trim(),
        code: subjectForm.code.trim(),
        class_id: Number(subjectForm.class_id),
        teacher_id: subjectForm.teacher_id ? Number(subjectForm.teacher_id) : null,
      })
      setSubjectForm({ name: '', code: '', class_id: '', teacher_id: '' })
      setNotice('Subject created.')
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function removeClass(classroom) {
    if (!window.confirm(`Delete ${classroom.name} - ${classroom.section}?`)) return
    try {
      await api.delete(`/classes/${classroom.id}`)
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function removeSubject(subject) {
    if (!window.confirm(`Delete subject ${subject.name}?`)) return
    try {
      await api.delete(`/subjects/${subject.id}`)
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Classes & subjects"
        subtitle="Set up the academic structure that attendance, marks and analytics depend on."
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
        <div className="grid gap-6 xl:grid-cols-2">
          <div className="space-y-6">
            <Card title="Create class">
              <form className="grid gap-3 sm:grid-cols-2" onSubmit={createClass}>
                <div>
                  <label className="label">Class name</label>
                  <input
                    className="input"
                    required
                    placeholder="Grade 9"
                    value={classForm.name}
                    onChange={(event) => setClassForm({ ...classForm, name: event.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Section</label>
                  <input
                    className="input"
                    required
                    value={classForm.section}
                    onChange={(event) => setClassForm({ ...classForm, section: event.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Academic year</label>
                  <input
                    className="input"
                    required
                    value={classForm.academic_year}
                    onChange={(event) => setClassForm({ ...classForm, academic_year: event.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Class teacher</label>
                  <select
                    className="input"
                    value={classForm.class_teacher_id}
                    onChange={(event) => setClassForm({ ...classForm, class_teacher_id: event.target.value })}
                  >
                    <option value="">Unassigned</option>
                    {teachers.map((teacher) => (
                      <option key={teacher.id} value={teacher.id}>
                        {teacher.full_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <button type="submit" className="btn-primary" disabled={busy}>
                    Create class
                  </button>
                </div>
              </form>
            </Card>

            <Card title={`Classes (${classes.length})`}>
              {classes.length ? (
                <div className="-mx-5 overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="table-head">
                      <tr>
                        <th className="px-4 py-3">Class</th>
                        <th className="px-4 py-3">Year</th>
                        <th className="px-4 py-3">Students</th>
                        <th className="px-4 py-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {classes.map((classroom) => (
                        <tr key={classroom.id} className="hover:bg-slate-50">
                          <td className="table-cell font-medium text-navy-900">
                            {classroom.name} - {classroom.section}
                          </td>
                          <td className="table-cell text-slate-600">{classroom.academic_year}</td>
                          <td className="table-cell">{classroom.student_count}</td>
                          <td className="table-cell text-right">
                            <button
                              type="button"
                              className="text-xs font-semibold text-red-600 hover:underline"
                              onClick={() => removeClass(classroom)}
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
                <EmptyState title="No classes yet" message="Create a class to get started." />
              )}
            </Card>
          </div>

          <div className="space-y-6">
            <Card title="Create subject">
              <form className="grid gap-3 sm:grid-cols-2" onSubmit={createSubject}>
                <div>
                  <label className="label">Subject name</label>
                  <input
                    className="input"
                    required
                    placeholder="Mathematics"
                    value={subjectForm.name}
                    onChange={(event) => setSubjectForm({ ...subjectForm, name: event.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Subject code</label>
                  <input
                    className="input"
                    required
                    placeholder="MATH9A"
                    value={subjectForm.code}
                    onChange={(event) => setSubjectForm({ ...subjectForm, code: event.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Class</label>
                  <select
                    className="input"
                    required
                    value={subjectForm.class_id}
                    onChange={(event) => setSubjectForm({ ...subjectForm, class_id: event.target.value })}
                  >
                    <option value="">Select class</option>
                    {classes.map((classroom) => (
                      <option key={classroom.id} value={classroom.id}>
                        {classroom.name} - {classroom.section}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Teacher</label>
                  <select
                    className="input"
                    value={subjectForm.teacher_id}
                    onChange={(event) => setSubjectForm({ ...subjectForm, teacher_id: event.target.value })}
                  >
                    <option value="">Unassigned</option>
                    {teachers.map((teacher) => (
                      <option key={teacher.id} value={teacher.id}>
                        {teacher.full_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <button type="submit" className="btn-primary" disabled={busy}>
                    Create subject
                  </button>
                </div>
              </form>
            </Card>

            <Card title={`Subjects (${subjects.length})`}>
              {subjects.length ? (
                <div className="-mx-5 max-h-[420px] overflow-auto">
                  <table className="min-w-full">
                    <thead className="table-head">
                      <tr>
                        <th className="px-4 py-3">Subject</th>
                        <th className="px-4 py-3">Class</th>
                        <th className="px-4 py-3">Teacher</th>
                        <th className="px-4 py-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {subjects.map((subject) => (
                        <tr key={subject.id} className="hover:bg-slate-50">
                          <td className="table-cell font-medium text-navy-900">
                            {subject.name}
                            <span className="ml-2 text-xs text-slate-400">{subject.code}</span>
                          </td>
                          <td className="table-cell text-slate-600">{subject.class_name}</td>
                          <td className="table-cell text-slate-600">{subject.teacher_name || 'Unassigned'}</td>
                          <td className="table-cell text-right">
                            <button
                              type="button"
                              className="text-xs font-semibold text-red-600 hover:underline"
                              onClick={() => removeSubject(subject)}
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
                <EmptyState title="No subjects yet" message="Create a subject for each class." />
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
