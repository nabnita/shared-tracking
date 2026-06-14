import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listExpenses } from '../services/endpoints'
import { Spinner, EmptyState, StatusBadge, TypeBadge, fmtAmount } from '../components/ui'
import type { ExpenseSummary, PaginatedResponse, ExpenseStatus } from '../types'

const STATUS_OPTIONS: ExpenseStatus[] = ['imported', 'warning', 'rejected']

export default function ExpenseList() {
  const [data, setData] = useState<PaginatedResponse<ExpenseSummary> | null>(null)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<ExpenseStatus | undefined>()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listExpenses({ page, page_size: 25, status: statusFilter })
      .then(setData)
      .finally(() => setLoading(false))
  }, [page, statusFilter])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Expenses</h1>
        <p className="text-gray-400 mt-1">All imported expense records</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-400">Filter by status:</span>
        <button
          onClick={() => { setStatusFilter(undefined); setPage(1) }}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${!statusFilter ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}`}
        >All</button>
        {STATUS_OPTIONS.map(s => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1) }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition capitalize ${statusFilter === s ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}`}
          >{s}</button>
        ))}
      </div>

      {loading ? <Spinner /> : !data || data.items.length === 0 ? (
        <EmptyState message="No expenses found." />
      ) : (
        <>
          <div className="text-sm text-gray-500">{data.total} expense{data.total !== 1 ? 's' : ''}</div>
          <div className="overflow-x-auto rounded-xl border border-gray-700">
            <table className="w-full text-sm">
              <thead className="bg-gray-800 text-gray-400">
                <tr>
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-left">Description</th>
                  <th className="px-4 py-3 text-left">Payer</th>
                  <th className="px-4 py-3 text-right">Amount</th>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map(exp => (
                  <tr key={exp.id} className="border-t border-gray-700/50 hover:bg-gray-800/40">
                    <td className="px-4 py-3 text-gray-400 font-mono text-xs whitespace-nowrap">
                      {exp.expense_date ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/expenses/${exp.id}`} className="text-indigo-400 hover:text-indigo-300 hover:underline">
                        {exp.description}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{exp.payer?.name ?? <span className="text-red-400 italic">Unknown</span>}</td>
                    <td className="px-4 py-3 text-right text-gray-200 font-medium whitespace-nowrap">
                      {fmtAmount(exp.amount, exp.currency)}
                    </td>
                    <td className="px-4 py-3"><TypeBadge type={exp.expense_type} /></td>
                    <td className="px-4 py-3"><StatusBadge status={exp.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.total > 25 && (
            <div className="flex justify-center gap-2 pt-2">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-600 transition">← Prev</button>
              <span className="px-4 py-2 text-gray-400 text-sm">Page {page}</span>
              <button disabled={page * 25 >= data.total} onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-600 transition">Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
