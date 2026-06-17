import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/api'
import { setLocale, type SupportedLocale } from '@/i18n'

interface User {
  id: string
  email: string
  is_admin: boolean
  preferred_language: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<User | null>(null)
  const hasFetchedUser = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
  }

  function clearAuth() {
    token.value = null
    user.value = null
    hasFetchedUser.value = false
    localStorage.removeItem('access_token')
  }

  async function login(email: string, password: string): Promise<void> {
    const response = await apiClient.post<{ access_token: string }>('/auth/login', { email, password })
    setToken(response.data.access_token)
    await fetchCurrentUser()
  }

  async function register(email: string, password: string): Promise<void> {
    await apiClient.post('/auth/register', { email, password })
  }

  async function fetchCurrentUser(): Promise<void> {
    try {
      const response = await apiClient.get<User>('/auth/me')
      user.value = response.data
      hasFetchedUser.value = true
      setLocale(response.data.preferred_language as SupportedLocale, false)
    } catch {
      clearAuth()
    }
  }

  async function updatePreferredLanguage(locale: SupportedLocale): Promise<void> {
    setLocale(locale)
    if (!token.value) return
    const response = await apiClient.patch<User>('/auth/me/preferences', {
      preferred_language: locale,
    })
    user.value = response.data
  }

  function logout() {
    clearAuth()
  }

  // 初始化时尝试恢复用户信息
  if (token.value) {
    fetchCurrentUser()
  }

  return {
    token,
    user,
    hasFetchedUser,
    isAuthenticated,
    isAdmin,
    login,
    register,
    fetchCurrentUser,
    updatePreferredLanguage,
    logout,
    clearAuth,
    setToken,
  }
})
