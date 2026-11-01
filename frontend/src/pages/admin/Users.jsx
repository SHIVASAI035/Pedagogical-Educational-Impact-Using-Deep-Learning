import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { Badge, Card, ErrorAlert, Loading, PageHeader } from '../../components/ui'

const EMPTY_FORM = {
  role: 'student',
  full_name: '',
  email: '',
  password: '',
  roll_number: '',
  class_id: '',
  guardian_name: '',
  employee_code: '',
  department: '',
  specialization: '',
}

export default function Users() {
  const [users, setUsers] = useState([])
  const [classes, setClasses] = useState([])
  const [role, setRole] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { per_page: 100 }
      if (role) params.role = role
      if (search) params.search = search
      const [usersResponse, classesResponse] = await Promise.all([
        api.get('/admin/users', { params }),
        api.get('/classes'),
      ])
      setUsers(usersResponse.data.items)
      setClasses(classesResponse.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [role, search])

  useEffect(() => {
    load()
  }, [load])

  async function createAccount(event) {
    event.preventDefault()
    setError('')
    setNotice('')
    setBusy(true)
    try {
      const payload = {
        role: form.role,
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
      }
      if (form.role === 'student') {
        payload.roll_number = form.roll_number.trim()
        payload.guardian_name = form.guardian_name.trim()
        if (form.class_id) payload.class_id = Number(form.class_id)
      }
      if (form.role === 'teacher') {
        payload.employee_code = form.employee_code.trim()
        payload.department = form.department.trim()
        payload.specialization = form.specialization.trim()
      }
      await api.post('/admin/users', payload)
      setNotice('Account created successfully.')
      setForm(EMPTY_FORM)
      setOpen(false)
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function toggleActive(user) {
    setError('')
    try {
      await api.put(`/admin/users/${user.id}`, { is_active: !user.is_active })
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function removeUser(user) {
    if (!window.confirm(`Delete ${user.full_name} (${user.email})? This cannot be undone.`)) return
    setError('')
    try {
      await api.delete(`/admin/users/${user.id}`)
      setNotice('Account deleted.')
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="User accounts"
        subtitle="Create and manage administrator, teacher and student accounts."
        actions={
          <button type="button" className="btn-primary" onClick={() => setOpen(true)}>
            New account
          </button>
        }
      />
      <ErrorAlert message={error} onRetry={load} />
      {notice && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {notice}
        </div>
      )}

      <Card
        title="Accounts"
        subtitle={`${users.length} account(s) shown`}
        actions={
          <div className="flex flex-wrap gap-2">
            <input
              className="input w-48"
              placeholder="Search name or email"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <select className="input w-36" value={role} onChange={(event) => setRole(event.target.value)}>
              <option value="">All roles</option>
              <option value="admin">Admin</option>
              <option value="teacher">Teacher</option>
              <option value="student">Student</option>
            </select>
          </div>
        }
      >
        {loading ? (
          <Loading label="Loading accounts…" />
        ) : (
          <div className="-mx-5 overflow-x-auto">
            <table className="min-w-full">
              <thead className="table-head">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50">
                    <td className="table-cell font-medium text-navy-900">{user.full_name}</td>
                    <td className="table-cell text-slate-600">{user.email}</td>
                    <td className="table-cell">
                      <Badge tone={user.role === 'admin' ? 'navy' : user.role === 'teacher' ? 'green' : 'slate'}>
                        {user.role}
                      </Badge>
                    </td>
                    <td className="table-cell">
                      <Badge tone={user.is_active ? 'green' : 'red'}>
                        {user.is_active ? 'active' : 'inactive'}
                      </Badge>
                    </td>
                    <td className="table-cell text-slate-500">
                      {user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="table-cell text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          className="text-xs font-semibold text-navy-700 hover:underline"
                          onClick={() => toggleActive(user)}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          type="button"
                          className="text-xs font-semibold text-red-600 hover:underline"
                          onClick={() => removeUser(user)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {!users.length && (
                  <tr>
                    <td className="table-cell text-center text-slate-500" colSpan={6}>
                      No accounts match the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {open && (
        <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-navy-900/50 p-4">
          <div className="my-8 w-full max-w-xl rounded-xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <h2 className="text-sm font-bold uppercase tracking-wide text-navy-800">New account</h2>
              <button
                type="button"
                className="text-slate-400 hover:text-slate-700"
                onClick={() => setOpen(false)}
              >
                ✕
              </button>
            </div>
            <form className="grid gap-4 p-5 sm:grid-cols-2" onSubmit={createAccount}>
              <div className="sm:col-span-2">
                <label className="label">Role</label>
                <select
                  className="input"
                  value={form.role}
                  onChange={(event) => setForm({ ...form, role: event.target.value })}
                >
                  <option value="student">Student</option>
                  <option value="teacher">Teacher</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
              <div>
                <label className="label">Full name</label>
                <input
                  className="input"
                  required
                  value={form.full_name}
                  onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                />
              </div>
              <div>
                <label className="label">Email</label>
                <input
                  type="email"
                  className="input"
                  required
                  value={form.email}
                  onChange={(event) => setForm({ ...form, email: event.target.value })}
                />
              </div>
              <div className="sm:col-span-2">
                <label className="label">Temporary password</label>
                <input
                  type="text"
                  className="input"
                  required
                  minLength={8}
                  value={form.password}
                  onChange={(event) => setForm({ ...form, password: event.target.value })}
                  placeholder="At least 8 characters"
                />
              </div>

              {form.role === 'student' && (
                <>
                  <div>
                    <label className="label">Roll number</label>
                    <input
                      className="input"
                      required
                      value={form.roll_number}
                      onChange={(event) => setForm({ ...form, roll_number: event.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Class</label>
                    <select
                      className="input"
                      value={form.class_id}
                      onChange={(event) => setForm({ ...form, class_id: event.target.value })}
                    >
                      <option value="">Unassigned</option>
                      {classes.map((classroom) => (
                        <option key={classroom.id} value={classroom.id}>
                          {classroom.name} - {classroom.section}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="sm:col-span-2">
                    <label className="label">Guardian name</label>
                    <input
                      className="input"
                      value={form.guardian_name}
                      onChange={(event) => setForm({ ...form, guardian_name: event.target.value })}
                    />
                  </div>
                </>
              )}

              {form.role === 'teacher' && (
                <>
                  <div>
                    <label className="label">Employee code</label>
                    <input
                      className="input"
                      required
                      value={form.employee_code}
                      onChange={(event) => setForm({ ...form, employee_code: event.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Department</label>
                    <input
                      className="input"
                      value={form.department}
                      onChange={(event) => setForm({ ...form, department: event.target.value })}
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="label">Specialization</label>
                    <input
                      className="input"
                      value={form.specialization}
                      onChange={(event) => setForm({ ...form, specialization: event.target.value })}
                    />
                  </div>
                </>
              )}

              <div className="mt-2 flex justify-end gap-2 sm:col-span-2">
                <button type="button" className="btn-ghost" onClick={() => setOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={busy}>
                  {busy ? 'Creating…' : 'Create account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
