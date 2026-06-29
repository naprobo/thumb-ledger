import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getPreferredItems, getPreferredLocations } from '@/api/preferences'
import { updateTransaction } from '@/api/transactions'
import TransactionDetail from '@/views/TransactionDetail.vue'

const transaction = {
  id: 'transaction-1',
  ledger_id: 'ledger-1',
  entry_mode_snapshot: 'receipt',
  amount: 1200,
  currency_code: 'JPY',
  transaction_date: '2026-06-12',
  necessity: 'essential',
  note: null,
  location_name: '駅前スーパー',
  items: [{
    id: 'item-1',
    category_name_snapshot: 'category.dining',
    item_name: 'item.cafe',
    amount: 1200,
    currency_code: 'JPY',
  }],
  transaction_subjects: [],
}

vi.mock('@/api/ledgers', () => ({
  getLedger: vi.fn(async () => ({
    id: 'ledger-1',
    owner_id: 'user-1',
    name: 'Home',
    entry_mode: 'receipt',
    receipt_item_enabled: true,
    location_step_mode: 'optional',
    subject_enabled: false,
    subject_step_mode: 'disabled',
    necessity_step_mode: 'required',
    default_currency_code: 'JPY',
    timezone: 'Asia/Tokyo',
    budget_enabled: false,
    created_at: '',
    updated_at: '',
  })),
  listCategories: vi.fn(async () => [
    { id: 'category-1', ledger_id: 'ledger-1', name: 'category.dining', is_system: true, display_order: 1 },
  ]),
}))

vi.mock('@/api/preferences', () => ({
  getPreferredItems: vi.fn(async () => ['item.restaurant', 'item.cafe']),
  getPreferredLocations: vi.fn(async () => ['駅前スーパー', '会社の近く']),
  listSubjects: vi.fn(async () => []),
}))

vi.mock('@/api/transactions', () => ({
  getTransaction: vi.fn(async () => ({ ...transaction })),
  updateTransaction: vi.fn(async (_ledgerId, _transactionId, payload) => ({ ...transaction, ...payload })),
  deleteTransaction: vi.fn(),
}))

function makeRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/ledgers/:id', name: 'ledger-detail', component: { template: '<div />' } },
      {
        path: '/ledgers/:id/transactions/:transactionId',
        name: 'transaction-detail',
        component: TransactionDetail,
      },
    ],
  })
}

describe('TransactionDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('supports suggested item names and free-form spending locations when editing', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1/transactions/transaction-1')
    await router.isReady()
    const wrapper = mount(TransactionDetail, { global: { plugins: [router] } })
    await vi.waitFor(() => expect(wrapper.text()).toContain('¥1,200'))

    await wrapper.findAll('button').find((button) => button.text() === '编辑')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.findAll('.v-combobox')).toHaveLength(2))
    await vi.waitFor(() => expect(getPreferredItems).toHaveBeenCalledWith('ledger-1', 'category.dining'))
    expect(getPreferredLocations).toHaveBeenCalledWith('ledger-1')

    const comboboxes = wrapper.findAll('.v-combobox input')
    await comboboxes[0].setValue('餐厅')
    await comboboxes[0].trigger('keydown.enter')
    await comboboxes[1].setValue('新宿店')
    await comboboxes[1].trigger('keydown.enter')
    await wrapper.find('.edit-form').trigger('submit')

    await vi.waitFor(() => expect(updateTransaction).toHaveBeenCalledTimes(1))
    expect(vi.mocked(updateTransaction).mock.calls[0][2]).toMatchObject({
      location_name: '新宿店',
      items: [{ item_name: 'item.restaurant' }],
    })
  })
})
