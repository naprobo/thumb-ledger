import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Settings from '@/views/Settings.vue'
import { useLedgerStore } from '@/stores/ledgers'
import { updateLedger } from '@/api/ledgers'

vi.mock('@/api/ledgers', () => ({
  getLedger: vi.fn(async () => ({
    id: 'ledger-1',
    owner_id: 'user-1',
    name: 'Home',
    entry_mode: 'receipt',
    subject_enabled: true,
    subject_step_mode: 'required',
    necessity_step_mode: 'required',
    default_currency_code: 'JPY',
    timezone: 'Asia/Tokyo',
    budget_enabled: false,
    created_at: '',
    updated_at: '',
  })),
  updateLedger: vi.fn(async (_id, payload) => ({
    id: 'ledger-1',
    owner_id: 'user-1',
    entry_mode: 'receipt',
    subject_enabled: true,
    default_currency_code: 'JPY',
    timezone: 'Asia/Tokyo',
    budget_enabled: false,
    created_at: '',
    updated_at: '',
    ...payload,
  })),
  deleteLedger: vi.fn(),
  getShareCode: vi.fn(async () => 'share-code'),
  listMembers: vi.fn(async () => []),
  listShareRequests: vi.fn(async () => []),
  approveShareRequest: vi.fn(),
  rejectShareRequest: vi.fn(),
  updateMemberRole: vi.fn(),
  removeMember: vi.fn(),
}))

function makeRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/ledgers', name: 'ledger-list', component: { template: '<div />' } },
      { path: '/ledgers/:id', name: 'ledger-detail', component: { template: '<div />' } },
      { path: '/ledgers/:id/settings', name: 'ledger-settings', component: Settings },
      { path: '/ledgers/:id/members/:userId', name: 'share-member', component: { template: '<div />' } },
      { path: '/ledgers/:id/budget', name: 'budget-wizard', component: { template: '<div />' } },
      { path: '/ledgers/:id/recurring', name: 'ledger-recurring', component: { template: '<div />' } },
    ],
  })
}

describe('Settings', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('loads ledger settings without a ledger-level language selector', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1/settings')
    await router.isReady()
    const wrapper = mount(Settings, { global: { plugins: [router] } })
    await vi.waitFor(() => expect(useLedgerStore().activeLedger?.name).toBe('Home'))

    expect(wrapper.find('input[maxlength="50"]').exists()).toBe(true)
    expect(wrapper.find('select option[value="ja"]').exists()).toBe(false)
    expect(wrapper.find('.back-button').exists()).toBe(true)
    expect(wrapper.find('.setting-toggle span').text()).toBe('可记录消费细节')
    expect(wrapper.find('.setting-toggle input[type="checkbox"]').exists()).toBe(true)
    expect(wrapper.find('.setting-toggle').element.lastElementChild?.tagName).toBe('INPUT')
  })

  it('keeps the compact settings layout order and avoids duplicate settings headings', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1/settings')
    await router.isReady()
    const wrapper = mount(Settings, { global: { plugins: [router] } })
    await vi.waitFor(() => expect(useLedgerStore().activeLedger?.name).toBe('Home'))

    expect(wrapper.findAll('h1').map((heading) => heading.text())).toEqual(['账本设置'])
    expect(wrapper.findAll('h2').map((heading) => heading.text())).not.toContain('账本设置')
    expect(wrapper.find('form .save-row .primary-button').text()).toBe('保存')

    const text = wrapper.text()
    expect(text.indexOf('定期交易')).toBeLessThan(text.indexOf('预算设置'))
    expect(text.indexOf('预算设置')).toBeLessThan(text.indexOf('邀请共享'))
    expect(wrapper.findAll('select').some((select) => select.text().includes('必须输入') && select.text().includes('可跳过') && select.text().includes('关闭'))).toBe(true)
  })

  it('saves ledger name and shows a floating success message', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1/settings')
    await router.isReady()
    const wrapper = mount(Settings, { global: { plugins: [router] } })
    await vi.waitFor(() => expect(useLedgerStore().activeLedger?.name).toBe('Home'))

    await wrapper.find('input[maxlength="50"]').setValue('New Home')
    await wrapper.find('form').trigger('submit')

    await vi.waitFor(() => expect(wrapper.find('.toast.success').exists()).toBe(true))
    expect(updateLedger).toHaveBeenCalledWith('ledger-1', {
      name: 'New Home',
      receipt_item_enabled: false,
      location_step_mode: 'optional',
      subject_step_mode: 'required',
      necessity_step_mode: 'required',
      default_currency_code: 'JPY',
    })
    expect(wrapper.text()).toContain('已保存')
  })

  it('uses an in-app confirmation dialog for deleting a ledger', async () => {
    const router = makeRouter()
    router.push('/ledgers/ledger-1/settings')
    await router.isReady()
    const wrapper = mount(Settings, { global: { plugins: [router] } })
    await vi.waitFor(() => expect(useLedgerStore().activeLedger?.name).toBe('Home'))

    expect(wrapper.find('.modal-backdrop').exists()).toBe(false)
    await wrapper.find('.danger button').trigger('click')

    expect(wrapper.find('.modal-backdrop').exists()).toBe(true)
    expect(wrapper.text()).toContain('确定删除此账本？')
  })
})
