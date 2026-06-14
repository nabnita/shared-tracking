import { useEffect, useState } from 'react'
import { listAnomalies } from '../services/endpoints'
import { Spinner, EmptyState, SeverityBadge } from '../components/ui'
import type { Anomaly, AnomalySeverity, PaginatedResponse } from '../types'

const SEVERITIES: AnomalySeverity[] = ['error', 'warning', 'info']

export default function AnomalyViewer() {
  const [data, setData] = useState<PaginatedResponse<Anomaly> | null>(null)
  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState<AnomalySeverity | undefined>()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listAnomalies({ page, page_size: 30, severity })
      .then(setData)
      .finally(() => setLoading(false))
  }, [page, severity])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Anomaly Viewer</h1>
        <p className="text-gray-400 mt-1">All detected data quality issues across imports</p>
      </div>

      {/* Severity filter */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-400">Filter:</span>
        <button
          onClick={() => { setSeverity(undefined); setPage(1) }}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${!severity ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}`}
        >All</button>
        {SEVERITIES.map(s => (
          <button
            key={s}
            onClick={() => { setSeverity(s); setPage(1) }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition capitalize ${severity === s ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}`}
          >{s}</button>
        ))}
      </div>

      {loading ? <Spinner /> : !data || data.items.length === 0 ? (
        <EmptyState message="No anomalies found." />
      ) : (
        <>
          <div className="text-sm text-gray-500">{data.total} anomal{data.total !== 1 ? 'ies' : 'y'}</div>
          <div className="space-y-2">
            {data.items.map(a => (
              <div key={a.id} className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <div className="shrink-0 pt-0.5">
                    <SeverityBadge severity={a.severity} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono text-gray-500">Row {a.row_number}</span>
                      <span className="text-gray-600">·</span>
                      <span className="text-xs text-indigo-400 font-medium">{a.category.replace(/_/g, ' ')}</span>
                    </div>
                    <p className="text-sm text-gray-300 mt-1.5">{a.reason}</p>
                    {a.resolution && (
                      <p className="text-xs text-gray-500 mt-1 border-l-2 border-gray-700 pl-2 italic">
                        {a.resolution}
                      </p>
                    )}
                  </div>
                  <div className="text-xs text-gray-600 shrink-0 whitespace-nowrap">
                    {new Date(a.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {data.total > 30 && (
            <div className="flex justify-center gap-2 pt-2">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-600 transition">← Prev</button>
              <span className="px-4 py-2 text-gray-400 text-sm">Page {page}</span>
              <button disabled={page * 30 >= data.total} onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-600 transition">Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
