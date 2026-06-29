<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="title-row">
        <button
          type="button"
          class="back-button"
          :aria-label="t('common.back')"
          :title="t('common.back')"
          @click="router.push({ name: 'ledger-detail', params: { id: ledgerId } })"
        >
          <ChevronLeft :size="24" aria-hidden="true" />
        </button>
        <h1>{{ t('settings.title') }}</h1>
      </div>
    </header>

    <div v-if="toastMessage" :class="['toast', toastKind]" role="status">
      {{ toastMessage }}
    </div>

    <AppLoadingPanel v-if="isInitialLoading" class="content-loading" />

    <template v-else>
    <section v-if="ledger" class="section-block">
      <form class="settings-form" @submit.prevent="saveSettings">
        <div class="settings-grid">
          <label>
            <span>{{ t('ledger.name') }}</span>
            <input v-model.trim="draft.name" maxlength="50" required />
          </label>

          <label>
            <span>{{ t('ledger.defaultCurrency') }}</span>
            <select v-model="draft.default_currency_code">
              <option v-for="currency in CURRENCY_OPTIONS" :key="currency.code" :value="currency.code">
                {{ currencyOptionLabel(currency) }}
              </option>
            </select>
          </label>

          <label>
            <span>{{ t('ledger.subjectStepMode') }}</span>
            <select v-model="draft.subject_step_mode">
              <option value="required">{{ t('ledger.subjectRequired') }}</option>
              <option value="optional">{{ t('ledger.subjectOptional') }}</option>
              <option value="disabled">{{ t('common.disabled') }}</option>
            </select>
          </label>

          <label>
            <span>{{ t('ledger.necessityTracking') }}</span>
            <select v-model="draft.necessity_step_mode">
              <option value="required">{{ t('ledger.subjectRequired') }}</option>
              <option value="optional">{{ t('ledger.subjectOptional') }}</option>
              <option value="disabled">{{ t('common.disabled') }}</option>
            </select>
          </label>
        </div>

        <div class="save-row">
          <button class="primary-button" type="submit" :disabled="isSaving">{{ t('common.save') }}</button>
        </div>
      </form>
    </section>

    <section v-if="ledger" class="section-block action-block">
      <button type="button" @click="router.push({ name: 'ledger-recurring', params: { id: ledger.id } })">
        {{ t('settings.recurringTransactions') }}
      </button>
    </section>

    <section v-if="ledger" class="section-block action-block">
      <button type="button" @click="router.push({ name: 'budget-wizard', params: { id: ledger.id } })">
        {{ t('budget.title') }}
      </button>
    </section>

    <section v-if="ledger" class="section-block share-panel">
      <div class="section-heading">
        <h2>{{ t('settings.share') }}</h2>
        <div class="heading-icons">
          <button
            type="button"
            class="round-icon-button"
            :aria-label="t('settings.shareCode')"
            :title="t('settings.shareCode')"
            @click="toggleShareCode"
          >
            <EyeOff v-if="isShareCodeVisible" :size="19" aria-hidden="true" />
            <Eye v-else :size="19" aria-hidden="true" />
          </button>
        </div>
      </div>
      <div class="share-code-row">
        <code>{{ displayShareCode }}</code>
        <button
          type="button"
          class="icon-action"
          :disabled="!isShareCodeVisible || !shareCode"
          :aria-label="t('share.copyCode')"
          :title="t('share.copyCode')"
          @click="copyShareCode"
        >
          <Copy :size="20" aria-hidden="true" />
        </button>
      </div>
      <p v-if="shareError" class="muted">{{ shareError }}</p>

      <div class="subsection-heading">
        <h3>{{ t('share.pendingRequests') }}</h3>
        <button
          type="button"
          class="round-icon-button small"
          :class="{ spinning: isShareRequestsLoading }"
          :disabled="isShareRequestsLoading"
          :aria-label="t('common.refresh')"
          :title="t('common.refresh')"
          @click="loadShareRequests"
        >
          <RotateCw :size="17" aria-hidden="true" />
        </button>
      </div>
      <ul v-if="pendingRequests.length" class="request-list">
        <li v-for="request in pendingRequests" :key="request.id">
          <div>
            <strong>{{ request.requester_display_name || request.requester_email || request.requester_id }}</strong>
            <small>{{ roleLabel(request.role) }}</small>
          </div>
          <div class="request-actions">
            <button type="button" @click="approveRequest(request.id)">{{ t('share.approve') }}</button>
            <button type="button" @click="rejectRequest(request.id)">{{ t('share.reject') }}</button>
          </div>
        </li>
      </ul>
      <p v-else class="muted">{{ t('share.noPendingRequests') }}</p>

      <div class="subsection-heading">
        <h3>{{ t('settings.members') }}</h3>
        <button
          type="button"
          class="round-icon-button small"
          :class="{ spinning: isMembersLoading }"
          :disabled="isMembersLoading"
          :aria-label="t('common.refresh')"
          :title="t('common.refresh')"
          @click="loadMembers"
        >
          <RotateCw :size="17" aria-hidden="true" />
        </button>
      </div>
      <ul v-if="members.length" class="member-list">
        <li v-for="member in members" :key="member.id">
          <button class="member-link" type="button" @click="router.push({ name: 'share-member', params: { id: ledgerId, userId: member.user_id } })">
            <span class="member-name">
              <span :class="['member-name-text', { marquee: isLongMemberName(member.display_name || member.email || member.user_id) }]">
                {{ member.display_name || member.email || member.user_id }}
              </span>
            </span>
            <small>{{ roleLabel(member.role) }}</small>
          </button>
        </li>
      </ul>
      <p v-else class="muted">{{ t('settings.noMembers') }}</p>
    </section>

    <section v-if="ledger" class="section-block danger">
      <h2>{{ t('settings.dangerZone') }}</h2>
      <button type="button" @click="showDeleteConfirm = true">{{ t('ledger.delete') }}</button>
    </section>
    </template>

    <div v-if="showDeleteConfirm" class="modal-backdrop" role="presentation" @click.self="showDeleteConfirm = false">
      <section class="confirm-dialog" role="dialog" aria-modal="true" :aria-label="t('ledger.delete')">
        <h2>{{ t('ledger.delete') }}</h2>
        <p>{{ t('ledger.deleteConfirm') }}</p>
        <div class="dialog-actions">
          <button type="button" @click="showDeleteConfirm = false">{{ t('common.cancel') }}</button>
          <button type="button" class="danger-button" @click="deleteCurrentLedger">{{ t('ledger.delete') }}</button>
        </div>
      </section>
    </div>

  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft, Copy, Eye, EyeOff, RotateCw } from '@lucide/vue'

