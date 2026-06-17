import { apiClient } from '@/api'
import type { Suggestion, SuggestionStatus } from '@/api/suggestions'

export interface AdminUser {
  id: string
  email: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface AdminStats {
  total_users: number
  total_ledgers: number
  total_transactions: number
}

export interface AdminSuggestion extends Suggestion {
  author_email: string
}

export async function listAdminUsers(): Promise<AdminUser[]> {
  const response = await apiClient.get<AdminUser[]>('/admin/users')
  return response.data
}

export async function updateAdminUserStatus(userId: string, isActive: boolean): Promise<AdminUser> {
  const response = await apiClient.patch<AdminUser>(`/admin/users/${userId}/status`, {
    is_active: isActive,
  })
  return response.data
}

export async function deleteAdminUser(userId: string): Promise<void> {
  await apiClient.delete(`/admin/users/${userId}`)
}

export async function getAdminStats(): Promise<AdminStats> {
  const response = await apiClient.get<AdminStats>('/admin/stats')
  return response.data
}

export async function listAdminSuggestions(): Promise<AdminSuggestion[]> {
  const response = await apiClient.get<AdminSuggestion[]>('/admin/suggestions')
  return response.data
}

export async function updateAdminSuggestionStatus(
  suggestionId: string,
  status: SuggestionStatus,
): Promise<AdminSuggestion> {
  const response = await apiClient.patch<AdminSuggestion>(`/admin/suggestions/${suggestionId}/status`, { status })
  return response.data
}
