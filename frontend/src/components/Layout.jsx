import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import Icon from './Icon'

const NAV = {
  admin: [
    { to: '/admin', label: 'Dashboard', icon: 'dashboard', end: true },
    { to: '/admin/users', label: 'User accounts', icon: 'users' },
    { to: '/admin/academics', label: 'Classes & subjects', icon: 'book' },
    { to: '/admin/model', label: 'Model performance', icon: 'brain' },
    { to: '/admin/reports', label: 'Reports', icon: 'book' },
    { to: '/impact', label: 'Educational impact', icon: 'chart' },
    { to: '/profile', label: 'My profile', icon: 'user' },
  ],
  teacher: [
    { to: '/teacher', label: 'Dashboard', icon: 'dashboard', end: true },
    { to: '/teacher/students', label: 'My students', icon: 'users' },
    { to: '/teacher/marks', label: 'Marks entry', icon: 'book' },
    { to: '/teacher/attendance', label: 'Attendance', icon: 'check' },
    { to: '/teacher/classroom', label: 'Classroom log', icon: 'star' },
    { to: '/teacher/feedback', label: 'Feedback insights', icon: 'feedback' },
    { to: '/teacher/recommendations', label: 'Recommendations', icon: 'star' },
    { to: '/impact', label: 'Educational impact', icon: 'chart' },
    { to: '/profile', label: 'My profile', icon: 'user' },
  ],
  student: [
    { to: '/student', label: 'Dashboard', icon: 'dashboard', end: true },
    { to: '/student/performance', label: 'My performance', icon: 'chart' },
    { to: '/student/feedback', label: 'Teaching feedback', icon: 'feedback' },
    { to: '/student/recommendations', label: 'My recommendations', icon: 'star' },
    { to: '/profile', label: 'My profile', icon: 'user' },
  ],
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const links = NAV[user?.role] || []

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const initials = (user?.full_name || 'U')
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 transform bg-navy-900 text-white transition-transform lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center gap-3 border-b border-white/10 px-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-500/20 text-green-400">
            <Icon name="brain" className="h-5 w-5" />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-bold">Pedagogical Impact</p>
            <p className="text-[11px] text-slate-400">Deep Learning Analytics</p>
          </div>
          <button
            type="button"
            className="ml-auto text-slate-400 lg:hidden"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
          >
            <Icon name="close" />
          </button>
        </div>

        <nav className="space-y-1 px-3 py-4">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? 'bg-white/10 text-white'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <Icon name={link.icon} className="h-4 w-4" />
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute inset-x-0 bottom-0 border-t border-white/10 p-4">
          <div className="mb-3 flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-green-500/20 text-xs font-bold text-green-300">
              {initials}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{user?.full_name}</p>
              <p className="text-[11px] uppercase tracking-wide text-slate-400">{user?.role}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white"
          >
            <Icon name="logout" className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {open && (
        <button
          type="button"
          aria-label="Close overlay"
          className="fixed inset-0 z-20 bg-navy-900/40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur lg:px-8">
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
          >
            <Icon name="menu" />
          </button>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-navy-900">
              {user?.role === 'admin'
                ? 'Institution analytics'
                : user?.role === 'teacher'
                  ? 'Teaching & learning workspace'
                  : 'My learning workspace'}
            </p>
            <p className="text-xs text-slate-500">
              {user?.class_name ? `${user.class_name} · Roll ${user.roll_number}` : user?.email}
            </p>
          </div>
          <span className="ml-auto hidden rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700 sm:inline">
            Synthetic demo data
          </span>
        </header>

        <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
        <footer className="border-t border-slate-200 px-4 py-4 text-center text-xs text-slate-400 lg:px-8">
          Pedagogical and Educational Impact Using Deep Learning · BTech project
        </footer>
      </div>
    </div>
  )
}
