import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle, Clock, XCircle, Upload } from 'lucide-react'
import { listImports } from '../services/endpoints'
import { Spinner, EmptyState, StatCard } from '../components/ui'
import type { ImportReportSummary, PaginatedResponse } from '../types'

export default function ImportList() {
  const [data, setData] = useState<PaginatedResponse<ImportReportSummary> | null>(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listImports(page, 20).then(setData).finally(() => setLoading(false))
  }, [page])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Import History</h1>
          <p className="text-gray-400 mt-1">All CSV import runs and their outcomes</p>
        </div>
        <Link
          to="/"
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg transition"
        >
          <Upload size={16} /> New Import
        </Link>
      </div>

      {loading ? <Spinner /> : !data || data.items.length === 0 ? (
        <EmptyState message="No imports yet." />
      ) : (
        <>
          <div className="text-sm text-gray-500">{data.total} total import{data.total !== 1 ? 's' : ''}</div>
          <div className="space-y-3">
            {data.items.map(imp => (
              <Link
                key={imp.id}
                to={`/imports/${imp.id}`}
                className="flex items-center gap-5 bg-gray-800/60 border border-gray-700 rounded-xl p-5 hover:border-indigo-600 transition-all group"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white truncate">{imp.filename}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Imported {new Date(imp.imported_at).toLocaleString()} · {imp.total_rows} rows
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm shrink-0">
                  <div className="text-center">
                    <p className="text-green-400 font-bold text-lg">{imp.imported_count}</p>
                    <p className="text-gray-500 text-xs">Imported</p>
                  </div>
                  <div className="text-center">
                    <p className="text-amber-400 font-bold text-lg">{imp.warning_count}</p>
                    <p className="text-gray-500 text-xs">Warnings</p>
                  </div>
                  <div className="text-center">
                    <p className="text-red-400 font-bold text-lg">{imp.rejected_count}</p>
                    <p className="text-gray-500 text-xs">Rejected</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {data.total > 20 && (
            <div className="flex justify-center gap-2 pt-4">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-600 transition"
              >← Prev</button>
              <span className="px-4 py-2 text-gray-400 text-sm">Page {page}</span>
              <button
                disabled={page * 20 >= data.total}
                onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-600 transition"
              >Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
