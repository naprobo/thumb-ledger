<template>
  <header v-if="authStore.isAuthenticated" class="app-header">
    <button type="button" class="brand-button" @click="router.push({ name: 'ledger-list' })">
      {{ t('app.title') }}
    </button>
    <details ref="menuRef" class="user-menu">
      <summary :aria-label="menuLabel" :title="menuLabel">
        <Menu :size="22" aria-hidden="true" />
      </summary>
      <div class="menu-panel">
        <p>{{ authStore.user?.email }}</p>
        <button type="button" @click="goTo('ledger-list')">
          {{ t('nav.ledgers') }}
        </button>
        <button type="button" @click="goTo('suggestions')">
          {{ t('nav.suggestions') }}
        </button>
        <label class="language-select">
          <span>{{ t('settings.language') }}</span>
          <select :value="locale" @change="changeLanguage">
            <option v-for="option in localeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <button
          v-if="authStore.isAdmin"
          type="button"
          @click="goTo('admin')"
        >
          {{ t('nav.admin') }}
        </button>
        <button type="button" @click="logout">
          {{ t('nav.logout') }}
        </button>
      </div>
    </details>
  </header>
  <router-view />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, type RouteRecordName } from 'vue-router'
import { Menu } from '@lucide/vue'

import { useAuthStore } from '@/stores/auth'
import { SUPPORTED_LOCALES, type SupportedLocale } from '@/i18n'

const authStore = useAuthStore()
const router = useRouter()
const { t, locale } = useI18n()
const menuRef = ref<HTMLDetailsElement | null>(null)
const menuLabel = computed(() => authStore.user?.email?.slice(0, 1).toUpperCase() || 'Menu')
const localeOptions: Array<{ value: SupportedLocale; label: string }> = SUPPORTED_LOCALES.map((value) => ({
  value,
  label: value === 'zh-CN' ? '简体中文' : value === 'ja' ? '日本語' : 'English',
}))

async function changeLanguage(event: Event) {
  const nextLocale = (event.target as HTMLSelectElement).value as SupportedLocale
  if (!SUPPORTED_LOCALES.includes(nextLocale)) return
  await authStore.updatePreferredLanguage(nextLocale)
}

function closeMenu() {
  if (menuRef.value) menuRef.value.open = false
}

async function goTo(name: RouteRecordName) {
  closeMenu()
  await router.push({ name })
}

function handleDocumentPointerDown(event: PointerEvent) {
  if (!menuRef.value?.open) return
  const target = event.target
  if (target instanceof Node && menuRef.value.contains(target)) return
  closeMenu()
}

function logout() {
  closeMenu()
  authStore.logout()
  router.push({ name: 'login' })
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 52px;
  border-bottom: 1px solid #d9dee7;
  padding: 0 16px;
  background: #fff;
}

.brand-button,
.user-menu summary,
.menu-panel button,
.language-select select {
  min-height: 40px;
  border: 0;
  background: transparent;
  color: #111827;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.user-menu {
  position: relative;
}

.user-menu summary {
  display: grid;
  place-items: center;
  width: 40px;
  border: 1px solid #c9d1dc;
  border-radius: 50%;
  list-style: none;
}

.user-menu summary::-webkit-details-marker {
  display: none;
}

.menu-panel {
  position: absolute;
  top: 48px;
  right: 0;
  display: grid;
  min-width: 220px;
  gap: 4px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 8px;
  background: #fff;
  box-shadow: 0 18px 40px rgb(15 23 42 / 14%);
}

.menu-panel p {
  margin: 0;
  overflow-wrap: anywhere;
  padding: 8px 10px;
  color: #607086;
  font-size: 0.9rem;
}

.language-select {
  display: grid;
  gap: 6px;
  padding: 8px 10px;
}

.language-select span {
  color: #607086;
  font-size: 0.85rem;
  font-weight: 700;
}

.language-select select {
  width: 100%;
  border: 1px solid #c9d1dc;
  border-radius: 6px;
  padding: 0 8px;
  font-weight: 700;
}

.menu-panel button {
  border-radius: 6px;
  padding: 0 10px;
  text-align: left;
}

.menu-panel button:hover {
  background: #f1f5f9;
}
</style>
