import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Upload,
  Receipt,
  AlertTriangle,
  FileText,
  ChevronRight,
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/imports', icon: Upload, label: 'Imports' },
  { to: '/expenses', icon: Receipt, label: 'Expenses' },
  { to: '/anomalies', icon: AlertTriangle, label: 'Anomalies' },
  { to: '/reports', icon: FileText, label: 'Reports' },
]

export default function Sidebar() {
  const { pathname } = useLocation()

  return (
    <aside className="w-64 min-h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-800">
        <h1 className="text-xl font-bold text-white tracking-tight">
          💸 <span className="text-indigo-400">Expense</span> Import
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">Spreetail Assessment</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => {
          const active = to === '/' ? pathname === '/' : pathname.startsWith(to)
          return (
            <Link
              key={to}
              to={to}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
                ${active
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'}
              `}
            >
              <Icon size={18} />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight size={14} className="opacity-60" />}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-800">
        <p className="text-xs text-gray-600">v0.1.0 · Production Ready</p>
      </div>
    </aside>
  )
}
