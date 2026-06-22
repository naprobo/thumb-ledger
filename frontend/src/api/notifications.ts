import { apiClient } from '@/api'

export interface NotificationItem {
  id: string
  user_id: string
  type: string
  status: string
  payload: Record<string, unknown> | null
  created_at: string
  read_at: string | null
}

export async function listNotifications(): Promise<NotificationItem[]> {
  const response = await apiClient.get<NotificationItem[]>('/notifications')
  return response.data
}

export async function getUnreadNotificationCount(): Promise<number> {
  const response = await apiClient.get<{ unread_count: number }>('/notifications/unread-count')
  return response.data.unread_count
}

export async function markNotificationRead(notificationId: string): Promise<NotificationItem> {
  const response = await apiClient.post<NotificationItem>(`/notifications/${notificationId}/read`)
  return response.data
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.post('/notifications/read-all')
}
