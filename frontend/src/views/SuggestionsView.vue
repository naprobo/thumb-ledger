<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="title-row">
        <button
          type="button"
          class="back-button"
          :aria-label="t('common.back')"
          :title="t('common.back')"
          @click="router.push({ name: 'ledger-list' })"
        >
          <ChevronLeft :size="24" aria-hidden="true" />
        </button>
        <h1>{{ t('suggestions.title') }}</h1>
      </div>
      <button type="button" class="refresh-button" :class="{ spinning: isRefreshing }" :disabled="isRefreshing" @click="refresh">
        <RefreshCw :size="18" aria-hidden="true" />
        <span>{{ t('common.refresh') }}</span>
      </button>
    </header>

    <div v-if="toastMessage" :class="['toast', toastKind]" role="status">
      {{ toastMessage }}
    </div>

    <section class="submit-panel">
      <h2>{{ t('suggestions.submit') }}</h2>
      <form @submit.prevent="submitSuggestion">
        <label>
          <span>{{ t('suggestions.subject') }}</span>
          <input v-model.trim="draft.title" maxlength="100" required />
        </label>
        <label>
          <span>{{ t('suggestions.body') }}</span>
          <textarea v-model.trim="draft.body" maxlength="2000" required />
        </label>
        <label class="switch-row">
          <input v-model="draft.is_public" type="checkbox" />
          <span>{{ t('suggestions.makePublic') }}</span>
        </label>
        <button class="primary-button" type="submit" :disabled="isSubmitting || !canSubmit">
          {{ t('suggestions.submit') }}
        </button>
      </form>
    </section>

    <section class="list-panel">
      <div class="tabs">
        <button type="button" :class="{ selected: activeTab === 'mine' }" @click="activeTab = 'mine'">
          {{ t('suggestions.mine') }}
        </button>
        <button type="button" :class="{ selected: activeTab === 'public' }" @click="activeTab = 'public'">
          {{ t('suggestions.public') }}
        </button>
      </div>

      <AppLoadingPanel v-if="isInitialLoading" class="list-loading" />

      <ul v-else-if="visibleSuggestions.length" class="suggestion-list">
        <li v-for="suggestion in visibleSuggestions" :key="suggestion.id">
          <div>
            <strong>{{ suggestion.title }}</strong>
            <p>{{ suggestion.body }}</p>
            <span>{{ statusLabel(suggestion.status) }} · {{ formatDate(suggestion.created_at) }}</span>
          </div>
          <div class="vote-actions">
            <button
              type="button"
              :class="{ selected: suggestion.my_vote === 'support' }"
              :disabled="activeTab !== 'public'"
              @click="vote(suggestion, 'support')"
            >
              {{ t('suggestions.support') }} {{ suggestion.support_count }}
            </button>
            <button
              type="button"
              :class="{ selected: suggestion.my_vote === 'oppose' }"
              :disabled="activeTab !== 'public'"
              @click="vote(suggestion, 'oppose')"
            >
              {{ t('suggestions.oppose') }} {{ suggestion.oppose_count }}
            </button>
          </div>
        </li>
      </ul>
      <p v-else class="muted">{{ t('suggestions.empty') }}</p>
    </section>

  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ChevronLeft, RefreshCw } from '@lucide/vue'

import {
  createSuggestion,
  listMySuggestions,
  listPublicSuggestions,
  voteSuggestion,
  type Suggestion,
  type SuggestionStatus,
  type SuggestionVoteType,
} from '@/api/suggestions'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'

const { t } = useI18n()
const router = useRouter()
const activeTab = ref<'mine' | 'public'>('mine')
const mySuggestions = ref<Suggestion[]>([])
const publicSuggestions = ref<Suggestion[]>([])
const isInitialLoading = ref(true)
const isRefreshing = ref(false)
const isSubmitting = ref(false)
const toastMessage = ref('')
const toastKind = ref<'success' | 'error'>('success')
let toastTimer: number | undefined
const draft = reactive({
  title: '',
  body: '',
  is_public: false,
})

const visibleSuggestions = computed(() => (activeTab.value === 'mine' ? mySuggestions.value : publicSuggestions.value))
const canSubmit = computed(() => draft.title.length >= 1 && draft.body.length >= 1)

