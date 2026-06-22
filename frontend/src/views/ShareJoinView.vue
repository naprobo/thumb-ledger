<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="title-row">
        <button type="button" class="back-button" :aria-label="t('common.back')" :title="t('common.back')" @click="router.push({ name: 'ledger-list' })">
          <ChevronLeft :size="24" aria-hidden="true" />
        </button>
        <h1>{{ t('share.joinTitle') }}</h1>
      </div>
    </header>

    <div v-if="toastMessage" :class="['toast', toastKind]" role="status">{{ toastMessage }}</div>

    <section class="section-block">
      <form class="join-form" @submit.prevent="submitRequest">
        <label>
          <span>{{ t('share.shareCode') }}</span>
          <input v-model.trim="shareCode" autocomplete="off" maxlength="80" required />
        </label>
        <label>
          <span>{{ t('share.requestRole') }}</span>
          <select v-model="role">
            <option value="read-write">{{ t('share.readWrite') }}</option>
            <option value="read-only">{{ t('share.readOnly') }}</option>
          </select>
        </label>
        <button class="primary-button" type="submit" :disabled="isSubmitting">{{ t('share.submitRequest') }}</button>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ChevronLeft } from '@lucide/vue'

import { createShareRequest } from '@/api/ledgers'

const { t } = useI18n()
const router = useRouter()
const shareCode = ref('')
const role = ref<'read-write' | 'read-only'>('read-write')
const isSubmitting = ref(false)
const toastMessage = ref('')
const toastKind = ref<'success' | 'error'>('success')
let toastTimer: number | undefined

async function submitRequest() {
  if (!shareCode.value.trim()) return
  isSubmitting.value = true
  try {
    await createShareRequest(shareCode.value.trim(), role.value)
    shareCode.value = ''
    await router.push({ name: 'ledger-list' })
  } catch {
    showToast(t('errors.validationError'), 'error')
  } finally {
    isSubmitting.value = false
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

h1 {
  margin: 0;
  font-size: 1.35rem;
}

.section-block {
  display: grid;
  gap: 12px;
  margin-top: 12px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 14px;
  background: #fff;
}

.join-form {
  display: grid;
  gap: 12px;
}

label {
  display: grid;
  gap: 6px;
  font-weight: 700;
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
