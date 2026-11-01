import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../../api/client'
import { Card, ErrorAlert, Loading, PageHeader } from '../../components/ui'

export default function AdminReports() {
  const [students, setStudents] = useState([])
  const [teachers, setTeachers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [studentsResponse, teachersResponse] = await Promise.all([
        api.get('/students', { params: { per_page: 100 } }),
        api.get('/teachers', { params: { per_page: 100 } }),
      ])
      setStudents(studentsResponse.data.items)
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

  return (
    <div>
      <PageHeader
        title="Student & teacher reports"
        subtitle="Open individual academic reports and teaching analytics."
        actions={
          <Link to="/impact" className="btn-ghost">
            Impact report
          </Link>
        }
      />
      <ErrorAlert message={error} onRetry={load} />

      {loading ? (
        <Loading />
      ) : (
        <div className="grid gap-6 xl:grid-cols-2">
          <Card title={`Students (${students.length})`}>
            <div className="-mx-5 max-h-[560px] overflow-auto">
              <table className="min-w-full">
                <thead className="table-head">
                  <tr>
                    <th className="px-4 py-3">Student</th>
                    <th className="px-4 py-3">Roll</th>
                    <th className="px-4 py-3">Class</th>
                    <th className="px-4 py-3 text-right">Report</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((student) => (
                    <tr key={student.id} className="hover:bg-slate-50">
                      <td className="table-cell font-medium text-navy-900">{student.full_name}</td>
                      <td className="table-cell text-slate-600">{student.roll_number}</td>
                      <td className="table-cell text-slate-600">{student.class_name || '—'}</td>
                      <td className="table-cell text-right">
                        <Link
                          to={`/teacher/students/${student.id}`}
                          className="text-xs font-semibold text-navy-700 hover:underline"
                        >
                          Open analytics
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title={`Teachers (${teachers.length})`}>
            <div className="-mx-5 max-h-[560px] overflow-auto">
              <table className="min-w-full">
                <thead className="table-head">
                  <tr>
                    <th className="px-4 py-3">Teacher</th>
                    <th className="px-4 py-3">Code</th>
                    <th className="px-4 py-3">Department</th>
                    <th className="px-4 py-3 text-right">Report</th>
                  </tr>
                </thead>
                <tbody>
                  {teachers.map((teacher) => (
                    <tr key={teacher.id} className="hover:bg-slate-50">
                      <td className="table-cell font-medium text-navy-900">{teacher.full_name}</td>
                      <td className="table-cell text-slate-600">{teacher.employee_code}</td>
                      <td className="table-cell text-slate-600">{teacher.department || '—'}</td>
                      <td className="table-cell text-right">
                        <Link
                          to={`/admin/teachers/${teacher.id}`}
                          className="text-xs font-semibold text-navy-700 hover:underline"
                        >
                          Open report
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
