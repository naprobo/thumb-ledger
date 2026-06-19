import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import SummaryView from '@/views/SummaryView.vue'

vi.mock('@/api/transactions', () => ({
  getLedgerSummary: vi.fn(async () => ({
    categories: [{ key: 'category.food', currency_code: 'JPY', amount: 1200 }],
    subjects: [{ key: 'subject.self', currency_code: 'JPY', amount: 1200 }],
    necessities: [{ key: 'essential', currency_code: 'JPY', amount: 1200 }],
  })),
}))

describe('SummaryView', () => {
  it('renders grouped totals without mixing currencies', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/ledgers/:id/summary', name: 'ledger-summary', component: SummaryView },
        { path: '/ledgers/:id', name: 'ledger-detail', component: { template: '<div />' } },
      ],
    })
    router.push('/ledgers/ledger-1/summary')
    await router.isReady()

    const wrapper = mount(SummaryView, { global: { plugins: [router] } })
    await vi.waitFor(() => expect(wrapper.text()).toContain('食品饮料'))

    expect(wrapper.text()).toContain('1,200 JPY')
    expect(wrapper.text()).toContain('自己')
  })
})
