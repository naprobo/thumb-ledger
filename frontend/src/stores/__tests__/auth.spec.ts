import { describe, expect, it, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useAuthStore } from '@/stores/auth'

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('stores and clears access token', () => {
    const auth = useAuthStore()

    auth.setToken('abc')
    expect(auth.isAuthenticated).toBe(true)
    expect(localStorage.getItem('access_token')).toBe('abc')

    auth.clearAuth()
    expect(auth.isAuthenticated).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})

