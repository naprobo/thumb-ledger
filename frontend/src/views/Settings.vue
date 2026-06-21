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

    <section v-if="ledger" class="section-block">
      <div class="section-heading">
        <h2>{{ t('settings.share') }}</h2>
        <button type="button" @click="loadShareCode">{{ t('settings.shareCode') }}</button>
      </div>
      <code v-if="shareCode">{{ shareCode }}</code>
      <p v-if="shareError" class="muted">{{ shareError }}</p>
    </section>

    <section v-if="ledger" class="section-block">
      <div class="section-heading">
        <h2>{{ t('settings.members') }}</h2>
        <button type="button" @click="loadMembers">{{ t('common.refresh') }}</button>
      </div>
      <ul v-if="members.length" class="member-list">
        <li v-for="member in members" :key="member.id">
          <span>{{ member.user_id }} · {{ member.role }}</span>
          <button type="button" @click="removeSharedMember(member.user_id)">{{ t('admin.delete') }}</button>
        </li>
      </ul>
      <p v-else class="muted">{{ t('settings.noMembers') }}</p>
    </section>

    <section v-if="ledger" class="section-block danger">
      <h2>{{ t('settings.dangerZone') }}</h2>
      <button type="button" @click="showDeleteConfirm = true">{{ t('ledger.delete') }}</button>
    </section>

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
import { ChevronLeft } from '@lucide/vue'

import { getShareCode, listMembers, removeMember, type LedgerMember, type NecessityStepMode, type SubjectStepMode } from '@/api/ledgers'
import { CURRENCY_OPTIONS, currencyOptionLabel } from '@/constants/currencies'
import { useLedgerStore } from '@/stores/ledgers'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
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
const shareCode = ref('')
const shareError = ref('')
const isSaving = ref(false)
const toastMessage = ref('')
const toastKind = ref<'success' | 'error'>('success')
const showDeleteConfirm = ref(false)
let toastTimer: number | undefined

onMounted(async () => {
  const loaded = await ledgerStore.fetchLedger(ledgerId.value)
  draft.name = loaded.name
  draft.subject_step_mode = loaded.subject_step_mode
  draft.necessity_step_mode = loaded.necessity_step_mode
  draft.default_currency_code = loaded.default_currency_code
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
  try {
    members.value = await listMembers(ledgerId.value)
  } catch {
    members.value = []
  }
}

async function removeSharedMember(userId: string) {
  await removeMember(ledgerId.value, userId)
  members.value = members.value.filter((member) => member.user_id !== userId)
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

code {
  overflow-wrap: anywhere;
  border-radius: 6px;
  background: #eef2f7;
  padding: 10px;
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
  .section-heading,
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
}
</style>
