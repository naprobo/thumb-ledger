import { apiClient } from '@/api'
import type { Necessity, TransactionCreatePayload } from '@/api/transactions'

export type RecurringInterval = 'daily' | 'weekly' | 'monthly' | 'yearly'

export interface RecurringTemplateData extends Omit<TransactionCreatePayload, 'transaction_date'> {
  amount: number
  currency_code?: string
  necessity?: Necessity
}

export interface RecurringTemplate {
  id: string
  ledger_id: string
  created_by: string | null
  interval: RecurringInterval
  next_run_date: string
  is_active: boolean
  template_data: RecurringTemplateData
  created_at: string
  updated_at: string
}

export interface RecurringCreatePayload {
  interval: RecurringInterval
  next_run_date: string
  template_data: RecurringTemplateData
}

export type RecurringUpdatePayload = Partial<RecurringCreatePayload> & {
  is_active?: boolean
}

export async function listRecurringTemplates(ledgerId: string): Promise<RecurringTemplate[]> {
  const response = await apiClient.get<RecurringTemplate[]>(`/ledgers/${ledgerId}/recurring`)
  return response.data
}

export async function createRecurringTemplate(
  ledgerId: string,
  payload: RecurringCreatePayload,
): Promise<RecurringTemplate> {
  const response = await apiClient.post<RecurringTemplate>(`/ledgers/${ledgerId}/recurring`, payload)
  return response.data
}

export async function updateRecurringTemplate(
  ledgerId: string,
  recurringId: string,
  payload: RecurringUpdatePayload,
): Promise<RecurringTemplate> {
  const response = await apiClient.patch<RecurringTemplate>(`/ledgers/${ledgerId}/recurring/${recurringId}`, payload)
  return response.data
}

export async function deleteRecurringTemplate(ledgerId: string, recurringId: string): Promise<void> {
  await apiClient.delete(`/ledgers/${ledgerId}/recurring/${recurringId}`)
}
