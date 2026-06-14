import type { AnomalySeverity, ExpenseStatus, ExpenseType } from '../../types'

// ── Severity Badge ────────────────────────────────────────────────────────────
export function SeverityBadge({ severity }: { severity: AnomalySeverity }) {
  const styles = {
    error: 'bg-red-900/50 text-red-300 border border-red-700',
    warning: 'bg-amber-900/50 text-amber-300 border border-amber-700',
    info: 'bg-blue-900/50 text-blue-300 border border-blue-700',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[severity]}`}>
      {severity.toUpperCase()}
    </span>
  )
}

// ── Status Badge ──────────────────────────────────────────────────────────────
export function StatusBadge({ status }: { status: ExpenseStatus }) {
  const styles = {
    imported: 'bg-green-900/50 text-green-300 border border-green-700',
    warning: 'bg-amber-900/50 text-amber-300 border border-amber-700',
    rejected: 'bg-red-900/50 text-red-300 border border-red-700',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

// ── Type Badge ────────────────────────────────────────────────────────────────
export function TypeBadge({ type }: { type: ExpenseType }) {
  const styles = {
    expense: 'bg-indigo-900/50 text-indigo-300 border border-indigo-700',
    settlement: 'bg-purple-900/50 text-purple-300 border border-purple-700',
    refund: 'bg-teal-900/50 text-teal-300 border border-teal-700',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[type]}`}>
      {type.charAt(0).toUpperCase() + type.slice(1)}
    </span>
  )
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
interface StatCardProps {
  label: string
  value: number | string
  sub?: string
  color?: 'default' | 'green' | 'red' | 'amber' | 'indigo'
}

export function StatCard({ label, value, sub, color = 'default' }: StatCardProps) {
  const border = {
    default: 'border-gray-700',
    green: 'border-green-700',
    red: 'border-red-700',
    amber: 'border-amber-700',
    indigo: 'border-indigo-700',
  }[color]

  const valueColor = {
    default: 'text-white',
    green: 'text-green-400',
    red: 'text-red-400',
    amber: 'text-amber-400',
    indigo: 'text-indigo-400',
  }[color]

  return (
    <div className={`bg-gray-800/60 rounded-xl border ${border} p-5 backdrop-blur`}>
      <p className="text-sm text-gray-400 font-medium">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${valueColor}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────────────────────
export function EmptyState({ message = 'No data yet.' }: { message?: string }) {
  return (
    <div className="text-center py-16 text-gray-500">
      <p className="text-lg">{message}</p>
    </div>
  )
}

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner() {
  return (
    <div className="flex justify-center items-center py-16">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

// ── Amount formatter ──────────────────────────────────────────────────────────
export function fmtAmount(amount: number, currency: string | null) {
  const cur = currency ?? 'INR'
  try {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: cur, maximumFractionDigits: 2 }).format(amount)
  } catch {
    return `${cur} ${amount.toFixed(2)}`
  }
}
