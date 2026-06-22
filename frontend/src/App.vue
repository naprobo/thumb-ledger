<template>
  <v-app>
    <header v-if="authStore.isAuthenticated" class="app-header">
      <button type="button" class="brand-button" @click="router.push({ name: 'ledger-list' })">
        {{ t('app.title') }}
      </button>
      <div class="header-actions">
        <button
          type="button"
          class="icon-button notification-button"
          :aria-label="t('notifications.title')"
          :title="t('notifications.title')"
          @click="router.push({ name: 'notifications' })"
        >
          <Bell :size="21" aria-hidden="true" />
          <span v-if="unreadCount > 0" class="unread-dot" aria-hidden="true" />
        </button>
        <details ref="menuRef" class="user-menu">
          <summary :aria-label="menuLabel" :title="menuLabel">
            <Menu :size="22" aria-hidden="true" />
          </summary>
        <div class="menu-panel">
          <p>{{ authStore.user?.display_name || authStore.user?.email }}</p>
          <button type="button" @click="goTo('ledger-list')">
            {{ t('nav.ledgers') }}
          </button>
          <button type="button" @click="goTo('profile')">
            {{ t('nav.profile') }}
          </button>
          <button type="button" @click="goTo('share-join')">
            {{ t('nav.joinShare') }}
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
      </div>
    </header>
    <router-view />
  </v-app>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, type RouteRecordName } from 'vue-router'
import { Bell, Menu } from '@lucide/vue'

import { useAuthStore } from '@/stores/auth'
import { SUPPORTED_LOCALES, type SupportedLocale } from '@/i18n'
import { getUnreadNotificationCount } from '@/api/notifications'

const authStore = useAuthStore()
const router = useRouter()
const { t, locale } = useI18n()
const menuRef = ref<HTMLDetailsElement | null>(null)
const unreadCount = ref(0)
const menuLabel = computed(() => authStore.user?.email?.slice(0, 1).toUpperCase() || 'Menu')
const localeOptions: Array<{ value: SupportedLocale; label: string }> = SUPPORTED_LOCALES.map((value) => ({
  value,
  label: value === 'zh-CN' ? '简体中文' : value === 'ja' ? '日本語' : 'English',
}))
const localizedSiteMeta: Record<SupportedLocale, { title: string; manifest: string; description: string }> = {
  'zh-CN': {
    title: '拇指账本',
    manifest: '/manifest.zh-CN.webmanifest',
    description: '拇指账本是面向手机单手操作的多语言记账应用，支持预算、共享账本、周期性消费和通知。',
  },
  ja: {
    title: '親指家計簿',
    manifest: '/manifest.ja.webmanifest',
    description: '親指家計簿は片手で素早く記録できる多言語家計簿アプリです。予算、共有家計簿、定期取引、通知に対応します。',
  },
  en: {
    title: 'Thumb Ledger',
    manifest: '/manifest.en.webmanifest',
    description: 'Thumb Ledger is a mobile-first multilingual bookkeeping app for fast expense entry, budgets, shared ledgers, recurring expenses, and notifications.',
  },
}

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

async function refreshUnreadCount() {
  if (!authStore.isAuthenticated) {
    unreadCount.value = 0
    return
  }
  try {
    unreadCount.value = await getUnreadNotificationCount()
  } catch {
    unreadCount.value = 0
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  refreshUnreadCount()
  syncSiteMeta(locale.value as SupportedLocale)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})

watch(
  () => router.currentRoute.value.fullPath,
  () => refreshUnreadCount(),
)

watch(
  () => locale.value,
  (value) => syncSiteMeta(value as SupportedLocale),
  { immediate: true },
)

function syncSiteMeta(value: SupportedLocale) {
  const meta = localizedSiteMeta[value] || localizedSiteMeta['zh-CN']
  document.documentElement.lang = value
  document.title = meta.title
  setMetaContent('application-name', meta.title)
  setMetaContent('apple-mobile-web-app-title', meta.title)
  setMetaContent('description', meta.description)
  const manifest = document.querySelector<HTMLLinkElement>('link[rel="manifest"]')
  if (manifest) manifest.href = meta.manifest
}

function setMetaContent(name: string, content: string) {
  const element = document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)
  if (element) element.content = content
}
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-button,
.icon-button,
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

.icon-button,
.user-menu summary {
  display: grid;
  place-items: center;
  width: 40px;
  min-width: 40px;
  height: 40px;
  border: 1px solid #c9d1dc;
  border-radius: 50%;
  list-style: none;
}

.notification-button {
  position: relative;
  padding: 0;
}

.unread-dot {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 9px;
  height: 9px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: #dc2626;
}

.user-menu summary::-webkit-details-marker {
  display: none;
}

.menu-panel {
  position: absolute;
  top: 48px;
  right: 0;
  display: grid;
  width: 240px;
  max-width: calc(100vw - 24px);
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
  box-sizing: border-box;
  width: 100%;
  border: 1px solid #c9d1dc;
  border-radius: 6px;
  padding: 0 32px 0 10px;
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
