export interface PaginatedResponse<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}

export interface ImportReportSummary {
  id: string
  filename: string
  imported_at: string
  total_rows: number
  imported_count: number
  rejected_count: number
  warning_count: number
}

export interface ImportReportDetail extends ImportReportSummary {
  report_json: string | null
}

export interface User {
  id: string
  name: string
  normalized_name: string
  is_guest: boolean
  email?: string
}

export interface ExpenseParticipant {
  id: string
  user: User
  share_amount: number | null
  share_percentage: number | null
  share_weight: number | null
}

export type ExpenseStatus = 'imported' | 'warning' | 'rejected'
export type ExpenseType = 'expense' | 'settlement' | 'refund'
export type SplitType = 'equal' | 'unequal' | 'percentage' | 'share'

export interface ExpenseSummary {
  id: string
  import_id: string
  row_number: number
  expense_date: string | null
  description: string
  amount: number
  currency: string | null
  split_type: SplitType | null
  expense_type: ExpenseType
  status: ExpenseStatus
  payer: User | null
}

export interface ExpenseDetail extends ExpenseSummary {
  participants: ExpenseParticipant[]
  raw_row: string | null
}

export type AnomalySeverity = 'error' | 'warning' | 'info'
export type AnomalyCategory =
  | 'DUPLICATE_EXPENSE'
  | 'MISSING_PAYER'
  | 'MISSING_CURRENCY'
  | 'INVALID_AMOUNT'
  | 'ZERO_AMOUNT'
  | 'AMOUNT_FORMAT_NORMALIZED'
  | 'AMOUNT_PRECISION_NORMALIZED'
  | 'AMBIGUOUS_DATE'
  | 'SETTLEMENT_TRANSACTION'
  | 'REFUND_TRANSACTION'
  | 'UNKNOWN_PARTICIPANT'
  | 'STALE_PARTICIPANT'
  | 'NAME_INCONSISTENCY'
  | 'CONFLICTING_SPLIT_INFO'
  | 'INVALID_PERCENTAGE_SPLIT'
  | 'MISSING_SPLIT_TYPE'

export interface Anomaly {
  id: string
  import_id: string
  expense_id: string | null
  row_number: number
  category: AnomalyCategory
  severity: AnomalySeverity
  reason: string
  resolution: string | null
  created_at: string
}
