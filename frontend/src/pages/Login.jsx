import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { homeFor } from '../auth/ProtectedRoute'
import { useAuth } from '../auth/AuthContext'
import Icon from '../components/Icon'

const DEMO = [
  { role: 'Admin', email: 'admin@school.edu', password: 'Admin@12345' },
  { role: 'Teacher', email: 'teacher1@school.edu', password: 'Teacher@12345' },
  { role: 'Student', email: 'student1001@school.edu', password: 'Student@12345' },
]

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const user = await login(form.email.trim(), form.password)
      navigate(location.state?.from || homeFor(user.role), { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  function fill(demo) {
    setForm({ email: demo.email, password: demo.password })
    setError('')
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="relative hidden flex-col justify-between overflow-hidden bg-navy-900 p-10 text-white lg:flex">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-green-500/10" />
        <div className="absolute -bottom-32 -left-16 h-96 w-96 rounded-full bg-navy-600/40" />
        <div className="relative">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-green-500/20 text-green-400">
              <Icon name="brain" className="h-6 w-6" />
            </span>
            <div>
              <p className="text-lg font-bold">Pedagogical Impact</p>
              <p className="text-xs text-slate-400">Deep Learning Analytics</p>
            </div>
          </div>
          <h1 className="mt-16 max-w-lg text-4xl font-bold leading-tight">
            Understand how teaching shapes learning.
          </h1>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-300">
            A single workspace connecting student performance, teaching effectiveness
            and evidence-based pedagogical insight — powered by a TensorFlow neural
            network.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-slate-300">
            {[
              'Student score prediction with a 7-feature ANN',
              'Multi-indicator teacher effectiveness analysis',
              'NLP sentiment analysis of student feedback',
              'Correlation-aware educational impact reporting',
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <Icon name="check" className="mt-0.5 h-4 w-4 text-green-400" />
                {item}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-slate-500">
          BTech project · Synthetic demonstration data · Local deployment
        </p>
      </section>

      <section className="flex items-center justify-center bg-slate-50 px-4 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy-900 text-green-400">
                <Icon name="brain" className="h-5 w-5" />
              </span>
              <div>
                <p className="font-bold text-navy-900">Pedagogical Impact</p>
                <p className="text-xs text-slate-500">Deep Learning Analytics</p>
              </div>
            </div>
          </div>

          <div className="card p-8">
            <h2 className="text-2xl font-bold text-navy-900">Welcome back</h2>
            <p className="mt-1 text-sm text-slate-500">
              Sign in with your institutional account.
            </p>

            {error && (
              <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
              <div>
                <label className="label" htmlFor="email">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="input"
                  value={form.email}
                  onChange={(event) => setForm({ ...form, email: event.target.value })}
                  placeholder="you@school.edu"
                />
              </div>
              <div>
                <label className="label" htmlFor="password">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  className="input"
                  value={form.password}
                  onChange={(event) => setForm({ ...form, password: event.target.value })}
                  placeholder="••••••••"
                />
              </div>
              <button type="submit" className="btn-primary w-full" disabled={busy}>
                {busy ? 'Signing in…' : 'Sign in'}
              </button>
            </form>

            <p className="mt-5 text-center text-sm text-slate-500">
              New student?{' '}
              <Link to="/register" className="link">
                Create an account
              </Link>
            </p>
          </div>

          <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Demo accounts
            </p>
            <div className="mt-2 space-y-1.5">
              {DEMO.map((demo) => (
                <button
                  key={demo.role}
                  type="button"
                  onClick={() => fill(demo)}
                  className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs hover:bg-slate-50"
                >
                  <span className="font-semibold text-navy-800">{demo.role}</span>
                  <span className="text-slate-500">{demo.email}</span>
                </button>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-slate-400">
              Click a row to fill the form. Password: Admin@12345 / Teacher@12345 /
              Student@12345.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
