import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { describe, expect, it } from 'vitest'

import AuthPages from '@/views/AuthPages.vue'

function makeRouter(path: string) {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/login', name: 'login', component: AuthPages },
      { path: '/register', name: 'register', component: AuthPages },
      { path: '/password-reset', name: 'password-reset', component: AuthPages },
      { path: '/password-reset/confirm', name: 'password-reset-confirm', component: AuthPages },
      { path: '/ledgers', name: 'ledger-list', component: { template: '<div />' } },
    ],
  })
  router.push(path)
  return router
}

async function mountAuth(path: string) {
  const router = makeRouter(path)
  await router.isReady()
  return mount(AuthPages, {
    global: {
      plugins: [router],
    },
  })
}

describe('AuthPages', () => {
  it('renders login form with email and password fields', async () => {
    const wrapper = await mountAuth('/login')

    expect(wrapper.find('input[type="email"]').exists()).toBe(true)
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(wrapper.find('button.primary-button').attributes('style')).toBeUndefined()
  })

  it('renders password reset confirmation fields', async () => {
    const wrapper = await mountAuth('/password-reset/confirm?token=abc')

    expect(wrapper.find('input[autocomplete="one-time-code"]').element).toHaveProperty('value', 'abc')
    expect(wrapper.findAll('input[type="password"]')).toHaveLength(2)
  })
})