import {
  approveShareRequest,
  getShareCode,
  listMembers,
  listShareRequests,
  rejectShareRequest,
  type LedgerMember,
  type NecessityStepMode,
  type ShareRequest,
  type SubjectStepMode,
} from '@/api/ledgers'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'
import { CURRENCY_OPTIONS, currencyOptionLabel } from '@/constants/currencies'
import { useAuthStore } from '@/stores/auth'
import { useLedgerStore } from '@/stores/ledgers'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const ledgerStore = useLedgerStore()
const ledgerId = computed(() => String(route.params.id))
const ledger = computed(() => ledgerStore.activeLedger)

const draft = reactive<{ name: string; subject_step_mode: SubjectStepMode; necessity_step_mode: NecessityStepMode; default_currency_code: string }>({
  name: '',
  subject_step_mode: 'required',
  necessity_step_mode: 'disabled',
  default_currency_code: 'JPY',
})
const members = ref<LedgerMember[]>([])
const shareRequests = ref<ShareRequest[]>([])
const shareCode = ref('')
const shareError = ref('')
const isShareCodeVisible = ref(false)
const isMembersLoading = ref(false)
const isShareRequestsLoading = ref(false)
const isInitialLoading = ref(true)
const isSaving = ref(false)
const toastMessage = ref('')
const toastKind = ref<'success' | 'error'>('success')
const showDeleteConfirm = ref(false)
let toastTimer: number | undefined

