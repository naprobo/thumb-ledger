import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createSuggestion, deleteSuggestion, updateSuggestion, voteSuggestion } from '@/api/suggestions'
import SuggestionsView from '@/views/SuggestionsView.vue'

vi.mock('@/api/suggestions', () => ({
  listMySuggestions: vi.fn(async () => [
    {
      id: 'suggestion-1',
      author_id: 'user-1',
      title: 'Monthly budget template',
      body: 'Please save budget templates',
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
      title: 'Public roadmap',
      body: 'Please show planned work',
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
  updateSuggestion: vi.fn(async (id, payload) => ({
    id,
    author_id: 'user-1',
    status: 'new',
    support_count: 0,
    oppose_count: 0,
    my_vote: null,
    created_at: '2026-06-12T00:00:00Z',
    updated_at: '2026-06-14T00:00:00Z',
    ...payload,
  })),
  deleteSuggestion: vi.fn(async () => undefined),
  voteSuggestion: vi.fn(async (id, voteType) => ({
    id,
    author_id: 'user-2',
    title: 'Public roadmap',
    body: 'Please show planned work',
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
    await vi.waitFor(() => expect(wrapper.find('.suggestion-list li').exists()).toBe(true))

    await wrapper.find('input[maxlength="100"]').setValue('Quick tags')
    await wrapper.find('textarea').setValue('Please support editing quick tags')
    await wrapper.find('input[type="checkbox"]').setValue(true)
    await wrapper.find('form').trigger('submit')

    expect(createSuggestion).toHaveBeenCalledWith({
      title: 'Quick tags',
      body: 'Please support editing quick tags',
      is_public: true,
    })

    expect(createSuggestion).toHaveBeenCalledTimes(1)
  })

  it('votes on a public suggestion', async () => {
    const { wrapper } = await mountWithRouter()
    await vi.waitFor(() => expect(wrapper.find('.suggestion-list li').exists()).toBe(true))
    await wrapper.findAll('.tabs button')[1].trigger('click')

    await wrapper.findAll('.vote-actions button')[0].trigger('click')

    expect(voteSuggestion).toHaveBeenCalledWith('suggestion-2', 'support')
  })

  it('edits and deletes own suggestions', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const { wrapper } = await mountWithRouter()
    await vi.waitFor(() => expect(wrapper.find('.suggestion-list li').exists()).toBe(true))

    await wrapper.findAll('.suggestion-actions button')[0].trigger('click')
    await wrapper.find('input[maxlength="100"]').setValue('Updated suggestion')
    await wrapper.find('textarea').setValue('Updated body')
    await wrapper.find('form').trigger('submit')

    expect(updateSuggestion).toHaveBeenCalledWith('suggestion-1', {
      title: 'Updated suggestion',
      body: 'Updated body',
      is_public: false,
    })

    await wrapper.find('.suggestion-actions .danger-button').trigger('click')
    expect(deleteSuggestion).toHaveBeenCalledWith('suggestion-1')
  })

  it('returns to ledger home from the title back button', async () => {
    const { wrapper, router } = await mountWithRouter()
    await vi.waitFor(() => expect(wrapper.find('.back-button').exists()).toBe(true))

    await wrapper.find('.back-button').trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('ledger-list'))
  })

  it('shows a floating error when voting is rejected', async () => {
    vi.mocked(voteSuggestion).mockRejectedValueOnce({ response: { status: 403 } })
    const { wrapper } = await mountWithRouter()
    await vi.waitFor(() => expect(wrapper.find('.suggestion-list li').exists()).toBe(true))
    await wrapper.findAll('.tabs button')[1].trigger('click')

    await wrapper.findAll('.vote-actions button')[0].trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.toast.error').exists()).toBe(true))
  })
})
