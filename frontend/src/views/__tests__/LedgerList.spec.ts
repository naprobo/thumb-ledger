import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LedgerList from '@/views/LedgerList.vue'

const mockLedgers = vi.hoisted(() => [] as Array<Record<string, unknown>>)

vi.mock('@/api/ledgers', () => ({
  listLedgers: vi.fn(async () => mockLedgers),
  createLedger: vi.fn(),
}))

function makeRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/ledgers', name: 'ledger-list', component: LedgerList },
      { path: '/ledgers/:id', name: 'ledger-detail', component: { template: '<div />' } },
      { path: '/ledgers/:id/settings', name: 'ledger-settings', component: { template: '<div />' } },
      { path: '/ledgers/:id/budget', name: 'budget-wizard', component: { template: '<div />' } },
    ],
  })
}

describe('LedgerList', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockLedgers.splice(0, mockLedgers.length)
  })

  it('renders create wizard controls', async () => {
    const router = makeRouter()
    router.push('/ledgers')
    await router.isReady()
    const wrapper = mount(LedgerList, { global: { plugins: [router] } })

    await wrapper.find('.create-icon-button').trigger('click')

    expect(wrapper.find('input[maxlength="50"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('1/5')
  })

  it('renders existing ledgers with settings action', async () => {
    const router = makeRouter()
    router.push('/ledgers')
    await router.isReady()
    mockLedgers.push({
      id: 'ledger-1',
      owner_id: 'user-1',
      name: 'Home',
      entry_mode: 'receipt',
      subject_enabled: false,
      subject_step_mode: 'disabled',
      necessity_step_mode: 'disabled',
      default_currency_code: 'JPY',
      timezone: 'Asia/Tokyo',
      budget_enabled: false,
      total_amounts: { JPY: 1200 },
      created_at: '',
      updated_at: '',
    })

    const wrapper = mount(LedgerList, { global: { plugins: [router] } })

    await vi.waitFor(() => expect(wrapper.text()).toContain('Home'))
    expect(wrapper.text()).toContain('¥')
    expect(wrapper.find('.settings-icon-button svg').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('设置')
  })
})
