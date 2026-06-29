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
    expect(wrapper.text()).toContain('1/7')
  })

  it('uses separate tag-based setup steps and hides timezone', async () => {
    const router = makeRouter()
    router.push('/ledgers')
    await router.isReady()
    const wrapper = mount(LedgerList, { global: { plugins: [router] } })

    await wrapper.find('.create-icon-button').trigger('click')
    await wrapper.find('input[maxlength="50"]').setValue('Home')
    await clickAction(wrapper, '下一步')

    expect(wrapper.text()).toContain('记录模式')
    expect(wrapper.text()).not.toContain('偶尔会记录详细')
    await clickAction(wrapper, '下一步')

    expect(wrapper.text()).toContain('3/7')
    expect(wrapper.text()).toContain('偶尔会记录详细')
    expect(wrapper.text()).toContain('不会记录详细')
    await wrapper.findAll('.choice-tags button').find((button) => button.text() === '偶尔会记录详细')?.trigger('click')
    await clickAction(wrapper, '下一步')

    expect(wrapper.text()).toContain('记录花费对象')
    expect(wrapper.findAll('.choice-tags button').map((button) => button.text())).toEqual(['必须记录', '可以跳过', '不会记录'])
    await clickAction(wrapper, '下一步')
    expect(wrapper.text()).toContain('记录消费必要性')
    await clickAction(wrapper, '下一步')
    expect(wrapper.text()).toContain('记录消费地点')
    await clickAction(wrapper, '下一步')

    expect(wrapper.text()).toContain('7/7')
    expect(wrapper.text()).toContain('默认货币')
    expect(wrapper.text()).not.toContain('时区')
    expect(wrapper.find('input[maxlength="50"]').exists()).toBe(false)
  })

  it('omits the receipt-detail setup step for item mode', async () => {
    const router = makeRouter()
    router.push('/ledgers')
    await router.isReady()
    const wrapper = mount(LedgerList, { global: { plugins: [router] } })

    await wrapper.find('.create-icon-button').trigger('click')
    await wrapper.find('input[maxlength="50"]').setValue('Items')
    await clickAction(wrapper, '下一步')
    await wrapper.findAll('.choice-tags button').find((button) => button.text() === '每种商品一笔')?.trigger('click')

    expect(wrapper.text()).toContain('2/6')
    await clickAction(wrapper, '下一步')
    expect(wrapper.text()).toContain('3/6')
    expect(wrapper.text()).toContain('记录花费对象')
    expect(wrapper.text()).not.toContain('偶尔会记录详细')
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

  it('opens a ledger when clicking the total but keeps settings separate', async () => {
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

    await wrapper.find('.ledger-total').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('ledger-detail'))

    await router.push('/ledgers')
    await wrapper.find('.settings-icon-button').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('ledger-settings'))
  })
})

async function clickAction(wrapper: ReturnType<typeof mount>, text: string) {
  const button = wrapper.findAll('.actions button').find((candidate) => candidate.text() === text)
  expect(button).toBeTruthy()
  await button?.trigger('click')
}
