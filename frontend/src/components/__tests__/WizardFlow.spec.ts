import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Ledger } from '@/api/ledgers'
import { createSubject, deleteSubject } from '@/api/preferences'
import { createTransaction } from '@/api/transactions'
import WizardFlow from '@/components/WizardFlow.vue'
import { buildWizardSteps } from '@/components/wizard/types'

const preferredItems = vi.hoisted(() => ['item.rice', 'item.eggs'])
const preferredLocations = vi.hoisted(() => ['駅前スーパー'])

vi.mock('@/api/ledgers', () => ({
  listCategories: vi.fn(async () => [
    { id: 'category-1', ledger_id: 'ledger-1', name: 'category.food', is_system: true, display_order: 0 },
    { id: 'category-2', ledger_id: 'ledger-1', name: 'category.transport', is_system: true, display_order: 1 },
  ]),
  updateCategory: vi.fn(),
  deleteCategory: vi.fn(),
}))

vi.mock('@/api/preferences', () => ({
  createCustomTag: vi.fn(async (_ledgerId, payload) => {
    const values = payload.tag_type === 'item' ? preferredItems : preferredLocations
    if (!values.includes(payload.name)) values.unshift(payload.name)
    return {
      id: `${payload.tag_type}-custom`,
      tag_type: payload.tag_type,
      name: payload.name,
      category: payload.category || null,
      is_hidden: false,
    }
  }),
  createSubject: vi.fn(async (_ledgerId, name) => ({ id: 'subject-custom', name, is_preset: false })),
  deleteCustomTag: vi.fn(async () => undefined),
  deleteSubject: vi.fn(async () => undefined),
  updateCustomTag: vi.fn(),
  updateSubject: vi.fn(),
  getPreferredCategories: vi.fn(async () => ['category.food', 'category.transport']),
  getItemChoices: vi.fn(async () => preferredItems.map((value) => ({
    id: value.startsWith('item.') ? null : 'item-custom',
    value,
    is_system: value.startsWith('item.'),
    selection_count: 0,
    last_selected_at: null,
  }))),
  getLocationChoices: vi.fn(async () => preferredLocations.map((value) => ({
    id: 'location-custom',
    value,
    is_system: false,
    selection_count: 0,
    last_selected_at: null,
  }))),
  getSubjectPreferenceDetails: vi.fn(async () => [
    { value: 'subject.self', selection_count: 4, last_selected_at: '2099-01-01T00:00:00Z' },
    { value: 'subject.mom', selection_count: 0, last_selected_at: null },
    { value: '家族', selection_count: 0, last_selected_at: null },
  ]),
  listSubjects: vi.fn(async () => [
    { id: 'subject-1', name: 'subject.self', is_preset: true },
    { id: 'subject-2', name: 'subject.mom', is_preset: true },
    { id: 'subject-custom-existing', name: '家族', is_preset: false },
  ]),
}))

vi.mock('@/api/transactions', () => ({
  createTransaction: vi.fn(async (_ledgerId, payload) => {
    const itemName = payload.items?.[0]?.item_name
    if (itemName && !preferredItems.includes(itemName)) {
      preferredItems.unshift(itemName)
    }
    return { id: 'transaction-1' }
  }),
}))

function ledger(overrides: Partial<Ledger> = {}): Ledger {
  return {
    id: 'ledger-1',
    owner_id: 'user-1',
    name: 'Home',
    entry_mode: 'item',
    subject_enabled: true,
    subject_step_mode: 'required',
    necessity_step_mode: 'required',
    location_step_mode: 'disabled',
    default_currency_code: 'JPY',
    timezone: 'Asia/Tokyo',
    budget_enabled: false,
    created_at: '',
    updated_at: '',
    ...overrides,
  }
}

