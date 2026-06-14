import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Users } from 'lucide-react'
import { getExpense } from '../services/endpoints'
import { Spinner, EmptyState, StatusBadge, TypeBadge, SeverityBadge, fmtAmount } from '../components/ui'
import type { ExpenseDetail } from '../types'

export default function ExpenseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [expense, setExpense] = useState<ExpenseDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) getExpense(id).then(setExpense).finally(() => setLoading(false))
  }, [id])

  if (loading) return <Spinner />
  if (!expense) return <EmptyState message="Expense not found." />

  const rawRow = expense.raw_row ? JSON.parse(expense.raw_row) : null

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3">
        <Link to="/expenses" className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition">
          <ArrowLeft size={18} className="text-gray-400" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">{expense.description}</h1>
          <p className="text-gray-400 text-sm mt-0.5">Row {expense.row_number} · {expense.expense_date ?? 'No date'}</p>
        </div>
      </div>

      {/* Core details */}
      <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Amount</p>
            <p className="text-white font-bold text-xl mt-1">{fmtAmount(expense.amount, expense.currency)}</p>
          </div>
          <div>
            <p className="text-gray-500">Paid by</p>
            <p className="text-white font-medium mt-1">{expense.payer?.name ?? <span className="text-red-400 italic">Unknown</span>}</p>
          </div>
          <div>
            <p className="text-gray-500">Type</p>
            <div className="mt-1"><TypeBadge type={expense.expense_type} /></div>
          </div>
          <div>
            <p className="text-gray-500">Status</p>
            <div className="mt-1"><StatusBadge status={expense.status} /></div>
          </div>
          <div>
            <p className="text-gray-500">Split type</p>
            <p className="text-white mt-1 capitalize">{expense.split_type ?? '—'}</p>
          </div>
          <div>
            <p className="text-gray-500">Currency</p>
            <p className="text-white mt-1">{expense.currency ?? '—'}</p>
          </div>
        </div>
      </div>

      {/* Participants */}
      {expense.participants.length > 0 && (
        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-5">
          <h2 className="font-semibold text-white flex items-center gap-2 mb-4">
            <Users size={16} className="text-indigo-400" /> Participants
          </h2>
          <div className="space-y-2">
            {expense.participants.map(p => (
              <div key={p.id} className="flex items-center justify-between text-sm py-2 border-b border-gray-700/50 last:border-0">
                <div className="flex items-center gap-2">
                  <span className="text-gray-300">{p.user.name}</span>
                  {p.user.is_guest && <span className="text-xs text-purple-400 bg-purple-900/30 px-1.5 py-0.5 rounded">Guest</span>}
                </div>
                <span className="text-gray-200 font-medium">
                  {p.share_amount != null ? fmtAmount(p.share_amount, expense.currency) :
                   p.share_percentage != null ? `${p.share_percentage}%` :
                   p.share_weight != null ? `${p.share_weight} share(s)` : '—'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw row */}
      {rawRow && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
          <h2 className="font-semibold text-white mb-3 text-sm">Original CSV Row</h2>
          <div className="space-y-1">
            {Object.entries(rawRow).map(([k, v]) => (
              <div key={k} className="flex gap-3 text-xs font-mono">
                <span className="text-indigo-400 w-28 shrink-0">{k}</span>
                <span className="text-gray-300">{v as string || <span className="text-gray-600 italic">empty</span>}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
