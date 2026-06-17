import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import App from '@/App.vue'

const authStore = vi.hoisted(() => ({
  isAuthenticated: true,
  isAdmin: true,
  user: { email: 'admin@example.com' },
  updatePreferredLanguage: vi.fn(),
  logout: vi.fn(),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => authStore,
}))

describe('App', () => {
  it('closes the user menu when clicking outside', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [{ path: '/', name: 'home', component: { template: '<div />' } }],
    })
    router.push('/')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    const details = wrapper.find('details').element as HTMLDetailsElement

    details.open = true
    document.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    await wrapper.vm.$nextTick()

    expect(details.open).toBe(false)
  })
})
