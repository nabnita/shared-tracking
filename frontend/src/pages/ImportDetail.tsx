import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Download } from 'lucide-react'
import { getImport, listAnomalies } from '../services/endpoints'
import { StatCard, Spinner, SeverityBadge, EmptyState } from '../components/ui'
import type { ImportReportDetail, Anomaly } from '../types'

export default function ImportDetail() {
  const { id } = useParams<{ id: string }>()
  const [report, setReport] = useState<ImportReportDetail | null>(null)
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    Promise.all([getImport(id), listAnomalies({ import_id: id, page_size: 100 })])
      .then(([r, a]) => { setReport(r); setAnomalies(a.items) })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <Spinner />
  if (!report) return <EmptyState message="Import not found." />

  const parsedReport = report.report_json ? JSON.parse(report.report_json) : null

  const downloadReport = () => {
    const blob = new Blob([JSON.stringify(parsedReport, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `import-report-${id?.slice(0, 8)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/imports" className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition mt-1">
          <ArrowLeft size={18} className="text-gray-400" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">{report.filename}</h1>
          <p className="text-gray-400 text-sm mt-1">
            Imported on {new Date(report.imported_at).toLocaleString()}
          </p>
        </div>
        <button
          onClick={downloadReport}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg transition"
        >
          <Download size={16} /> Download Report
        </button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Rows" value={report.total_rows} />
        <StatCard label="Imported" value={report.imported_count} color="green" />
        <StatCard label="Warnings" value={report.warning_count} color="amber" />
        <StatCard label="Rejected" value={report.rejected_count} color="red" />
      </div>

      {/* Anomaly breakdown */}
      {parsedReport?.anomaly_breakdown && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-4">By Severity</h3>
            <div className="space-y-2">
              {Object.entries(parsedReport.anomaly_breakdown.by_severity).map(([sev, count]) => (
                <div key={sev} className="flex items-center justify-between">
                  <SeverityBadge severity={sev as any} />
                  <span className="text-gray-300 font-medium">{count as number}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-4">By Category</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {Object.entries(parsedReport.anomaly_breakdown.by_category).map(([cat, count]) => (
                <div key={cat} className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">{cat.replace(/_/g, ' ')}</span>
                  <span className="text-gray-300 font-medium">{count as number}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Anomaly list */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          Anomalies ({anomalies.length})
        </h2>
        {anomalies.length === 0 ? (
          <EmptyState message="No anomalies detected — clean import!" />
        ) : (
          <div className="space-y-2">
            {anomalies.map(a => (
              <div key={a.id} className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <SeverityBadge severity={a.severity} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 font-mono">Row {a.row_number}</span>
                      <span className="text-xs text-gray-600">·</span>
                      <span className="text-xs text-indigo-400">{a.category.replace(/_/g, ' ')}</span>
                    </div>
                    <p className="text-sm text-gray-300 mt-1">{a.reason}</p>
                    {a.resolution && (
                      <p className="text-xs text-gray-500 mt-1 italic">→ {a.resolution}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Row actions */}
      {parsedReport?.row_actions && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Row-by-Row Actions</h2>
          <div className="overflow-x-auto rounded-xl border border-gray-700">
            <table className="w-full text-sm">
              <thead className="bg-gray-800 text-gray-400">
                <tr>
                  <th className="px-4 py-3 text-left">Row</th>
                  <th className="px-4 py-3 text-left">Action</th>
                  <th className="px-4 py-3 text-left">Reason</th>
                </tr>
              </thead>
              <tbody>
                {parsedReport.row_actions.map((ra: any) => (
                  <tr key={ra.row} className="border-t border-gray-700/50 hover:bg-gray-800/40">
                    <td className="px-4 py-3 text-gray-400 font-mono">{ra.row}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                        ra.action === 'IMPORTED' ? 'text-green-400 bg-green-900/30' :
                        ra.action === 'REJECTED' ? 'text-red-400 bg-red-900/30' :
                        'text-amber-400 bg-amber-900/30'
                      }`}>{ra.action}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{ra.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
