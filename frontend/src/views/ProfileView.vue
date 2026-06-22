<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="title-row">
        <button type="button" class="back-button" :aria-label="t('common.back')" :title="t('common.back')" @click="router.push({ name: 'ledger-list' })">
          <ChevronLeft :size="24" aria-hidden="true" />
        </button>
        <h1>{{ t('profile.title') }}</h1>
      </div>
    </header>

    <div v-if="toastMessage" :class="['toast', toastKind]" role="status">{{ toastMessage }}</div>

    <section class="section-block">
      <h2>{{ t('profile.basicInfo') }}</h2>
      <form class="profile-form" @submit.prevent="saveProfile">
        <label>
          <span>{{ t('auth.email') }}</span>
          <input :value="authStore.user?.email" disabled />
        </label>
        <label>
          <span>{{ t('auth.nickname') }}</span>
          <input v-model.trim="nickname" maxlength="50" />
        </label>
        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="isSavingProfile">{{ t('common.save') }}</button>
        </div>
      </form>
    </section>

    <section class="section-block">
      <h2>{{ t('profile.changePassword') }}</h2>
      <form class="profile-form" @submit.prevent="changePassword">
        <label>
          <span>{{ t('profile.currentPassword') }}</span>
          <input v-model="currentPassword" type="password" autocomplete="current-password" maxlength="128" required />
        </label>
        <label>
          <span>{{ t('auth.newPassword') }}</span>
          <input v-model="newPassword" type="password" autocomplete="new-password" minlength="8" maxlength="128" required />
        </label>
        <label>
          <span>{{ t('auth.confirmPassword') }}</span>
          <input v-model="confirmPassword" type="password" autocomplete="new-password" minlength="8" maxlength="128" required />
        </label>
        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="isChangingPassword">{{ t('profile.changePassword') }}</button>
        </div>
      </form>
    </section>

    <section class="section-block danger-zone">
      <h2>{{ t('profile.dangerZone') }}</h2>
      <p>{{ t('profile.accountDeletionHint') }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ChevronLeft } from '@lucide/vue'

import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const nickname = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isSavingProfile = ref(false)
const isChangingPassword = ref(false)
const toastMessage = ref('')
const toastKind = ref<'success' | 'error'>('success')
let toastTimer: number | undefined

onMounted(() => {
  nickname.value = authStore.user?.nickname || ''
})

async function saveProfile() {
  isSavingProfile.value = true
  try {
    await authStore.updateProfile({ nickname: nickname.value || null })
    showToast(t('common.saved'), 'success')
  } catch {
    showToast(t('errors.validationError'), 'error')
  } finally {
    isSavingProfile.value = false
  }
}

async function changePassword() {
  if (newPassword.value !== confirmPassword.value) {
    showToast(t('errors.passwordMismatch'), 'error')
    return
  }
  isChangingPassword.value = true
  try {
    await authStore.changePassword(currentPassword.value, newPassword.value)
    showToast(t('profile.passwordChanged'), 'success')
    await router.push({ name: 'login' })
  } catch {
    showToast(t('errors.invalidCredentials'), 'error')
  } finally {
    isChangingPassword.value = false
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
  width: min(100%, 960px);
  margin: 0 auto;
  padding: 24px clamp(12px, 3vw, 36px);
}

.topbar,
.title-row,
.form-actions {
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

.section-block {
  display: grid;
  gap: 12px;
  margin-top: 12px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 14px;
  background: #fff;
}

.profile-form {
  display: grid;
  gap: 12px;
}

label {
  display: grid;
  gap: 6px;
  font-weight: 700;
}

input,
button {
  min-height: 44px;
  border-radius: 6px;
  font: inherit;
}

input {
  border: 1px solid #b8c0cc;
  padding: 10px 12px;
}

input:disabled {
  background: #f8fafc;
  color: #607086;
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

.danger-zone p {
  margin-bottom: 0;
  color: #607086;
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
