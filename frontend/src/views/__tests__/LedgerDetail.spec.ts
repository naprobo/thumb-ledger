import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getBudget } from '@/api/budget'
import { listTransactions } from '@/api/transactions'
import LedgerDetail from '@/views/LedgerDetail.vue'

const mockLedgerDisplay = vi.hoisted(() => ({
  locationStepMode: 'optional',
  necessityStepMode: 'required',
  subjectEnabled: true,
  subjectStepMode: 'required',
}))

vi.mock('@/api/ledgers', () => ({
  getLedger: vi.fn(async () => ({
    id: 'ledger-1',
    owner_id: 'user-1',
    name: 'Home',
    entry_mode: 'receipt',
    location_step_mode: mockLedgerDisplay.locationStepMode,
    subject_enabled: mockLedgerDisplay.subjectEnabled,
    subject_step_mode: mockLedgerDisplay.subjectStepMode,
    necessity_step_mode: mockLedgerDisplay.necessityStepMode,
    default_currency_code: 'JPY',
    timezone: 'Asia/Tokyo',
    budget_enabled: true,
    created_at: '',
    updated_at: '',
  })),
  updateLedger: vi.fn(async (_id, payload) => ({
    id: 'ledger-1',
    owner_id: 'user-1',
    name: 'Home',
    entry_mode: 'receipt',
    subject_enabled: true,
    default_currency_code: 'JPY',
    timezone: 'Asia/Tokyo',
    budget_enabled: true,
    created_at: '',
    updated_at: '',
    ...payload,
  })),
  listCategories: vi.fn(async () => [
    { id: 'category-1', ledger_id: 'ledger-1', name: 'category.food', is_system: true, display_order: 0 },
  ]),
  deleteCategory: vi.fn(),
  updateCategory: vi.fn(),
}))

vi.mock('@/api/transactions', () => ({
  listTransactions: vi.fn(async () => ({
    items: [
      {
        id: 'txn-1',
        ledger_id: 'ledger-1',
        entry_mode_snapshot: 'receipt',
        amount: 1200,
        currency_code: 'JPY',
        transaction_date: '2026-06-12',
        necessity: 'essential',
        note: 'Lunch',
        location_name: '駅前カフェ',
        items: [{ id: 'item-1', category_name_snapshot: 'category.food', item_name: 'item.cafe', amount: 1200, currency_code: 'JPY' }],
        transaction_subjects: [{ subject_id: 'subject-1', name: 'subject.self' }],
      },
      {
        id: 'txn-2',
        ledger_id: 'ledger-1',
        entry_mode_snapshot: 'receipt',
        amount: 800,
        currency_code: 'JPY',
        transaction_date: '2026-06-14',
        necessity: 'essential',
        note: '',
        location_name: null,
        items: [{ id: 'item-2', category_name_snapshot: 'category.transport', item_name: 'item.train', amount: 800, currency_code: 'JPY' }],
        transaction_subjects: [{ subject_id: 'subject-1', name: 'subject.self' }],
      },
      {
        id: 'txn-3',
        ledger_id: 'ledger-1',
        entry_mode_snapshot: 'receipt',
        amount: 600,
        currency_code: 'JPY',
        transaction_date: '2026-06-14',
        necessity: 'non-essential',
        note: '',
        location_name: null,
        items: [{ id: 'item-3', category_name_snapshot: 'category.food', item_name: 'item.restaurant', amount: 600, currency_code: 'JPY' }],
        transaction_subjects: [{ subject_id: 'subject-1', name: 'subject.self' }],
      },
    ],
    page: 1,
    page_size: 50,
    total: 3,
    page_total_amounts: { JPY: 2600 },
  })),
  createTransaction: vi.fn(),
}))

const mockBudget = vi.hoisted(() => ({
  warning: 'soft' as 'soft' | 'over',
  percentage: 0.85,
  spent: 8500,
}))

vi.mock('@/api/budget', () => ({
  getBudget: vi.fn(async () => ({
    id: 'budget-1',
    ledger_id: 'ledger-1',
    monthly_total: 10000,
    annual_total: 120000,
    is_enabled: true,
    progress: {
      monthly_spent: mockBudget.spent,
      monthly_total: 10000,
      percentage: mockBudget.percentage,
      warning: mockBudget.warning,
      category_spending: {},
    },
  })),
}))

vi.mock('@/api/preferences', () => ({
  createCustomTag: vi.fn(),
  createSubject: vi.fn(),
  deleteCustomTag: vi.fn(),
  deleteSubject: vi.fn(),
  getPreferredCategories: vi.fn(async () => ['category.food']),
  getItemChoices: vi.fn(async () => [
    { id: null, value: 'item.rice', is_system: true, selection_count: 0, last_selected_at: null },
  ]),
  getLocationChoices: vi.fn(async () => []),
  getSubjectPreferenceDetails: vi.fn(async () => [{ value: '自己', selection_count: 1, last_selected_at: '2099-01-01T00:00:00Z' }]),
  listSubjects: vi.fn(async () => [{ id: 'subject-1', name: '自己' }]),
  updateCustomTag: vi.fn(),
  updateSubject: vi.fn(),
}))

function makeRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/ledgers', name: 'ledger-list', component: { template: '<div />' } },
      { path: '/ledgers/:id', name: 'ledger-detail', component: LedgerDetail },
      { path: '/ledgers/:id/settings', name: 'ledger-settings', component: { template: '<div />' } },
    ],
  })
}

function mountLedgerDetail(router: ReturnType<typeof makeRouter>) {
  return mount(LedgerDetail, { global: { plugins: [router] } })
}

