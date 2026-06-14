import { apiClient } from './api'
import type {
  PaginatedResponse,
  ImportReportSummary,
  ImportReportDetail,
  ExpenseSummary,
  ExpenseDetail,
  Anomaly,
  ExpenseStatus,
  ExpenseType,
  AnomalySeverity,
  AnomalyCategory,
} from '../types'

// ── Imports ──────────────────────────────────────────────────────────────────

export const uploadCSV = async (file: File): Promise<ImportReportDetail> => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<ImportReportDetail>('/imports', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const listImports = async (page = 1, pageSize = 20): Promise<PaginatedResponse<ImportReportSummary>> => {
  const { data } = await apiClient.get<PaginatedResponse<ImportReportSummary>>(
    `/imports?page=${page}&page_size=${pageSize}`
  )
  return data
}

export const getImport = async (id: string): Promise<ImportReportDetail> => {
  const { data } = await apiClient.get<ImportReportDetail>(`/imports/${id}`)
  return data
}

// ── Expenses ──────────────────────────────────────────────────────────────────

interface ExpenseFilters {
  import_id?: string
  currency?: string
  status?: ExpenseStatus
  expense_type?: ExpenseType
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export const listExpenses = async (filters: ExpenseFilters = {}): Promise<PaginatedResponse<ExpenseSummary>> => {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => { if (v !== undefined) params.set(k, String(v)) })
  const { data } = await apiClient.get<PaginatedResponse<ExpenseSummary>>(`/expenses?${params}`)
  return data
}

export const getExpense = async (id: string): Promise<ExpenseDetail> => {
  const { data } = await apiClient.get<ExpenseDetail>(`/expenses/${id}`)
  return data
}

// ── Anomalies ─────────────────────────────────────────────────────────────────

interface AnomalyFilters {
  import_id?: string
  severity?: AnomalySeverity
  category?: AnomalyCategory
  page?: number
  page_size?: number
}

export const listAnomalies = async (filters: AnomalyFilters = {}): Promise<PaginatedResponse<Anomaly>> => {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => { if (v !== undefined) params.set(k, String(v)) })
  const { data } = await apiClient.get<PaginatedResponse<Anomaly>>(`/anomalies?${params}`)
  return data
}
