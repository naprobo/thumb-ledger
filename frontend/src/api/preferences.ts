import { apiClient } from '@/api'

export interface PreferenceListResponse {
  items: string[]
}

export interface PreferenceItem {
  value: string
  selection_count: number
  last_selected_at: string | null
}

export interface PreferenceDetailListResponse {
  items: PreferenceItem[]
}

export interface Subject {
  id: string
  ledger_id?: string
  name: string
  is_preset?: boolean
  display_order?: number
  created_at?: string
}

export async function getPreferredCategories(ledgerId: string): Promise<string[]> {
  const response = await apiClient.get<PreferenceListResponse>(`/ledgers/${ledgerId}/preferences/categories`)
  return response.data.items
}

export async function getPreferredItems(ledgerId: string, category: string): Promise<string[]> {
  const response = await apiClient.get<PreferenceListResponse>(`/ledgers/${ledgerId}/preferences/items`, {
    params: { category },
  })
  return response.data.items
}

export async function getPreferredLocations(ledgerId: string): Promise<string[]> {
  const response = await apiClient.get<PreferenceListResponse>(`/ledgers/${ledgerId}/preferences/locations`)
  return response.data.items
}

export async function getPreferredSubjects(ledgerId: string): Promise<string[]> {
  const response = await apiClient.get<PreferenceListResponse>(`/ledgers/${ledgerId}/preferences/subjects`)
  return response.data.items
}

export async function getSubjectPreferenceDetails(ledgerId: string): Promise<PreferenceItem[]> {
  const response = await apiClient.get<PreferenceDetailListResponse>(`/ledgers/${ledgerId}/preferences/subjects/details`)
  return response.data.items
}

export async function listSubjects(ledgerId: string): Promise<Subject[]> {
  const response = await apiClient.get<Subject[]>(`/ledgers/${ledgerId}/subjects`)
  return response.data
}

export async function createSubject(ledgerId: string, name: string): Promise<Subject> {
  const response = await apiClient.post<Subject>(`/ledgers/${ledgerId}/subjects`, { name })
  return response.data
}

export async function deleteSubject(ledgerId: string, subjectId: string): Promise<void> {
  await apiClient.delete(`/ledgers/${ledgerId}/subjects/${subjectId}`)
}
