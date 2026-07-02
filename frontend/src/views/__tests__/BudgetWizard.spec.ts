import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getBudget, saveBudget } from '@/api/budget'
import BudgetWizard from '@/views/BudgetWizard.vue'

vi.mock('@/api/ledgers', () => ({
  listCategories: vi.fn(async () => [
    { id: 'cat-1', ledger_id: 'ledger-1', name: 'category.food', is_system: true, display_order: 0 },
    { id: 'cat-2', ledger_id: 'ledger-1', name: 'category.transport', is_system: true, display_order: 1 },
  ]),
}))

vi.mock('@/api/budget', () => ({
  getBudget: vi.fn(async () => null),
  saveBudget: vi.fn(async () => ({ id: 'budget-1' })),
}))

describe('BudgetWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getBudget).mockResolvedValue(null)
  })

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
    expect((wrapper.find('input[inputmode="numeric"]').element as HTMLInputElement).value).toBe('120000')
  })

  it('starts monthly budget empty and validates non-positive values', async () => {
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

    const input = wrapper.find('input[inputmode="numeric"]')
    expect((input.element as HTMLInputElement).value).toBe('')
    await input.setValue('0')
    await input.trigger('focus')
    expect((input.element as HTMLInputElement).value).toBe('')
    await input.setValue('-1')
    await input.trigger('blur')
    expect(wrapper.text()).toContain('请输入大于零的整数金额')
  })

  it('loads existing monthly and annual budget values', async () => {
    vi.mocked(getBudget).mockResolvedValueOnce({
      id: 'budget-1',
      ledger_id: 'ledger-1',
      monthly_total: 5000,
      annual_total: 65000,
      is_enabled: true,
      categories: [],
      progress: {
        monthly_spent: 0,
        monthly_total: 5000,
        percentage: 0,
        warning: null,
        category_spending: {},
      },
    })
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

    expect((wrapper.find('input[inputmode="numeric"]').element as HTMLInputElement).value).toBe('5000')
    await wrapper.find('form').trigger('submit')
    expect((wrapper.find('input[inputmode="numeric"]').element as HTMLInputElement).value).toBe('65000')
  })

  it('keeps a manually edited annual budget and submits from category choice step', async () => {
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
    await wrapper.find('input[inputmode="numeric"]').setValue('1500')
    await wrapper.find('form').trigger('submit')
    await wrapper.find('section button').trigger('click')

    await vi.waitFor(() => expect(saveBudget).toHaveBeenCalledTimes(1))
    expect(saveBudget).toHaveBeenCalledWith('ledger-1', {
      monthly_total: 100,
      annual_total: 1500,
      categories: undefined,
    })
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