onMounted(refresh)

async function refresh() {
  isRefreshing.value = true
  try {
    const [mine, publicRows] = await Promise.all([listMySuggestions(), listPublicSuggestions()])
    mySuggestions.value = mine
    publicSuggestions.value = publicRows
  } catch {
    showToast(t('errors.networkError'), 'error')
  } finally {
    isInitialLoading.value = false
    isRefreshing.value = false
  }
}

async function submitSuggestion() {
  if (!canSubmit.value) return
  isSubmitting.value = true
  try {
    await createSuggestion({ ...draft })
    draft.title = ''
    draft.body = ''
    draft.is_public = false
    showToast(t('suggestions.submitted'), 'success')
    await refresh()
    activeTab.value = 'mine'
  } catch {
    showToast(t('errors.validationError'), 'error')
  } finally {
    isSubmitting.value = false
  }
}

async function vote(suggestion: Suggestion, voteType: SuggestionVoteType) {
  try {
    const updated = await voteSuggestion(suggestion.id, voteType)
    publicSuggestions.value = publicSuggestions.value.map((item) => (item.id === updated.id ? updated : item))
  } catch {
    showToast(t('suggestions.ownVoteForbidden'), 'error')
  }
}

function statusLabel(status: SuggestionStatus): string {
  return t(`suggestions.status.${status}`)
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString()
}

function showToast(message: string, kind: 'success' | 'error') {
  toastMessage.value = message
  toastKind.value = kind
  if (toastTimer) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
  }, 3200)
}
</script>

<style scoped>
.page-shell {
  width: min(100%, 1280px);
  margin: 0 auto;
  padding: 24px clamp(12px, 3vw, 36px);
}

.topbar,
.title-row,
.tabs,
.vote-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title-row {
  min-width: 0;
  justify-content: start;
}

.back-button {
  display: inline-grid;
  width: 44px;
  min-width: 44px;
  height: 44px;
  min-height: 44px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  padding: 0;
  background: transparent;
  line-height: 1;
}

h1,
h2,
p {
  margin-top: 0;
}

.submit-panel,
.list-panel {
  margin-top: 16px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}

.list-loading {
  min-height: 260px;
}

.toast {
  position: fixed;
  top: 64px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 15;
  width: min(calc(100% - 32px), 520px);
  border: 1px solid;
  border-radius: 8px;
  padding: 12px 16px;
  text-align: center;
  font-weight: 800;
  box-shadow: 0 14px 32px rgb(15 23 42 / 14%);
}

.toast.success {
  border-color: #86efac;
  background: #dcfce7;
  color: #166534;
}

.toast.error {
  border-color: #fecaca;
  background: #fee2e2;
  color: #991b1b;
}

form {
  display: grid;
  gap: 12px;
}

label {
  display: grid;
  gap: 6px;
  font-weight: 700;
}

.switch-row {
  display: flex;
  align-items: center;
  min-height: 44px;
}

input,
textarea,
button {
  min-height: 44px;
  border-radius: 6px;
  font: inherit;
}

input,
textarea {
  border: 1px solid #b8c0cc;
  padding: 10px 12px;
}

textarea {
  min-height: 132px;
  resize: vertical;
}

button {
  border: 1px solid #c9d1dc;
  background: #fff;
  padding: 0 14px;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.refresh-button.spinning svg {
  animation: spin-refresh 0.8s linear infinite;
}

.primary-button,
.selected {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
  font-weight: 700;
}

.tabs {
  justify-content: start;
}

.suggestion-list {
  display: grid;
  gap: 10px;
  padding: 0;
  list-style: none;
}

.suggestion-list li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  border-top: 1px solid #eef2f7;
  padding: 12px 0;
}

.suggestion-list p {
  margin-bottom: 8px;
  white-space: pre-wrap;
}

.suggestion-list span,
.muted {
  color: #607086;
}

@media (max-width: 640px) {
  .topbar,
  .suggestion-list li,
  .vote-actions {
    align-items: stretch;
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}

@keyframes spin-refresh {
  to {
    transform: rotate(360deg);
  }
}
</style>
