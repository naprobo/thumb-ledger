import { describe, expect, it, beforeEach } from 'vitest'
import type { AxiosAdapter } from 'axios'

import { apiClient } from '@/api'

describe('api client', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('targets the versioned backend API prefix', () => {
    expect(apiClient.defaults.baseURL).toBe('/api/v1')
  })

  it('injects bearer token from localStorage', async () => {
    localStorage.setItem('access_token', 'test-token')
    const adapter: AxiosAdapter = async (config) => ({
      data: { authorization: config.headers?.Authorization },
      status: 200,
      statusText: 'OK',
      headers: {},
      config,
    })

    const response = await apiClient.get('/auth/me', { adapter })

    expect(response.data.authorization).toBe('Bearer test-token')
  })

  it('keeps bearer token on business-level forbidden responses', async () => {
    localStorage.setItem('access_token', 'test-token')
    const adapter: AxiosAdapter = async (config) =>
      Promise.reject({
        response: { status: 403, data: { detail: 'Forbidden' } },
        config,
        isAxiosError: true,
      })

    await expect(apiClient.post('/suggestions/id/vote', {}, { adapter })).rejects.toBeTruthy()

    expect(localStorage.getItem('access_token')).toBe('test-token')
  })
})
