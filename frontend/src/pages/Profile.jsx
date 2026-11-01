import { useState } from 'react'
import api, { errorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Card, ErrorAlert, PageHeader } from '../components/ui'

export default function Profile() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    guardian_name: '',
    department: user?.department || '',
    specialization: '',
  })
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '' })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function saveProfile(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setBusy(true)
    try {
      const payload = { full_name: form.full_name }
      if (user.role === 'student') payload.guardian_name = form.guardian_name
      if (user.role === 'teacher') {
        payload.department = form.department
        payload.specialization = form.specialization
      }
      const { data } = await api.put('/auth/profile', payload)
      const merged = { ...user, ...data }
      localStorage.setItem('pe_user', JSON.stringify(merged))
      setUser(merged)
      setMessage('Profile updated.')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function changePassword(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setBusy(true)
    try {
      await api.post('/auth/change-password', passwords)
      setPasswords({ current_password: '', new_password: '' })
      setMessage('Password changed successfully.')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="My profile" subtitle="Manage your account details and password." />
      <ErrorAlert message={error} />
      {message && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {message}
        </div>
      )}

      <div className="space-y-6">
        <Card title="Account details">
          <dl className="mb-5 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Email</dt>
              <dd className="font-medium text-slate-800">{user.email}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Role</dt>
              <dd className="font-medium capitalize text-slate-800">{user.role}</dd>
            </div>
            {user.roll_number && (
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Roll number</dt>
                <dd className="font-medium text-slate-800">{user.roll_number}</dd>
              </div>
            )}
            {user.class_name && (
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Class</dt>
                <dd className="font-medium text-slate-800">{user.class_name}</dd>
              </div>
            )}
            {user.employee_code && (
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Employee code</dt>
                <dd className="font-medium text-slate-800">{user.employee_code}</dd>
              </div>
            )}
          </dl>

          <form className="grid gap-4 sm:grid-cols-2" onSubmit={saveProfile}>
            <div className="sm:col-span-2">
              <label className="label">Full name</label>
              <input
                className="input"
                value={form.full_name}
                onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                required
              />
            </div>
            {user.role === 'student' && (
              <div className="sm:col-span-2">
                <label className="label">Guardian name</label>
                <input
                  className="input"
                  value={form.guardian_name}
                  onChange={(event) => setForm({ ...form, guardian_name: event.target.value })}
                  placeholder="Optional"
                />
              </div>
            )}
            {user.role === 'teacher' && (
              <>
                <div>
                  <label className="label">Department</label>
                  <input
                    className="input"
                    value={form.department}
                    onChange={(event) => setForm({ ...form, department: event.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Specialization</label>
                  <input
                    className="input"
                    value={form.specialization}
                    onChange={(event) => setForm({ ...form, specialization: event.target.value })}
                  />
                </div>
              </>
            )}
            <div className="sm:col-span-2">
              <button type="submit" className="btn-primary" disabled={busy}>
                Save changes
              </button>
            </div>
          </form>
        </Card>

        <Card title="Change password">
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={changePassword}>
            <div>
              <label className="label">Current password</label>
              <input
                type="password"
                className="input"
                required
                value={passwords.current_password}
                onChange={(event) =>
                  setPasswords({ ...passwords, current_password: event.target.value })
                }
              />
            </div>
            <div>
              <label className="label">New password</label>
              <input
                type="password"
                className="input"
                required
                minLength={8}
                value={passwords.new_password}
                onChange={(event) =>
                  setPasswords({ ...passwords, new_password: event.target.value })
                }
              />
            </div>
            <div className="sm:col-span-2">
              <button type="submit" className="btn-ghost" disabled={busy}>
                Update password
              </button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  )
}
