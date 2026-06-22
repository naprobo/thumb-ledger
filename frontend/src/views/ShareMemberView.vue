<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="title-row">
        <button type="button" class="back-button" :aria-label="t('common.back')" :title="t('common.back')" @click="router.push({ name: 'ledger-settings', params: { id: ledgerId } })">
          <ChevronLeft :size="24" aria-hidden="true" />
        </button>
        <h1>{{ t('share.memberDetail') }}</h1>
      </div>
    </header>

    <div v-if="toastMessage" :class="['toast', toastKind]" role="status">{{ toastMessage }}</div>
    <AppLoadingPanel v-if="isLoading" class="content-loading" />

    <section v-else-if="member" class="section-block">
      <div class="member-heading">
        <strong>{{ member.display_name || member.email || member.user_id }}</strong>
        <small>{{ member.email || member.user_id }}</small>
      </div>

      <form class="member-form" @submit.prevent="saveRole">
        <label>
          <span>{{ t('share.role') }}</span>
          <select v-model="role">
            <option value="read-write">{{ t('share.readWrite') }}</option>
            <option value="read-only">{{ t('share.readOnly') }}</option>
          </select>
        </label>
        <button class="primary-button" type="submit" :disabled="isSaving">{{ t('common.save') }}</button>
      </form>
    </section>

    <section v-if="member" class="section-block danger-zone">
      <h2>{{ t('share.stopSharing') }}</h2>
      <button type="button" class="danger-button" @click="showRemoveConfirm = true">{{ t('share.removeMember') }}</button>
    </section>

    <div v-if="showRemoveConfirm" class="modal-backdrop" role="presentation" @click.self="showRemoveConfirm = false">
      <section class="confirm-dialog" role="dialog" aria-modal="true" :aria-label="t('share.removeMember')">
        <h2>{{ t('share.removeMember') }}</h2>
        <p>{{ t('share.removeConfirm') }}</p>
        <div class="dialog-actions">
          <button type="button" @click="showRemoveConfirm = false">{{ t('common.cancel') }}</button>
          <button type="button" class="danger-button" :disabled="isRemoving" @click="removeCurrentMember">{{ t('share.removeMember') }}</button>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft } from '@lucide/vue'

import { listMembers, removeMember, updateMemberRole, type LedgerMember } from '@/api/ledgers'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const ledgerId = computed(() => String(route.params.id))
const userId = computed(() => String(route.params.userId))
const member = ref<LedgerMember | null>(null)
const role = ref<'read-write' | 'read-only'>('read-write')
const isLoading = ref(true)
const isSaving = ref(false)
const isRemoving = ref(false)
const showRemoveConfirm = ref(false)
const toastMessage = ref('')
const toastKind = ref<'success' | 'error'>('success')
let toastTimer: number | undefined

onMounted(loadMember)

async function loadMember() {
  isLoading.value = true
  try {
    const members = await listMembers(ledgerId.value)
    member.value = members.find((item) => item.user_id === userId.value) || null
    if (member.value) role.value = member.value.role
  } finally {
    isLoading.value = false
  }
}

async function saveRole() {
  isSaving.value = true
  try {
    member.value = await updateMemberRole(ledgerId.value, userId.value, role.value)
    showToast(t('common.saved'), 'success')
  } catch {
    showToast(t('errors.validationError'), 'error')
  } finally {
    isSaving.value = false
  }
}

async function removeCurrentMember() {
  isRemoving.value = true
  try {
    await removeMember(ledgerId.value, userId.value)
    showRemoveConfirm.value = false
    await router.push({ name: 'ledger-settings', params: { id: ledgerId.value } })
  } finally {
    isRemoving.value = false
  }
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
  width: min(100%, 760px);
  margin: 0 auto;
  padding: 24px clamp(12px, 3vw, 36px);
}

.topbar,
.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title-row {
  justify-content: flex-start;
}

.back-button {
  display: inline-grid;
  width: 44px;
  min-width: 44px;
  height: 44px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  font-size: 1.35rem;
}

h2 {
  font-size: 1rem;
}

.section-block,
.content-loading {
  margin-top: 12px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
}

.section-block {
  display: grid;
  gap: 12px;
  padding: 14px;
}

.content-loading {
  min-height: 320px;
}

.member-heading,
.member-form,
label {
  display: grid;
  gap: 6px;
}

.member-heading small {
  color: #607086;
}

label {
  font-weight: 700;
}

select,
button {
  min-height: 44px;
  border-radius: 6px;
  font: inherit;
}

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

.danger-zone {
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

.toast {
  position: fixed;
  top: 64px;
  left: 50%;
  z-index: 30;
  width: min(calc(100% - 32px), 520px);
  transform: translateX(-50%);
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
</style>