describe('LedgerDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockBudget.warning = 'soft'
    mockBudget.percentage = 0.85
    mockBudget.spent = 8500
    mockLedgerDisplay.locationStepMode = 'optional'
    mockLedgerDisplay.necessityStepMode = 'required'
    mockLedgerDisplay.subjectEnabled = true
    mockLedgerDisplay.subjectStepMode = 'required'
  })

  it('renders prominent transaction action, budget progress, and transaction list', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1')
    await router.isReady()

    const wrapper = mountLedgerDetail(router)
    expect(wrapper.find('.loading-panel').exists()).toBe(true)
    await vi.waitFor(() => expect(wrapper.text()).toContain('Home'))

    expect(wrapper.find('.topbar .record-button').exists()).toBe(true)
    expect(wrapper.find('.budget-panel.soft').exists()).toBe(true)
    expect(wrapper.find('.budget-panel').text()).toContain('本月支出进度（85%）')
    expect(wrapper.text()).not.toContain('消费记录 ·')
    expect(wrapper.text()).toContain('本月合计')
    expect(wrapper.find('.records-section').exists()).toBe(true)
    expect(wrapper.find('.list-panel').exists()).toBe(false)
    expect(wrapper.find('.month-nav strong').text()).toMatch(/年.*月/)
    expect(wrapper.find('.section-heading .v-chip').exists()).toBe(false)
    expect(wrapper.find('.month-title').exists()).toBe(false)
    expect(wrapper.text()).toContain('分类金额占比')
    expect(wrapper.text()).not.toContain('transaction.list')
    expect(wrapper.text()).not.toContain('transaction.monthTotal')
    expect(wrapper.text()).toContain('咖啡')
    expect(wrapper.text()).toContain('Lunch')
    expect(wrapper.text()).toContain('¥1,200')
    expect(wrapper.text()).toContain('¥2,600')
    expect(wrapper.text()).toContain('当天合计 ¥1,400')
    expect(wrapper.text()).not.toContain('1 / 1')
    expect(wrapper.findAll('.month-nav button')).toHaveLength(2)
    expect(wrapper.find('.transaction-list li').classes()).not.toContain('transaction-meta')
    expect(wrapper.findAll('.transaction-name').map((name) => name.text())).toContain('咖啡')
    expect(wrapper.findAll('.transaction-context').map((context) => context.text())).toEqual(['-', '-', '駅前カフェ'])
    expect(wrapper.findAll('.day-group header strong').map((date) => date.text())).toEqual(['2026-06-14', '2026-06-12'])
    expect(wrapper.find('.pie-chart').exists()).toBe(true)
    expect(wrapper.findAll('.chart-legend li')).toHaveLength(2)
    expect(listTransactions).toHaveBeenCalledWith(
      'ledger-1',
      1,
      1000,
      expect.stringMatching(/^\d{4}-\d{2}-01$/),
      expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
    )
    expect(getBudget).toHaveBeenCalledWith('ledger-1', expect.stringMatching(/^\d{4}-\d{2}-01$/))

    await wrapper.findAll('.month-nav button')[0].trigger('click')
    await vi.waitFor(() => expect(getBudget).toHaveBeenCalledTimes(2))
    expect(vi.mocked(getBudget).mock.calls[1][1]).toMatch(/^\d{4}-\d{2}-01$/)
  })

  it('hides ledger chrome and transaction history while recording a transaction', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1')
    await router.isReady()

    const wrapper = mountLedgerDetail(router)
    await vi.waitFor(() => expect(wrapper.text()).toContain('Home'))
    await wrapper.find('.topbar .record-button').trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    expect(wrapper.find('.topbar').exists()).toBe(false)
    expect(wrapper.find('.budget-panel').exists()).toBe(false)
    expect(wrapper.find('.list-panel').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('设置')
    expect(wrapper.text()).not.toContain('消费记录')
    expect(wrapper.text()).not.toContain('Lunch')
  })

  it('renders over-budget progress state', async () => {
    mockBudget.warning = 'over'
    mockBudget.percentage = 1.2
    mockBudget.spent = 12000
    const router = makeRouter()
    router.push('/ledgers/ledger-1')
    await router.isReady()

    const wrapper = mountLedgerDetail(router)
    await vi.waitFor(() => expect(wrapper.find('.budget-panel.over').exists()).toBe(true))

    expect(wrapper.find('.budget-panel.over').exists()).toBe(true)
    expect(wrapper.text()).toMatch(/已超出预算|Over budget|予算を超えました/)
  })

  it('falls back from location to necessity and then subject', async () => {
    mockLedgerDisplay.locationStepMode = 'disabled'
    mockLedgerDisplay.necessityStepMode = 'required'
    const necessityRouter = makeRouter()
    necessityRouter.push('/ledgers/ledger-1')
    await necessityRouter.isReady()
    const necessityWrapper = mountLedgerDetail(necessityRouter)
    await vi.waitFor(() => expect(necessityWrapper.findAll('.transaction-context')).toHaveLength(3))
    expect(necessityWrapper.findAll('.transaction-context').map((context) => context.text())).toEqual([
      '不花不行',
      '其实可以不花',
      '不花不行',
    ])
    necessityWrapper.unmount()

    mockLedgerDisplay.necessityStepMode = 'disabled'
    const subjectRouter = makeRouter()
    subjectRouter.push('/ledgers/ledger-1')
    await subjectRouter.isReady()
    const subjectWrapper = mountLedgerDetail(subjectRouter)
    await vi.waitFor(() => expect(subjectWrapper.findAll('.transaction-context')).toHaveLength(3))
    expect(subjectWrapper.findAll('.transaction-context').map((context) => context.text())).toEqual(['自己', '自己', '自己'])
  })
})
