import { mount } from '@vue/test-utils'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import AdminPanel from '@/views/AdminPanel.vue'
import { updateAdminSuggestionStatus, updateAdminUserStatus } from '@/api/admin'

vi.mock('@/api/admin', () => ({
  listAdminUsers: vi.fn(async () => [
    {
      id: 'user-1',
      email: 'admin@example.com',
      is_active: true,
      is_admin: true,
      created_at: '2026-06-12T00:00:00Z',
    },
    {
      id: 'user-2',
      email: 'disabled@example.com',
      is_active: false,
      is_admin: false,
      created_at: '2026-06-11T00:00:00Z',
    },
  ]),
  getAdminStats: vi.fn(async () => ({
    total_users: 2,
    total_ledgers: 3,
    total_transactions: 4,
  })),
  listAdminSuggestions: vi.fn(async () => [
    {
      id: 'suggestion-1',
      author_id: 'user-2',
      author_email: 'user@example.com',
      title: '导出 OFX',
      body: '希望支持银行软件格式',
      is_public: true,
      status: 'new',
      support_count: 3,
      oppose_count: 1,
      my_vote: null,
      created_at: '2026-06-12T00:00:00Z',
      updated_at: '2026-06-12T00:00:00Z',
    },
  ]),
  updateAdminSuggestionStatus: vi.fn(async (id: string, status: string) => ({
    id,
    author_id: 'user-2',
    author_email: 'user@example.com',
    title: '导出 OFX',
    body: '希望支持银行软件格式',
    is_public: true,
    status,
    support_count: 3,
    oppose_count: 1,
    my_vote: null,
    created_at: '2026-06-12T00:00:00Z',
    updated_at: '2026-06-12T00:00:00Z',
  })),
  updateAdminUserStatus: vi.fn(async (id: string, isActive: boolean) => ({
    id,
    email: 'admin@example.com',
    is_active: isActive,
    is_admin: true,
    created_at: '2026-06-12T00:00:00Z',
  })),
  deleteAdminUser: vi.fn(),
}))

describe('AdminPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders stats and user rows', async () => {
    const wrapper = mount(AdminPanel)
    await vi.waitFor(() => expect(wrapper.text()).toContain('admin@example.com'))

    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('4')
    expect(wrapper.text()).toContain('disabled@example.com')
    expect(wrapper.text()).toContain('导出 OFX')
    expect(wrapper.text()).toContain('user@example.com')
  })

  it('toggles user active status', async () => {
    const wrapper = mount(AdminPanel)
    await vi.waitFor(() => expect(wrapper.text()).toContain('admin@example.com'))

    await wrapper.findAll('tbody button')[0].trigger('click')

    expect(updateAdminUserStatus).toHaveBeenCalledWith('user-1', false)
  })

  it('updates suggestion status', async () => {
    const wrapper = mount(AdminPanel)
    await vi.waitFor(() => expect(wrapper.text()).toContain('导出 OFX'))

    await wrapper.find('select').setValue('planned')

    expect(updateAdminSuggestionStatus).toHaveBeenCalledWith('suggestion-1', 'planned')
  })
})
