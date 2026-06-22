import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import BudgetWizard from '@/views/BudgetWizard.vue'

vi.mock('@/api/ledgers', () => ({
  listCategories: vi.fn(async () => [
    { id: 'cat-1', ledger_id: 'ledger-1', name: 'category.food', is_system: true, display_order: 0 },
    { id: 'cat-2', ledger_id: 'ledger-1', name: 'category.transport', is_system: true, display_order: 1 },
  ]),
}))

vi.mock('@/api/budget', () => ({
  saveBudget: vi.fn(async () => ({ id: 'budget-1' })),
}))

describe('BudgetWizard', () => {
  it('uses numeric input for each budget amount step', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/ledgers/:id/budget', name: 'budget-wizard', component: BudgetWizard },
        { path: '/ledgers/:id', name: 'ledger-detail', component: { template: '<div />' } },
        { path: '/ledgers/:id/settings', name: 'ledger-settings', component: { template: '<div />' } },
      ],
    })
    router.push('/ledgers/ledger-1/budget')
    await router.isReady()

    const wrapper = mount(BudgetWizard, { global: { plugins: [router] } })

    await vi.waitFor(() => expect(wrapper.find('input[inputmode="numeric"]').exists()).toBe(true))
    await wrapper.find('input[inputmode="numeric"]').setValue('10000')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.find('input[inputmode="numeric"]').exists()).toBe(true)
  })

  it('shows category over-budget warning but keeps save available', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/ledgers/:id/budget', name: 'budget-wizard', component: BudgetWizard },
        { path: '/ledgers/:id', name: 'ledger-detail', component: { template: '<div />' } },
        { path: '/ledgers/:id/settings', name: 'ledger-settings', component: { template: '<div />' } },
      ],
    })
    router.push('/ledgers/ledger-1/budget')
    await router.isReady()
    const wrapper = mount(BudgetWizard, { global: { plugins: [router] } })

    await vi.waitFor(() => expect(wrapper.find('input[inputmode="numeric"]').exists()).toBe(true))
    await wrapper.find('input[inputmode="numeric"]').setValue('100')
    await wrapper.find('form').trigger('submit')
    await wrapper.find('form').trigger('submit')
    await wrapper.find('input[type="checkbox"]').setValue(true)
    await wrapper.find('form').trigger('submit')
    const categoryInputs = wrapper.findAll('input[inputmode="numeric"]')
    await categoryInputs[0].setValue('80')
    await categoryInputs[1].setValue('80')

    expect(wrapper.text()).toContain('分类预算合计已超过月度总预算')
    expect(wrapper.find('.primary-button').attributes('disabled')).toBeUndefined()
  })
})