const displayShareCode = computed(() => {
  if (!shareCode.value) return '********'
  return isShareCodeVisible.value ? shareCode.value : '*'.repeat(Math.max(8, shareCode.value.length))
})

onMounted(async () => {
  try {
    if (!authStore.user && authStore.token) {
      await authStore.fetchCurrentUser()
    }
    const loaded = await ledgerStore.fetchLedger(ledgerId.value)
    if (authStore.user && loaded.owner_id !== authStore.user.id) {
      await router.replace({ name: 'ledger-detail', params: { id: ledgerId.value } })
      return
    }
    draft.name = loaded.name
    draft.subject_step_mode = loaded.subject_step_mode
    draft.necessity_step_mode = loaded.necessity_step_mode
    draft.default_currency_code = loaded.default_currency_code
    await Promise.all([loadShareCode(), loadMembers(), loadShareRequests()])
  } finally {
    isInitialLoading.value = false
  }
})

async function saveSettings() {
  if (!draft.name.trim()) {
    showToast(t('errors.validationError'), 'error')
    return
  }
  isSaving.value = true
  try {
    await ledgerStore.saveLedger(ledgerId.value, {
      name: draft.name.trim(),
      subject_step_mode: draft.subject_step_mode,
      necessity_step_mode: draft.necessity_step_mode,
      default_currency_code: draft.default_currency_code,
    })
    showToast(t('common.saved'), 'success')
  } catch {
    showToast(t('errors.validationError'), 'error')
  } finally {
    isSaving.value = false
  }
}

async function loadShareCode() {
  shareError.value = ''
  try {
    shareCode.value = await getShareCode(ledgerId.value)
  } catch {
    shareError.value = t('errors.forbidden')
  }
}

async function loadMembers() {
  isMembersLoading.value = true
  try {
    members.value = await listMembers(ledgerId.value)
  } catch {
    members.value = []
  } finally {
    isMembersLoading.value = false
  }
}

async function toggleShareCode() {
  if (!shareCode.value) await loadShareCode()
  isShareCodeVisible.value = !isShareCodeVisible.value
}

async function loadShareRequests() {
  isShareRequestsLoading.value = true
  try {
    shareRequests.value = await listShareRequests(ledgerId.value)
  } catch {
    shareRequests.value = []
  } finally {
    isShareRequestsLoading.value = false
  }
}

const pendingRequests = computed(() => shareRequests.value.filter((request) => request.status === 'pending'))

async function approveRequest(requestId: string) {
  await approveShareRequest(ledgerId.value, requestId)
  await Promise.all([loadShareRequests(), loadMembers()])
  showToast(t('share.approved'), 'success')
}

async function rejectRequest(requestId: string) {
  await rejectShareRequest(ledgerId.value, requestId)
  await loadShareRequests()
  showToast(t('share.rejected'), 'success')
}

async function copyShareCode() {
  if (!isShareCodeVisible.value || !shareCode.value) return
  try {
    await navigator.clipboard.writeText(shareCode.value)
    showToast(t('share.copied'), 'success')
  } catch {
    showToast(t('errors.validationError'), 'error')
  }
}

function roleLabel(role: 'read-write' | 'read-only'): string {
  return role === 'read-only' ? t('share.readOnly') : t('share.readWrite')
}

function isLongMemberName(value: string): boolean {
  return value.length > 24
}

