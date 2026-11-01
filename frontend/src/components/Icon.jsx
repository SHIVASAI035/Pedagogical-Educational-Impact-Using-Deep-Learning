const PATHS = {
  dashboard: 'M3 12l9-9 9 9M5 10v10h5v-6h4v6h5V10',
  users: 'M17 20v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2M9 10a4 4 0 100-8 4 4 0 000 8M21 20v-2a4 4 0 00-3-3.87M16 3.13A4 4 0 0116 11',
  book: 'M4 5a2 2 0 012-2h13v18H6a2 2 0 01-2-2V5zM8 7h8M8 11h8',
  brain: 'M9 3a3 3 0 00-3 3v1a3 3 0 000 6v1a3 3 0 003 3h1V3H9zM15 3a3 3 0 013 3v1a3 3 0 010 6v1a3 3 0 01-3 3h-1V3h1z',
  chart: 'M4 20V10M10 20V4M16 20v-7M22 20H2',
  feedback: 'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z',
  star: 'M12 3l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.8 6.2 20.9l1.1-6.5L2.6 9.8l6.5-.9L12 3z',
  user: 'M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8',
  logout: 'M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9',
  menu: 'M3 6h18M3 12h18M3 18h18',
  close: 'M6 6l12 12M18 6L6 18',
  check: 'M20 6L9 17l-5-5',
  alert: 'M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z',
  arrow: 'M5 12h14M13 6l6 6-6 6',
  clock: 'M12 22a10 10 0 100-20 10 10 0 000 20zM12 6v6l4 2',
  school: 'M3 21h18M5 21V8l7-5 7 5v13M9 21v-6h6v6',
}

export default function Icon({ name, className = 'h-5 w-5', strokeWidth = 1.8 }) {
  const path = PATHS[name] || PATHS.dashboard
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  )
}
