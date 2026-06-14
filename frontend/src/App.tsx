import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Sidebar from './components/layout/Sidebar'
import Dashboard from './pages/Dashboard'
import ImportList from './pages/ImportList'
import ImportDetail from './pages/ImportDetail'
import ExpenseList from './pages/ExpenseList'
import ExpenseDetail from './pages/ExpenseDetail'
import AnomalyViewer from './pages/AnomalyViewer'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex min-h-screen bg-gray-950 text-white">
          <Sidebar />
          <main className="flex-1 p-8 overflow-auto">
            <div className="max-w-6xl mx-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/imports" element={<ImportList />} />
                <Route path="/imports/:id" element={<ImportDetail />} />
                <Route path="/expenses" element={<ExpenseList />} />
                <Route path="/expenses/:id" element={<ExpenseDetail />} />
                <Route path="/anomalies" element={<AnomalyViewer />} />
                <Route path="/reports" element={<ImportList />} />
              </Routes>
            </div>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
