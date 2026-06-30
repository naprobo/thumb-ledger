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
  is_hidden?: boolean
  display_order?: number
  created_at?: string
}

export interface TagChoice {
  id: string | null
  value: string
  is_system: boolean
  selection_count: number
  last_selected_at: string | null
}

export interface CustomTag {
  id: string
  tag_type: 'item' | 'location'
  name: string
  category: string | null
  is_hidden: boolean
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

export async function getItemChoices(ledgerId: string, category: string): Promise<TagChoice[]> {
  const response = await apiClient.get<{ items: TagChoice[] }>(`/ledgers/${ledgerId}/preferences/items/details`, {
    params: { category },
  })
  return response.data.items
}

export async function getPreferredLocations(ledgerId: string): Promise<string[]> {
  const response = await apiClient.get<PreferenceListResponse>(`/ledgers/${ledgerId}/preferences/locations`)
  return response.data.items
}

export async function getLocationChoices(ledgerId: string): Promise<TagChoice[]> {
  const response = await apiClient.get<{ items: TagChoice[] }>(`/ledgers/${ledgerId}/preferences/locations/details`)
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

export async function updateSubject(ledgerId: string, subjectId: string, name: string): Promise<Subject> {
  const response = await apiClient.patch<Subject>(`/ledgers/${ledgerId}/subjects/${subjectId}`, { name })
  return response.data
}

export async function createCustomTag(
  ledgerId: string,
  payload: { tag_type: 'item' | 'location'; name: string; category?: string },
): Promise<CustomTag> {
  const response = await apiClient.post<CustomTag>(`/ledgers/${ledgerId}/preferences/tags`, payload)
  return response.data
}

export async function updateCustomTag(ledgerId: string, tagId: string, name: string): Promise<CustomTag> {
  const response = await apiClient.patch<CustomTag>(`/ledgers/${ledgerId}/preferences/tags/${tagId}`, { name })
  return response.data
}

export async function deleteCustomTag(ledgerId: string, tagId: string): Promise<void> {
  await apiClient.delete(`/ledgers/${ledgerId}/preferences/tags/${tagId}`)
}