async function deleteCurrentLedger() {
  await ledgerStore.removeLedger(ledgerId.value)
  showDeleteConfirm.value = false
  await router.push({ name: 'ledger-list' })
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
.actions,
.section-heading,
.member-list li {
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

h2 {
  font-size: 1rem;
}

h3 {
  margin: 8px 0 0;
  font-size: 0.92rem;
}

.settings-form,
.section-block {
  display: grid;
  gap: 12px;
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

.section-block {
  margin-top: 12px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 14px;
  background: #fff;
}

.content-loading {
  min-height: 320px;
  margin-top: 12px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.settings-grid label {
  display: grid;
  gap: 6px;
  font-weight: 700;
}

.save-row {
  display: flex;
  justify-content: flex-end;
}

.action-block {
  padding: 10px 14px;
}

.action-block button {
  width: 100%;
  justify-self: center;
}

input,
select,
button {
  min-height: 44px;
  border-radius: 6px;
  font: inherit;
}

input,
select {
  border: 1px solid #b8c0cc;
  padding: 10px 12px;
}

button {
  border: 1px solid #c9d1dc;
  background: #fff;
  padding: 0 14px;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.primary-button {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
  font-weight: 700;
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
}

.member-list {
  display: grid;
  gap: 8px;
  padding: 0;
  list-style: none;
}

.request-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.share-panel {
  gap: 10px;
}

.heading-icons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.subsection-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
}

.round-icon-button {
  display: inline-grid;
  width: 38px;
  min-width: 38px;
  height: 38px;
  min-height: 38px;
  place-items: center;
  border-radius: 50%;
  padding: 0;
}

.round-icon-button.small {
  width: 34px;
  min-width: 34px;
  height: 34px;
  min-height: 34px;
}

.round-icon-button.spinning svg {
  animation: spin-refresh 0.8s linear infinite;
}

.request-list li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  border: 1px solid #eef2f7;
  border-radius: 8px;
  padding: 10px;
}

.request-list li > div:first-child {
  display: grid;
  min-width: 0;
  gap: 2px;
}

.request-list small,
.member-link small {
  color: #607086;
}

.member-link > .member-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-link small {
  justify-self: end;
  white-space: nowrap;
}

.request-actions {
  display: flex;
  gap: 8px;
}

.share-code-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 44px;
  gap: 8px;
  align-items: center;
}

.icon-action {
  display: inline-grid;
  width: 44px;
  min-width: 44px;
  height: 44px;
  min-height: 44px;
  place-items: center;
  padding: 0;
}

.member-link {
  display: grid;
  width: 100%;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  border-color: #eef2f7;
  padding: 0 12px;
  text-align: left;
}

.member-name {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
}

.member-name-text {
  display: inline-block;
  padding-right: 32px;
}

.member-link:hover .member-name-text.marquee,
.member-link:focus-visible .member-name-text.marquee {
  animation: marquee-name 7s linear infinite;
}

code {
  display: block;
  overflow-wrap: anywhere;
  border-radius: 6px;
  background: #eef2f7;
  padding: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  line-height: 1.5;
}

.danger {
  border-color: #f3b8b3;
}

.danger-button {
  border-color: #dc2626;
  background: #dc2626;
  color: #fff;
  font-weight: 700;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgb(15 23 42 / 42%);
}

.confirm-dialog {
  display: grid;
  width: min(100%, 420px);
  gap: 14px;
  border-radius: 8px;
  padding: 18px;
  background: #fff;
  box-shadow: 0 24px 60px rgb(15 23 42 / 22%);
}

.confirm-dialog p {
  margin-bottom: 0;
  color: #334155;
}

.dialog-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.muted {
  color: #607086;
}

@media (max-width: 640px) {
  .topbar,
  .actions,
  .member-list li {
    align-items: stretch;
    flex-direction: column;
  }

  .title-row {
    align-items: center;
    flex-direction: row;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .request-list li {
    grid-template-columns: 1fr;
  }

  .request-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@keyframes marquee-name {
  0%,
  12% {
    transform: translateX(0);
  }
  88%,
  100% {
    transform: translateX(-45%);
  }
}

@keyframes spin-refresh {
  to {
    transform: rotate(360deg);
  }
}
</style>