describe('WizardFlow', () => {
  const originalVibrate = navigator.vibrate

  beforeEach(() => {
    vi.clearAllMocks()
    preferredItems.splice(0, preferredItems.length, 'item.rice', 'item.eggs')
    preferredLocations.splice(0, preferredLocations.length, '駅前スーパー')
  })

  afterEach(() => {
    vi.useRealTimers()
    if (originalVibrate) {
      Object.defineProperty(navigator, 'vibrate', { value: originalVibrate, configurable: true })
    } else {
      Reflect.deleteProperty(navigator, 'vibrate')
    }
  })

  it('builds full item-mode step order from ledger settings', () => {
    expect(buildWizardSteps(ledger())).toEqual(['amount', 'category', 'item', 'necessity', 'subject'])
  })

  it('places location after spending name and before necessity when enabled', () => {
    expect(buildWizardSteps(ledger({ location_step_mode: 'optional' }))).toEqual([
      'amount',
      'category',
      'item',
      'location',
      'necessity',
      'subject',
    ])
  })

  it('adds an optional detail step to receipt mode when configured', () => {
    expect(
      buildWizardSteps(
        ledger({
          entry_mode: 'receipt',
          receipt_item_enabled: true,
          location_step_mode: 'disabled',
          necessity_step_mode: 'disabled',
          subject_enabled: false,
          subject_step_mode: 'disabled',
        }),
      ),
    ).toEqual(['amount', 'category', 'item'])
  })

  it('omits item, necessity, and subject steps when disabled by ledger settings', () => {
    expect(
      buildWizardSteps(
        ledger({
          entry_mode: 'receipt',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'disabled',
        }),
      ),
    ).toEqual(['amount', 'category'])
  })

  it('keeps receipt-mode category selection before necessity', () => {
    expect(
      buildWizardSteps(
        ledger({
          entry_mode: 'receipt',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'required',
        }),
      ),
    ).toEqual(['amount', 'category', 'necessity'])
  })

  it('renders a custom amount keypad instead of relying on the system numeric keyboard', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 5, 17, 9, 0, 0))
    const wrapper = mount(WizardFlow, {
      props: { ledger: ledger() },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    expect(wrapper.find('.wizard-titlebar h2').text()).toBe('输入金额')
    expect(wrapper.text()).toContain('2026/6/17(今天)')
    expect(wrapper.find('.date-side-button').text()).toBe('昨天')
    expect(wrapper.find('input[inputmode="numeric"]').exists()).toBe(false)
    expect(wrapper.findAll('.keypad button').map((button) => button.text())).toEqual([
      '1',
      '2',
      '3',
      '4',
      '5',
      '6',
      '7',
      '8',
      '9',
      '清除',
      '0',
      '.',
      'OK',
    ])
  })

  it('requests haptic feedback when tapping the amount keypad', async () => {
    const vibrate = vi.fn()
    Object.defineProperty(navigator, 'vibrate', { value: vibrate, configurable: true })
    const wrapper = mount(WizardFlow, {
      props: { ledger: ledger() },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')

    expect(vibrate).toHaveBeenCalledWith(8)
  })

  it('lets the amount step choose yesterday and saves that transaction date', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 5, 17, 9, 0, 0))
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'disabled',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.find('.date-side-button').trigger('click')
    expect(wrapper.text()).toContain('2026/6/16(昨天)')
    expect(wrapper.find('.date-side-button svg').exists()).toBe(true)

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')

    await vi.waitFor(() => expect(createTransaction).toHaveBeenCalledTimes(1))
    expect(vi.mocked(createTransaction).mock.calls[0][1].transaction_date).toBe('2026-06-16')
    expect(vi.mocked(createTransaction).mock.calls[0][1].items).toEqual([
      {
        category_name: 'category.food',
        item_name: undefined,
        amount: 1,
        currency_code: 'JPY',
      },
    ])

    await vi.waitFor(() => expect(wrapper.find('.done-panel').exists()).toBe(true))
    await wrapper.find('.done-panel .primary-button').trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))
    expect(wrapper.text()).toContain('2026/6/16(昨天)')
  })

  it('shows a saving overlay while the final submit is in progress', async () => {
    let resolveSave: () => void = () => undefined
    vi.mocked(createTransaction).mockImplementationOnce(
      async () =>
        new Promise((resolve) => {
          resolveSave = () => resolve({ id: 'transaction-1' } as Awaited<ReturnType<typeof createTransaction>>)
        }),
    )
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'disabled',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')

    await vi.waitFor(() => expect(wrapper.find('.saving-overlay').exists()).toBe(true))
    expect(wrapper.text()).toContain('保存中')

    resolveSave()
    await vi.waitFor(() => expect(wrapper.find('.done-panel').exists()).toBe(true))
  })

  it('opens a large app calendar and applies the selected date immediately', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 5, 17, 9, 0, 0))
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'disabled',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.find('.calendar-button').trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.calendar-dialog').exists()).toBe(true))
    const dayButton = wrapper.findAll('.dp--cell-inner').find((button) => button.text() === '12')
    expect(dayButton).toBeTruthy()
    await dayButton?.trigger('click')

    await vi.waitFor(() => expect(wrapper.find('.calendar-dialog').exists()).toBe(false))
    expect(wrapper.text()).toContain('2026/6/12')

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')

    await vi.waitFor(() => expect(createTransaction).toHaveBeenCalledTimes(1))
    expect(vi.mocked(createTransaction).mock.calls[0][1].transaction_date).toBe('2026-06-12')
  })

  it('supports decimal amount entry for currencies with minor units', async () => {
    const wrapper = mount(WizardFlow, {
      props: { ledger: ledger({ default_currency_code: 'CNY' }) },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === '2')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === '.')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === '3')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === '4')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '米')?.trigger('click')
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '不花不行')?.trigger('click')
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '自己')?.trigger('click')
    await wrapper.find('.subject-confirm').trigger('click')

    await vi.waitFor(() => expect(createTransaction).toHaveBeenCalledTimes(1))
    expect(vi.mocked(createTransaction).mock.calls[0][1].amount).toBe(1234)
  })

  it('advances from amount to category after keypad OK', async () => {
    const wrapper = mount(WizardFlow, {
      props: { ledger: ledger() },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === '2')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === '0')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === '0')?.trigger('click')
    expect(wrapper.find('.amount-display strong').text()).toBe('1,200')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')

    expect(wrapper.text()).toContain('分类')
  })

  it('uses the titlebar back button to leave from amount and step back later', async () => {
    const wrapper = mount(WizardFlow, {
      props: { ledger: ledger() },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.find('.back-button').trigger('click')
    expect(wrapper.emitted('done')).toHaveLength(1)

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.wizard-titlebar h2').text()).toBe('分类'))
    await wrapper.find('.back-button').trigger('click')

    expect(wrapper.find('.wizard-titlebar h2').text()).toBe('输入金额')
    expect(wrapper.find('.keypad').exists()).toBe(true)
  })

  it('advances from receipt amount to category before necessity', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'required',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))

    expect(wrapper.text()).not.toContain('不花不行')
    expect(wrapper.text()).not.toContain('保存')
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    expect(wrapper.text()).toContain('不花不行')
    expect(wrapper.findAll('.chip-grid .selected')).toHaveLength(0)
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '不花不行')?.trigger('click')
    await vi.waitFor(() => expect(createTransaction).toHaveBeenCalledTimes(1))
    expect(wrapper.text()).toContain('记录成功')
  })

  it('waits for an explicit necessity choice before saving', async () => {
    vi.useFakeTimers()
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'required',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('不花不行'))

    expect(wrapper.findAll('.chip-grid .selected')).toHaveLength(0)
    vi.advanceTimersByTime(5000)
    await wrapper.vm.$nextTick()
    expect(createTransaction).not.toHaveBeenCalled()
    expect(wrapper.text()).not.toContain('记录成功')

    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '其实可以不花')?.trigger('click')
    await vi.waitFor(() => expect(createTransaction).toHaveBeenCalledTimes(1))
    expect(wrapper.find('.wizard-titlebar h2').text()).toBe('记录成功')
    expect(wrapper.text()).toContain('记录成功')
    expect(wrapper.text()).not.toContain('不花不行')
    expect(wrapper.text()).toContain('再记一笔')
    vi.useRealTimers()
  })

  it('hides the close-step action when necessity is required', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'required',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('不花不行'))

    expect(wrapper.text()).toContain('其实可以不花')
    expect(wrapper.text()).not.toContain('关闭此步骤')
  })

  it('lets the subject step select multiple people before confirming', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          necessity_step_mode: 'disabled',
          subject_enabled: true,
          subject_step_mode: 'required',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.wizard-titlebar h2').text()).toBe('花费对象'))

    expect(wrapper.find('.subject-confirm').attributes('disabled')).toBeDefined()
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '自己')?.trigger('click')
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '妈妈')?.trigger('click')
    expect(wrapper.findAll('.chip-grid .selected')).toHaveLength(2)
    await wrapper.find('.subject-confirm').trigger('click')

    await vi.waitFor(() => expect(createTransaction).toHaveBeenCalledTimes(1))
    expect(vi.mocked(createTransaction).mock.calls[0][1].subject_ids).toEqual(['subject-1', 'subject-2'])
  })

  it('places OK between frequently used subjects and unused subjects', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          necessity_step_mode: 'disabled',
          subject_enabled: true,
          subject_step_mode: 'required',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.wizard-titlebar h2').text()).toBe('花费对象'))

    const text = wrapper.text()
    expect(text.indexOf('自己')).toBeLessThan(text.indexOf('OK'))
    expect(text.indexOf('OK')).toBeLessThan(text.indexOf('妈妈'))
  })

  it('creates a custom subject and selects it immediately', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          necessity_step_mode: 'disabled',
          subject_enabled: true,
          subject_step_mode: 'required',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.wizard-titlebar h2').text()).toBe('花费对象'))

    await wrapper.findAll('.add-chip').find((button) => button.text().includes('自定义'))?.trigger('click')
    await wrapper.find('.custom-subject-field input').setValue('家族')
    await wrapper.find('.custom-subject-field .primary-button').trigger('click')

    expect(createSubject).toHaveBeenCalledWith('ledger-1', '家族')
    expect(wrapper.text()).toContain('家族')
    await wrapper.find('.subject-confirm').trigger('click')
    await vi.waitFor(() => expect(createTransaction).toHaveBeenCalledTimes(1))
    expect(vi.mocked(createTransaction).mock.calls[0][1].subject_ids).toEqual(['subject-custom'])
  })

  it('uses the title trash action to remove a subject from the current user view', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          necessity_step_mode: 'disabled',
          subject_enabled: true,
          subject_step_mode: 'required',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.wizard-titlebar h2').text()).toBe('花费对象'))

    await wrapper.findAll('.title-action-button')[1].trigger('click')
    expect(wrapper.findAll('.subject-chip').find((button) => button.text().includes('自己'))?.attributes('disabled')).toBeDefined()
    await wrapper.findAll('.subject-chip').find((button) => button.text().includes('家族'))?.trigger('click')

    expect(deleteSubject).toHaveBeenCalledWith('ledger-1', 'subject-custom-existing')
    expect(wrapper.text()).not.toContain('家族')
  })

  it('moves to the next available step after disabling necessity', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          subject_enabled: true,
          subject_step_mode: 'required',
          necessity_step_mode: 'optional',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('关闭此步骤'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '关闭此步骤')?.trigger('click')
    await wrapper.setProps({
      ledger: ledger({
        entry_mode: 'receipt',
        subject_enabled: true,
        subject_step_mode: 'required',
        necessity_step_mode: 'disabled',
      }),
    })

    await vi.waitFor(() => expect(wrapper.find('.wizard-titlebar h2').text()).toBe('花费对象'))
    expect(wrapper.text()).toContain('自己')
  })

  it('does not show a save button before the wizard reaches completion', async () => {
    const wrapper = mount(WizardFlow, {
      props: { ledger: ledger() },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))

    expect(wrapper.text()).not.toContain('保存')
    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    expect(wrapper.text()).not.toContain('保存')
  })

  it('shows a plus custom item chip before opening manual item input', async () => {
    const wrapper = mount(WizardFlow, {
      props: { ledger: ledger() },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))
    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    expect(wrapper.find('.title-actions').exists()).toBe(false)
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('自定义'))

    expect(wrapper.find('.title-actions').exists()).toBe(false)
    expect(wrapper.find('.custom-item-field input').exists()).toBe(false)
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '自定义')?.trigger('click')
    expect(wrapper.find('.custom-item-field input').exists()).toBe(true)
    expect(wrapper.find('.custom-item-field').classes()).toContain('custom-item-field')
  })

  it('lets receipt details be skipped and saves an added spending location', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'receipt',
          receipt_item_enabled: true,
          location_step_mode: 'optional',
          necessity_step_mode: 'disabled',
          subject_enabled: false,
          subject_step_mode: 'disabled',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))
    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')

    await vi.waitFor(() => expect(wrapper.find('.wizard-titlebar h2').text()).toBe('消费名称'))
    await vi.waitFor(() => expect(wrapper.text()).toContain('米'))
    expect(wrapper.text().indexOf('跳过')).toBeLessThan(wrapper.text().indexOf('米'))
    expect(wrapper.find('.skip-button svg').exists()).toBe(true)
    await wrapper.find('.skip-button').trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.wizard-titlebar h2').text()).toBe('在哪里消费'))
    expect(wrapper.text().indexOf('跳过')).toBeLessThan(wrapper.text().indexOf('駅前スーパー'))
    expect(wrapper.find('.skip-button svg').exists()).toBe(true)
    await wrapper.findAll('.add-chip').find((button) => button.text().includes('追加地点'))?.trigger('click')
    await wrapper.find('.location-field input').setValue('公司附近')
    await wrapper.find('.location-field button').trigger('click')

    expect(createTransaction).not.toHaveBeenCalled()
    expect(wrapper.find('.location-field').exists()).toBe(false)
    expect(wrapper.findAll('.chip-grid button').some((button) => button.text() === '公司附近')).toBe(true)
    expect(wrapper.find('.title-actions').exists()).toBe(true)
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '公司附近')?.trigger('click')

    await vi.waitFor(() => expect(createTransaction).toHaveBeenCalledTimes(1))
    expect(vi.mocked(createTransaction).mock.calls[0][1]).toMatchObject({
      location_name: '公司附近',
      items: [{ item_name: undefined }],
    })
  })

  it('refreshes item tags after saving a custom item and recording another', async () => {
    const wrapper = mount(WizardFlow, {
      props: {
        ledger: ledger({
          entry_mode: 'item',
          subject_enabled: false,
          subject_step_mode: 'disabled',
          necessity_step_mode: 'disabled',
        }),
      },
    })
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))
    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('自定义'))

    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '自定义')?.trigger('click')
    await wrapper.find('.custom-item-field input').setValue('咖啡')
    await wrapper.find('.custom-item-field .primary-button').trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('记录成功'))

    await wrapper.find('.done-panel .primary-button').trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.keypad').exists()).toBe(true))
    await wrapper.findAll('.keypad button').find((button) => button.text() === '1')?.trigger('click')
    await wrapper.findAll('.keypad button').find((button) => button.text() === 'OK')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('分类'))
    await wrapper.findAll('.chip-grid button').find((button) => button.text() === '食品饮料')?.trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('咖啡'))
  })
})
