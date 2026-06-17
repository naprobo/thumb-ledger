<template>
  <main class="auth-page">
    <section class="auth-panel" aria-live="polite">
      <h1>{{ pageTitle }}</h1>

      <form v-if="currentPage === 'login'" class="auth-form" @submit.prevent="handleLogin">
        <label>
          <span>{{ t('auth.email') }}</span>
          <input v-model.trim="email" type="email" autocomplete="email" required maxlength="255" />
        </label>

        <label>
          <span>{{ t('auth.password') }}</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            minlength="8"
            maxlength="128"
          />
        </label>

        <button class="primary-button" type="submit" :disabled="isSubmitting">
          {{ t('auth.login') }}
        </button>
        <button class="link-button" type="button" @click="goTo('register')">
          {{ t('auth.noAccount') }}
        </button>
        <button class="link-button" type="button" @click="goTo('password-reset')">
          {{ t('auth.forgotPassword') }}
        </button>
      </form>

      <form v-else-if="currentPage === 'register'" class="auth-form" @submit.prevent="handleRegister">
        <label>
          <span>{{ t('auth.email') }}</span>
          <input v-model.trim="email" type="email" autocomplete="email" required maxlength="255" />
        </label>

        <label>
          <span>{{ t('auth.password') }}</span>
          <input
            v-model="password"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
          />
        </label>

        <button class="primary-button" type="submit" :disabled="isSubmitting">
          {{ t('auth.register') }}
        </button>
        <button class="link-button" type="button" @click="goTo('login')">
          {{ t('auth.hasAccount') }}
        </button>
      </form>

      <form v-else-if="currentPage === 'reset'" class="auth-form" @submit.prevent="handleResetRequest">
        <label>
          <span>{{ t('auth.email') }}</span>
          <input v-model.trim="email" type="email" autocomplete="email" required maxlength="255" />
        </label>

        <button class="primary-button" type="submit" :disabled="isSubmitting">
          {{ t('auth.sendResetLink') }}
        </button>
        <button class="link-button" type="button" @click="goTo('login')">
          {{ t('auth.hasAccount') }}
        </button>
      </form>

      <form v-else class="auth-form" @submit.prevent="handleResetConfirm">
        <label>
          <span>{{ t('auth.resetToken') }}</span>
          <input v-model.trim="resetToken" type="text" autocomplete="one-time-code" required maxlength="255" />
        </label>

        <label>
          <span>{{ t('auth.newPassword') }}</span>
          <input
            v-model="newPassword"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
          />
        </label>

        <label>
          <span>{{ t('auth.confirmPassword') }}</span>
          <input
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
          />
        </label>

        <button class="primary-button" type="submit" :disabled="isSubmitting">
          {{ t('auth.resetPassword') }}
        </button>
        <button class="link-button" type="button" @click="goTo('login')">
          {{ t('auth.hasAccount') }}
        </button>
      </form>

      <p v-if="statusMessage" class="status">{{ statusMessage }}</p>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter, type RouteRecordName } from 'vue-router'

import { apiClient } from '@/api'
import { useAuthStore } from '@/stores/auth'

type AuthPage = 'login' | 'register' | 'reset' | 'reset-confirm'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentPage = ref<AuthPage>(pageFromRoute(route.name))
const email = ref('')
const password = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const resetToken = ref(readTokenFromRoute())
const isSubmitting = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')

const pageTitle = computed(() => {
  if (currentPage.value === 'register') return t('auth.register')
  if (currentPage.value === 'reset' || currentPage.value === 'reset-confirm') return t('auth.resetPassword')
  return t('auth.login')
})

watch(
  () => route.name,
  (name) => {
    currentPage.value = pageFromRoute(name)
    resetToken.value = readTokenFromRoute()
    statusMessage.value = ''
    errorMessage.value = ''
  },
)

function pageFromRoute(name: RouteRecordName | null | undefined): AuthPage {
  if (name === 'register') return 'register'
  if (name === 'password-reset') return 'reset'
  if (name === 'password-reset-confirm') return 'reset-confirm'
  return 'login'
}

function readTokenFromRoute(): string {
  return typeof route.query.token === 'string' ? route.query.token : ''
}

function goTo(name: 'login' | 'register' | 'password-reset') {
  router.push({ name })
}

async function runSubmitting(action: () => Promise<void>) {
  isSubmitting.value = true
  statusMessage.value = ''
  errorMessage.value = ''
  try {
    await action()
  } finally {
    isSubmitting.value = false
  }
}

async function handleLogin() {
  await runSubmitting(async () => {
    try {
      await authStore.login(email.value, password.value)
      await router.push((route.query.redirect as string | undefined) || { name: 'ledger-list' })
    } catch {
      errorMessage.value = t('errors.invalidCredentials')
    }
  })
}

async function handleRegister() {
  await runSubmitting(async () => {
    try {
      await authStore.register(email.value, password.value)
      statusMessage.value = t('auth.registerSuccess')
      password.value = ''
      await router.push({ name: 'login' })
    } catch {
      errorMessage.value = t('errors.emailAlreadyUsed')
    }
  })
}

async function handleResetRequest() {
  await runSubmitting(async () => {
    try {
      await apiClient.post('/auth/password-reset/request', { email: email.value })
    } finally {
      statusMessage.value = t('auth.resetEmailSent')
    }
  })
}

async function handleResetConfirm() {
  await runSubmitting(async () => {
    if (newPassword.value !== confirmPassword.value) {
      errorMessage.value = t('errors.passwordMismatch')
      return
    }
    try {
      await apiClient.post('/auth/password-reset/confirm', {
        token: resetToken.value,
        new_password: newPassword.value,
      })
      statusMessage.value = t('auth.resetSuccess')
      resetToken.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
      await router.push({ name: 'login' })
    } catch {
      errorMessage.value = t('errors.invalidToken')
    }
  })
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #f6f7f9;
  color: #1f2933;
}

.auth-panel {
  width: min(100%, 420px);
  padding: 28px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgb(31 41 51 / 8%);
}

h1 {
  margin: 0 0 24px;
  font-size: 1.6rem;
  line-height: 1.2;
}

.auth-form {
  display: grid;
  gap: 16px;
}

label {
  display: grid;
  gap: 6px;
  font-weight: 600;
}

input {
  min-height: 44px;
  width: 100%;
  border: 1px solid #b8c0cc;
  border-radius: 6px;
  padding: 10px 12px;
  font: inherit;
}

input:focus {
  border-color: #2563eb;
  outline: 3px solid rgb(37 99 235 / 18%);
}

button {
  min-height: 44px;
  border-radius: 6px;
  font: inherit;
  cursor: pointer;
}

button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.primary-button {
  border: 0;
  background: #2563eb;
  color: white;
  font-weight: 700;
}

.link-button {
  border: 1px solid transparent;
  background: transparent;
  color: #1d4ed8;
  text-align: left;
}

.status,
.error {
  margin: 16px 0 0;
  line-height: 1.4;
}

.status {
  color: #166534;
}

.error {
  color: #b42318;
}
</style>
