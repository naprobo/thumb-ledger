import { apiClient } from '@/api'

export type EntryMode = 'receipt' | 'item'
export type SubjectStepMode = 'required' | 'optional' | 'disabled'
export type NecessityStepMode = 'required' | 'optional' | 'disabled'
export type LocationStepMode = 'required' | 'optional' | 'disabled'

export interface Ledger {
  id: string
  owner_id: string
  name: string
  entry_mode: EntryMode
  receipt_item_enabled?: boolean
  location_step_mode?: LocationStepMode
  subject_enabled: boolean
  subject_step_mode: SubjectStepMode
  necessity_step_mode: NecessityStepMode
  default_currency_code: string
  timezone: string
  budget_enabled: boolean
  total_amounts?: Record<string, number>
  current_month_amounts?: Record<string, number>
  created_at: string
  updated_at: string
}

export interface LedgerCreatePayload {
  name: string
  entry_mode: EntryMode
  receipt_item_enabled: boolean
  location_step_mode: LocationStepMode
  subject_enabled: boolean
  subject_step_mode: SubjectStepMode
  necessity_step_mode: NecessityStepMode
  default_currency_code: string
  timezone: string
  budget_enabled: boolean
}

export interface LedgerUpdatePayload {
  name?: string
  receipt_item_enabled?: boolean
  location_step_mode?: LocationStepMode
  subject_step_mode?: SubjectStepMode
  necessity_step_mode?: NecessityStepMode
  default_currency_code?: string
}

export interface LedgerMember {
  id: string
  ledger_id: string
  user_id: string
  email?: string | null
  nickname?: string | null
  display_name?: string | null
  role: 'read-write' | 'read-only'
  joined_at: string | null
}

export interface ShareRequest {
  id: string
  ledger_id: string
  requester_id: string
  requester_email?: string | null
  requester_nickname?: string | null
  requester_display_name?: string | null
  role: 'read-write' | 'read-only'
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  updated_at: string
}

export interface Category {
  id: string
  ledger_id: string
  name: string
  is_system: boolean
  is_hidden?: boolean
  display_order: number
}

export async function listLedgers(): Promise<Ledger[]> {
  const response = await apiClient.get<Ledger[]>('/ledgers')
  return response.data
}

export async function getLedger(ledgerId: string): Promise<Ledger> {
  const response = await apiClient.get<Ledger>(`/ledgers/${ledgerId}`)
  return response.data
}

export async function createLedger(payload: LedgerCreatePayload): Promise<Ledger> {
  const response = await apiClient.post<Ledger>('/ledgers', payload)
  return response.data
}

export async function updateLedger(ledgerId: string, payload: LedgerUpdatePayload): Promise<Ledger> {
  const response = await apiClient.patch<Ledger>(`/ledgers/${ledgerId}`, payload)
  return response.data
}

export async function deleteLedger(ledgerId: string): Promise<void> {
  await apiClient.delete(`/ledgers/${ledgerId}`)
}

export async function getShareCode(ledgerId: string): Promise<string> {
  const response = await apiClient.get<{ share_code: string }>(`/ledgers/${ledgerId}/share-code`)
  return response.data.share_code
}

export async function listMembers(ledgerId: string): Promise<LedgerMember[]> {
  const response = await apiClient.get<LedgerMember[]>(`/ledgers/${ledgerId}/members`)
  return response.data
}

export async function updateMemberRole(
  ledgerId: string,
  userId: string,
  role: 'read-write' | 'read-only',
): Promise<LedgerMember> {
  const response = await apiClient.patch<LedgerMember>(`/ledgers/${ledgerId}/members/${userId}`, { role })
  return response.data
}

export async function removeMember(ledgerId: string, userId: string): Promise<void> {
  await apiClient.delete(`/ledgers/${ledgerId}/members/${userId}`)
}

export async function createShareRequest(shareCodeOrLedgerId: string, role: 'read-write' | 'read-only'): Promise<ShareRequest> {
  const response = await apiClient.post<ShareRequest>(`/ledgers/${shareCodeOrLedgerId}/share-requests`, { role })
  return response.data
}

export async function listShareRequests(ledgerId: string): Promise<ShareRequest[]> {
  const response = await apiClient.get<ShareRequest[]>(`/ledgers/${ledgerId}/share-requests`)
  return response.data
}

export async function approveShareRequest(ledgerId: string, requestId: string): Promise<ShareRequest> {
  const response = await apiClient.post<ShareRequest>(`/ledgers/${ledgerId}/share-requests/${requestId}/approve`)
  return response.data
}

export async function rejectShareRequest(ledgerId: string, requestId: string): Promise<ShareRequest> {
  const response = await apiClient.post<ShareRequest>(`/ledgers/${ledgerId}/share-requests/${requestId}/reject`)
  return response.data
}

export async function listCategories(ledgerId: string): Promise<Category[]> {
  const response = await apiClient.get<Category[]>(`/ledgers/${ledgerId}/categories`)
  return response.data
}

export async function updateCategory(ledgerId: string, categoryId: string, name: string): Promise<Category> {
  const response = await apiClient.patch<Category>(`/ledgers/${ledgerId}/categories/${categoryId}`, { name })
  return response.data
}

export async function deleteCategory(ledgerId: string, categoryId: string): Promise<void> {
  await apiClient.delete(`/ledgers/${ledgerId}/categories/${categoryId}`)
}
