import { apiClient } from '@/api'

export type Necessity = 'essential' | 'non-essential'

export interface TransactionItemPayload {
  category_name?: string
  item_name?: string
  item_tag_id?: string
  amount: number
  currency_code?: string
}

export interface TransactionCreatePayload {
  amount: number
  currency_code?: string
  transaction_date?: string
  necessity?: Necessity
  note?: string
  location_name?: string
  location_tag_id?: string
  items?: TransactionItemPayload[]
  subject_ids?: string[]
}

export interface TransactionUpdatePayload {
  amount?: number
  currency_code?: string
  transaction_date?: string
  necessity?: Necessity
  note?: string | null
  location_name?: string | null
  location_tag_id?: string | null
  items?: TransactionItemPayload[]
  subject_ids?: string[]
}

export interface Transaction {
  id: string
  ledger_id: string
  entry_mode_snapshot: string | null
  amount: number
  currency_code: string
  transaction_date: string
  necessity: string
  note: string | null
  location_name: string | null
  location_tag_id?: string | null
  items: Array<{
    id: string
    category_name_snapshot: string
    item_name: string | null
    item_tag_id?: string | null
    amount: number
    currency_code: string
  }>
  transaction_subjects: Array<{ subject_id: string; name?: string }>
  budget_warning?: 'soft' | 'over' | null
}

export interface TransactionListResponse {
  items: Transaction[]
  page: number
  page_size: number
  total: number
  page_total_amounts: Record<string, number>
}

export interface SummaryGroup {
  key: string
  currency_code: string
  amount: number
}

export interface LedgerSummary {
  categories: SummaryGroup[]
  subjects: SummaryGroup[]
  necessities: SummaryGroup[]
}

export async function createTransaction(ledgerId: string, payload: TransactionCreatePayload): Promise<Transaction> {
  const response = await apiClient.post<Transaction>(`/ledgers/${ledgerId}/transactions`, payload)
  return response.data
}

export async function getTransaction(ledgerId: string, transactionId: string): Promise<Transaction> {
  const response = await apiClient.get<Transaction>(`/ledgers/${ledgerId}/transactions/${transactionId}`)
  return response.data
}

export async function updateTransaction(
  ledgerId: string,
  transactionId: string,
  payload: TransactionUpdatePayload,
): Promise<Transaction> {
  const response = await apiClient.patch<Transaction>(`/ledgers/${ledgerId}/transactions/${transactionId}`, payload)
  return response.data
}

export async function deleteTransaction(ledgerId: string, transactionId: string): Promise<void> {
  await apiClient.delete(`/ledgers/${ledgerId}/transactions/${transactionId}`)
}

export async function listTransactions(
  ledgerId: string,
  page = 1,
  pageSize = 50,
  startDate?: string,
  endDate?: string,
): Promise<TransactionListResponse> {
  const response = await apiClient.get<TransactionListResponse>(`/ledgers/${ledgerId}/transactions`, {
    params: { page, page_size: pageSize, start_date: startDate, end_date: endDate },
  })
  return response.data
}

export async function getLedgerSummary(
  ledgerId: string,
  params: { time_range: 'week' | 'month' | 'year' | 'custom'; start_date?: string; end_date?: string },
): Promise<LedgerSummary> {
  const response = await apiClient.get<LedgerSummary>(`/ledgers/${ledgerId}/summary`, { params })
  return response.data
}
