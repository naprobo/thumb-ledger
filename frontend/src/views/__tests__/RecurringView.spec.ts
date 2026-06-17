import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import RecurringView from '@/views/RecurringView.vue'
import { createRecurringTemplate, deleteRecurringTemplate, updateRecurringTemplate } from '@/api/recurring'

vi.mock('@/api/ledgers', () => ({
  getLedger: vi.fn(async () => ({
    id: 'ledger-1',
    owner_id: 'user-1',
    name: 'Home',
    entry_mode: 'receipt',
    subject_enabled: false,
    subject_step_mode: 'disabled',
    necessity_step_mode: 'required',
    default_currency_code: 'JPY',
    timezone: 'Asia/Tokyo',
    budget_enabled: false,
    created_at: '',
    updated_at: '',
  })),
  updateLedger: vi.fn(),
  listCategories: vi.fn(async () => [
    { id: 'cat-1', ledger_id: 'ledger-1', name: 'category.food', is_system: true, display_order: 0 },
    { id: 'cat-2', ledger_id: 'ledger-1', name: 'category.other', is_system: true, display_order: 1 },
  ]),
}))

const templates = vi.hoisted(() => [
  {
    id: 'recurring-1',
    ledger_id: 'ledger-1',
    created_by: 'user-1',
    interval: 'monthly',
    next_run_date: '2026-07-01',
    is_active: true,
    template_data: {
      amount: 50000,
      currency_code: 'JPY',
      necessity: 'essential',
      items: [{ category_name: 'category.other', item_name: '家賃', amount: 50000, currency_code: 'JPY' }],
      subject_ids: [],
    },
    created_at: '',
    updated_at: '',
  },
])

vi.mock('@/api/recurring', () => ({
  listRecurringTemplates: vi.fn(async () => templates),
  createRecurringTemplate: vi.fn(async (_ledgerId, payload) => {
    const created = {
      id: 'recurring-2',
      ledger_id: 'ledger-1',
      created_by: 'user-1',
      is_active: true,
      created_at: '',
      updated_at: '',
      ...payload,
    }
    templates.push(created)
    return created
  }),
  updateRecurringTemplate: vi.fn(async (_ledgerId, recurringId, payload) => {
    const index = templates.findIndex((template) => template.id === recurringId)
    if (index >= 0) {
      templates[index] = { ...templates[index], ...payload }
      return templates[index]
    }
    return { id: recurringId, ledger_id: _ledgerId, created_by: 'user-1', is_active: true, created_at: '', updated_at: '', ...payload }
  }),
  deleteRecurringTemplate: vi.fn(async (_ledgerId, recurringId) => {
    const index = templates.findIndex((template) => template.id === recurringId)
    if (index >= 0) templates.splice(index, 1)
  }),
}))

function makeRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/ledgers/:id/settings', name: 'ledger-settings', component: { template: '<div />' } },
      { path: '/ledgers/:id/recurring', name: 'ledger-recurring', component: RecurringView },
    ],
  })
}

describe('RecurringView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    templates.splice(0, templates.length, {
      id: 'recurring-1',
      ledger_id: 'ledger-1',
      created_by: 'user-1',
      interval: 'monthly',
      next_run_date: '2026-07-01',
      is_active: true,
      template_data: {
        amount: 50000,
        currency_code: 'JPY',
        necessity: 'essential',
        items: [{ category_name: 'category.other', item_name: '家賃', amount: 50000, currency_code: 'JPY' }],
        subject_ids: [],
      },
      created_at: '',
      updated_at: '',
    })
  })

  it('creates, toggles, and deletes recurring templates', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1/recurring')
    await router.isReady()
    const wrapper = mount(RecurringView, { global: { plugins: [router] } })
    await vi.waitFor(() => expect(wrapper.text()).toContain('家賃'))

    await wrapper.find('.section-heading button').trigger('click')
    await wrapper.find('input[type="number"]').setValue('1200')
    await wrapper.find('input[type="date"]').setValue('2026-07-10')
    await wrapper.findAll('select')[0].setValue('weekly')
    await wrapper.findAll('select')[1].setValue('category.food')
    await wrapper.find('input[maxlength="100"]').setValue('米')
    await wrapper.find('form').trigger('submit')

    await vi.waitFor(() => expect(createRecurringTemplate).toHaveBeenCalledTimes(1))
    expect(createRecurringTemplate).toHaveBeenCalledWith('ledger-1', {
      interval: 'weekly',
      next_run_date: '2026-07-10',
      template_data: {
        amount: 1200,
        currency_code: 'JPY',
        necessity: 'essential',
        items: [{ category_name: 'category.food', item_name: '米', amount: 1200, currency_code: 'JPY' }],
        subject_ids: [],
      },
    })

    await wrapper.findAll('.template-list button').find((button) => button.text() === '停用')?.trigger('click')
    await vi.waitFor(() => expect(updateRecurringTemplate).toHaveBeenCalledWith('ledger-1', 'recurring-1', { is_active: false }))

    await wrapper.findAll('.template-list button').find((button) => button.text() === '启用')?.trigger('click')
    await vi.waitFor(() => expect(updateRecurringTemplate).toHaveBeenCalledWith('ledger-1', 'recurring-1', { is_active: true }))

    await wrapper.find('.danger-button').trigger('click')
    await vi.waitFor(() => expect(deleteRecurringTemplate).toHaveBeenCalledWith('ledger-1', 'recurring-1'))
  })

  it('edits an existing recurring template', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1/recurring')
    await router.isReady()
    const wrapper = mount(RecurringView, { global: { plugins: [router] } })
    await vi.waitFor(() => expect(wrapper.text()).toContain('家賃'))

    await wrapper.findAll('.template-list button').find((button) => button.text() === '编辑')?.trigger('click')
    await wrapper.find('input[type="number"]').setValue('60000')
    await wrapper.findAll('select')[0].setValue('yearly')
    await wrapper.find('form').trigger('submit')

    await vi.waitFor(() => expect(updateRecurringTemplate).toHaveBeenCalledTimes(1))
    expect(updateRecurringTemplate).toHaveBeenCalledWith('ledger-1', 'recurring-1', {
      interval: 'yearly',
      next_run_date: '2026-07-01',
      template_data: {
        amount: 60000,
        currency_code: 'JPY',
        necessity: 'essential',
        items: [{ category_name: 'category.other', item_name: '家賃', amount: 60000, currency_code: 'JPY' }],
        subject_ids: [],
      },
    })
  })
})
