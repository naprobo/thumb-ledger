<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="title-row">
        <button type="button" class="back-button" :aria-label="t('common.back')" :title="t('common.back')" @click="router.push({ name: 'ledger-list' })">
          <ChevronLeft :size="24" aria-hidden="true" />
        </button>
        <h1>{{ t('notifications.title') }}</h1>
      </div>
      <button type="button" :disabled="!notifications.length || isMarking" @click="markAllRead">
        {{ t('notifications.markAllRead') }}
      </button>
    </header>

    <AppLoadingPanel v-if="isLoading" class="content-loading" />

    <section v-else class="section-block">
      <p v-if="!notifications.length" class="muted">{{ t('notifications.empty') }}</p>
      <ul v-else class="notification-list">
        <li v-for="notification in notifications" :key="notification.id" :class="{ unread: !notification.read_at }">
          <button type="button" class="notification-item" @click="openNotification(notification)">
            <span class="status-dot" aria-hidden="true" />
            <span>
              <strong>{{ notificationTitle(notification) }}</strong>
              <small>{{ notificationMessage(notification) }}</small>
            </span>
            <time>{{ formatDate(notification.created_at) }}</time>
          </button>
        </li>
      </ul>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ChevronLeft } from '@lucide/vue'

import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationItem,
} from '@/api/notifications'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'

const { t, locale } = useI18n()
const router = useRouter()
const notifications = ref<NotificationItem[]>([])
const isLoading = ref(true)
const isMarking = ref(false)

onMounted(loadNotifications)

async function loadNotifications() {
  isLoading.value = true
  try {
    notifications.value = await listNotifications()
  } finally {
    isLoading.value = false
  }
}

async function openNotification(notification: NotificationItem) {
  if (!notification.read_at) {
    const updated = await markNotificationRead(notification.id)
    notifications.value = notifications.value.map((item) => (item.id === updated.id ? updated : item))
  }
  const ledgerId = typeof notification.payload?.ledger_id === 'string' ? notification.payload.ledger_id : ''
  const transactionId = typeof notification.payload?.transaction_id === 'string' ? notification.payload.transaction_id : ''
  if (notification.type === 'LEDGER_TRANSACTION_CREATED' && ledgerId && transactionId) {
    await router.push({ name: 'transaction-detail', params: { id: ledgerId, transactionId } })
  } else if (notification.type === 'LEDGER_SHARE_REQUESTED' && ledgerId) {
    await router.push({ name: 'ledger-settings', params: { id: ledgerId } })
  } else if (ledgerId) {
    await router.push({ name: 'ledger-detail', params: { id: ledgerId } })
  }
}

async function markAllRead() {
  isMarking.value = true
  try {
    await markAllNotificationsRead()
    notifications.value = notifications.value.map((notification) => ({
      ...notification,
      status: 'read',
      read_at: notification.read_at || new Date().toISOString(),
    }))
  } finally {
    isMarking.value = false
  }
}

function notificationTitle(notification: NotificationItem): string {
  const key = `notifications.types.${notification.type}`
  const translated = t(key)
  return translated === key ? t('notifications.types.default') : translated
}

function notificationMessage(notification: NotificationItem): string {
  const ledgerName = stringPayload(notification, 'ledger_name') || t('ledger.name')
  const userName = stringPayload(notification, 'requester_display_name') || stringPayload(notification, 'owner_display_name') || ''
  const recorderName = stringPayload(notification, 'recorder_display_name') || ''
  const role = stringPayload(notification, 'role')
  if (notification.type === 'LEDGER_SHARE_REQUESTED') return t('notifications.messages.shareRequested', { user: userName, ledger: ledgerName })
  if (notification.type === 'LEDGER_SHARE_PENDING') return t('notifications.messages.sharePending', { ledger: ledgerName, role: roleLabel(role) })
  if (notification.type === 'LEDGER_SHARE_APPROVED') return t('notifications.messages.shareApproved', { ledger: ledgerName })
  if (notification.type === 'LEDGER_SHARE_REJECTED') return t('notifications.messages.shareRejected', { ledger: ledgerName })
  if (notification.type === 'LEDGER_MEMBER_ROLE_CHANGED') return t('notifications.messages.roleChanged', { ledger: ledgerName, role: roleLabel(role) })
  if (notification.type === 'LEDGER_SHARED_USER_REMOVED') return t('notifications.messages.removed', { ledger: ledgerName })
  if (notification.type === 'LEDGER_TRANSACTION_CREATED') return t('notifications.messages.transactionCreated', { user: recorderName, ledger: ledgerName })
  return ledgerName
}

function stringPayload(notification: NotificationItem, key: string): string {
  const value = notification.payload?.[key]
  return typeof value === 'string' ? value : ''
}

function roleLabel(role: string): string {
  if (role === 'read-only') return t('share.readOnly')
  if (role === 'read-write') return t('share.readWrite')
  return role || '-'
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(locale.value, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}
</script>

<style scoped>
.page-shell {
  width: min(100%, 960px);
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

button {
  min-height: 44px;
  border: 1px solid #c9d1dc;
  border-radius: 6px;
  background: #fff;
  padding: 0 14px;
  font: inherit;
  cursor: pointer;
}

.section-block,
.content-loading {
  margin-top: 12px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
}

.section-block {
  padding: 10px;
}

.content-loading {
  min-height: 320px;
}

.notification-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.notification-item {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr) auto;
  align-items: center;
  width: 100%;
  min-height: 68px;
  gap: 10px;
  border-color: transparent;
  padding: 10px;
  text-align: left;
}

.notification-item:hover {
  background: #f8fafc;
}

.notification-item span:nth-child(2) {
  display: grid;
  min-width: 0;
  gap: 3px;
}

.notification-item small {
  overflow-wrap: anywhere;
  color: #607086;
}

.notification-item time {
  color: #607086;
  font-size: 0.82rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: transparent;
}

.unread .status-dot {
  background: #dc2626;
}

.unread strong {
  color: #111827;
}

.muted {
  margin: 0;
  padding: 14px;
  color: #607086;
}

@media (max-width: 640px) {
  .topbar {
    align-items: stretch;
    flex-direction: column;
  }

  .title-row {
    align-items: center;
    flex-direction: row;
  }

  .notification-item {
    grid-template-columns: 14px minmax(0, 1fr);
  }

  .notification-item time {
    grid-column: 2;
  }
}
</style>
