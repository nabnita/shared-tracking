import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, AlertCircle, CheckCircle, XCircle, Clock } from 'lucide-react'
import { listImports, listAnomalies, listExpenses } from '../services/endpoints'
import { StatCard, Spinner, EmptyState } from '../components/ui'
import UploadZone from '../components/ui/UploadZone'
import type { ImportReportSummary } from '../types'

export default function Dashboard() {
  const [imports, setImports] = useState<ImportReportSummary[]>([])
  const [stats, setStats] = useState({ totalExpenses: 0, totalAnomalies: 0, importCount: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([listImports(1, 5), listAnomalies(), listExpenses()])
      .then(([imp, anomalies, expenses]) => {
        setImports(imp.items)
        setStats({ totalExpenses: expenses.total, totalAnomalies: anomalies.total, importCount: imp.total })
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Overview of your expense imports and data quality</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Imports" value={stats.importCount} color="indigo" />
        <StatCard label="Total Expenses" value={stats.totalExpenses} color="default" />
        <StatCard label="Anomalies Detected" value={stats.totalAnomalies}
          color={stats.totalAnomalies > 0 ? 'amber' : 'green'} />
        <StatCard label="Data Quality" value={stats.totalExpenses > 0
          ? `${Math.round((1 - stats.totalAnomalies / Math.max(stats.totalExpenses, 1)) * 100)}%`
          : '—'} color="green" />
      </div>

      {/* Upload */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Import New CSV</h2>
        <UploadZone />
      </div>

      {/* Recent imports */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white">Recent Imports</h2>
          <Link to="/imports" className="text-sm text-indigo-400 hover:text-indigo-300">View all →</Link>
        </div>

        {imports.length === 0
          ? <EmptyState message="No imports yet. Upload a CSV above to get started." />
          : (
            <div className="space-y-2">
              {imports.map(imp => (
                <Link
                  key={imp.id}
                  to={`/imports/${imp.id}`}
                  className="flex items-center gap-4 bg-gray-800/60 border border-gray-700 rounded-xl p-4 hover:border-indigo-600 transition-all group"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{imp.filename}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {new Date(imp.imported_at).toLocaleString()} · {imp.total_rows} rows
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs shrink-0">
                    <span className="flex items-center gap-1 text-green-400">
                      <CheckCircle size={12} /> {imp.imported_count}
                    </span>
                    <span className="flex items-center gap-1 text-amber-400">
                      <Clock size={12} /> {imp.warning_count}
                    </span>
                    <span className="flex items-center gap-1 text-red-400">
                      <XCircle size={12} /> {imp.rejected_count}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
      </div>
    </div>
  )
}
