import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Icon from '../components/Icon'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm: '',
    roll_number: '',
    guardian_name: '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    try {
      await register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
        role: 'student',
        roll_number: form.roll_number.trim(),
        guardian_name: form.guardian_name.trim(),
      })
      navigate('/student', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-lg">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy-900 text-green-400">
            <Icon name="brain" className="h-5 w-5" />
          </span>
          <div>
            <p className="font-bold text-navy-900">Pedagogical Impact</p>
            <p className="text-xs text-slate-500">Student registration</p>
          </div>
        </div>

        <div className="card p-8">
          <h1 className="text-2xl font-bold text-navy-900">Create a student account</h1>
          <p className="mt-1 text-sm text-slate-500">
            Ask your administrator to link you to a class after registration.
          </p>

          {error && (
            <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form className="mt-6 grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
            <div className="sm:col-span-2">
              <label className="label" htmlFor="full_name">
                Full name
              </label>
              <input
                id="full_name"
                required
                className="input"
                value={form.full_name}
                onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="label" htmlFor="email">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                className="input"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
              />
            </div>
            <div>
              <label className="label" htmlFor="roll_number">
                Roll number
              </label>
              <input
                id="roll_number"
                required
                className="input"
                value={form.roll_number}
                onChange={(event) => setForm({ ...form, roll_number: event.target.value })}
              />
            </div>
            <div>
              <label className="label" htmlFor="guardian_name">
                Guardian name (optional)
              </label>
              <input
                id="guardian_name"
                className="input"
                value={form.guardian_name}
                onChange={(event) => setForm({ ...form, guardian_name: event.target.value })}
              />
            </div>
            <div>
              <label className="label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                className="input"
                value={form.password}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
              />
            </div>
            <div>
              <label className="label" htmlFor="confirm">
                Confirm password
              </label>
              <input
                id="confirm"
                type="password"
                required
                minLength={8}
                className="input"
                value={form.confirm}
                onChange={(event) => setForm({ ...form, confirm: event.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <button type="submit" className="btn-primary w-full" disabled={busy}>
                {busy ? 'Creating account…' : 'Create account'}
              </button>
            </div>
          </form>

          <p className="mt-5 text-center text-sm text-slate-500">
            Already registered?{' '}
            <Link to="/login" className="link">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
