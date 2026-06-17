import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { createSuggestion, voteSuggestion } from '@/api/suggestions'
import SuggestionsView from '@/views/SuggestionsView.vue'

vi.mock('@/api/suggestions', () => ({
  listMySuggestions: vi.fn(async () => [
    {
      id: 'suggestion-1',
      author_id: 'user-1',
      title: '月度预算模板',
      body: '希望能保存预算模板',
      is_public: false,
      status: 'new',
      support_count: 0,
      oppose_count: 0,
      my_vote: null,
      created_at: '2026-06-12T00:00:00Z',
      updated_at: '2026-06-12T00:00:00Z',
    },
  ]),
  listPublicSuggestions: vi.fn(async () => [
    {
      id: 'suggestion-2',
      author_id: 'user-2',
      title: '公开路线图',
      body: '希望能看到计划',
      is_public: true,
      status: 'reviewing',
      support_count: 2,
      oppose_count: 0,
      my_vote: null,
      created_at: '2026-06-11T00:00:00Z',
      updated_at: '2026-06-11T00:00:00Z',
    },
  ]),
  createSuggestion: vi.fn(async (payload) => ({
    id: 'suggestion-3',
    author_id: 'user-1',
    status: 'new',
    support_count: 0,
    oppose_count: 0,
    my_vote: null,
    created_at: '2026-06-13T00:00:00Z',
    updated_at: '2026-06-13T00:00:00Z',
    ...payload,
  })),
  voteSuggestion: vi.fn(async (id, voteType) => ({
    id,
    author_id: 'user-2',
    title: '公开路线图',
    body: '希望能看到计划',
    is_public: true,
    status: 'reviewing',
    support_count: voteType === 'support' ? 3 : 2,
    oppose_count: voteType === 'oppose' ? 1 : 0,
    my_vote: voteType,
    created_at: '2026-06-11T00:00:00Z',
    updated_at: '2026-06-11T00:00:00Z',
  })),
}))

async function mountWithRouter() {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/ledgers', name: 'ledger-list', component: { template: '<div />' } },
      { path: '/suggestions', name: 'suggestions', component: SuggestionsView },
    ],
  })
  router.push('/suggestions')
  await router.isReady()
  const wrapper = mount(SuggestionsView, { global: { plugins: [router] } })
  return { wrapper, router }
}

describe('SuggestionsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('submits a suggestion and renders mine/public tabs', async () => {
    const { wrapper } = await mountWithRouter()
    await vi.waitFor(() => expect(wrapper.text()).toContain('月度预算模板'))

    await wrapper.find('input[maxlength="100"]').setValue('快捷标签')
    await wrapper.find('textarea').setValue('希望首页支持快捷标签编辑')
    await wrapper.find('input[type="checkbox"]').setValue(true)
    await wrapper.find('form').trigger('submit')

    expect(createSuggestion).toHaveBeenCalledWith({
      title: '快捷标签',
      body: '希望首页支持快捷标签编辑',
      is_public: true,
    })

    await vi.waitFor(() => expect(wrapper.text()).toContain('建议已提交'))
    await wrapper.findAll('.tabs button')[1].trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('公开路线图')
  })

  it('votes on a public suggestion', async () => {
    const { wrapper } = await mountWithRouter()
    await vi.waitFor(() => expect(wrapper.text()).toContain('月度预算模板'))
    await wrapper.findAll('.tabs button')[1].trigger('click')

    await wrapper.findAll('.vote-actions button')[0].trigger('click')

    expect(voteSuggestion).toHaveBeenCalledWith('suggestion-2', 'support')
  })

  it('returns to ledger home from the title back button', async () => {
    const { wrapper, router } = await mountWithRouter()
    await vi.waitFor(() => expect(wrapper.text()).toContain('用户建议'))

    await wrapper.find('.back-button').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('ledger-list'))

    expect(router.currentRoute.value.name).toBe('ledger-list')
  })

  it('shows a floating error when voting is rejected', async () => {
    vi.mocked(voteSuggestion).mockRejectedValueOnce({ response: { status: 403 } })
    const { wrapper } = await mountWithRouter()
    await vi.waitFor(() => expect(wrapper.text()).toContain('月度预算模板'))
    await wrapper.findAll('.tabs button')[1].trigger('click')

    await wrapper.findAll('.vote-actions button')[0].trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.toast.error').exists()).toBe(true))

    expect(wrapper.text()).toContain('不能支持或反对自己的建议')
  })
})
