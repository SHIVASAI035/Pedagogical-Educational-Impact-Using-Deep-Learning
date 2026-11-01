import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center">
      <p className="text-sm font-semibold uppercase tracking-wide text-green-600">404</p>
      <h1 className="mt-2 text-3xl font-bold text-navy-900">Page not found</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        The page you are looking for does not exist or you may not have access to it.
      </p>
      <Link to="/" className="btn-primary mt-6">
        Go to my dashboard
      </Link>
    </div>
  )
}
