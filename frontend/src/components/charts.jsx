import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Bar, Doughnut, Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Filler,
  Tooltip,
  Legend,
)

export const COLORS = {
  navy: '#16395a',
  navyLight: '#4f7ea8',
  green: '#10b981',
  greenDark: '#047857',
  amber: '#f59e0b',
  red: '#ef4444',
  slate: '#94a3b8',
  purple: '#7c6fd0',
}

export const SERIES_COLORS = [
  COLORS.navy,
  COLORS.green,
  COLORS.amber,
  COLORS.purple,
  COLORS.navyLight,
  COLORS.red,
]

const base = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { boxWidth: 12, boxHeight: 12, usePointStyle: true, color: '#475569' },
    },
    tooltip: { backgroundColor: '#102a44', padding: 10, cornerRadius: 6 },
  },
}

const scale = {
  grid: { color: 'rgba(148, 163, 184, 0.18)' },
  ticks: { color: '#64748b', font: { size: 11 } },
}

export function LineChart({ data, options = {}, height = 260 }) {
  return (
    <div style={{ height }}>
      <Line
        data={data}
        options={{
          ...base,
          scales: { x: { ...scale, grid: { display: false } }, y: { ...scale, beginAtZero: true } },
          ...options,
        }}
      />
    </div>
  )
}

export function BarChart({ data, options = {}, height = 260, horizontal = false }) {
  return (
    <div style={{ height }}>
      <Bar
        data={data}
        options={{
          ...base,
          indexAxis: horizontal ? 'y' : 'x',
          scales: {
            x: { ...scale, beginAtZero: true, grid: { display: !horizontal } },
            y: { ...scale, beginAtZero: !horizontal, grid: { display: horizontal } },
          },
          ...options,
        }}
      />
    </div>
  )
}

export function DoughnutChart({ data, options = {}, height = 240, cutout = '62%' }) {
  return (
    <div style={{ height }}>
      <Doughnut
        data={data}
        options={{
          ...base,
          cutout,
          plugins: { ...base.plugins, ...(options.plugins || {}) },
          ...options,
        }}
      />
    </div>
  )
}

export function ChartLegend({ items }) {
  return (
    <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
          {item.label}
        </li>
      ))}
    </ul>
  )
}
