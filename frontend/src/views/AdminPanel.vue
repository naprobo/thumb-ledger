<template>
  <main class="page-shell">
    <header class="topbar">
      <h1>{{ t('admin.title') }}</h1>
      <button type="button" @click="refresh">{{ t('common.refresh') }}</button>
    </header>

    <AppLoadingPanel v-if="isInitialLoading" class="admin-loading" />

    <template v-else>
    <section class="stats-grid">
      <article>
        <span>{{ t('admin.totalUsers') }}</span>
        <strong>{{ stats?.total_users ?? '-' }}</strong>
      </article>
      <article>
        <span>{{ t('admin.totalLedgers') }}</span>
        <strong>{{ stats?.total_ledgers ?? '-' }}</strong>
      </article>
      <article>
        <span>{{ t('admin.totalTransactions') }}</span>
        <strong>{{ stats?.total_transactions ?? '-' }}</strong>
      </article>
    </section>

    <section class="users-panel">
      <div class="section-heading">
        <h2>{{ t('admin.users') }}</h2>
        <span>{{ users.length }}</span>
      </div>

      <table v-if="users.length">
        <thead>
          <tr>
            <th>{{ t('auth.email') }}</th>
            <th>{{ t('admin.registeredAt') }}</th>
            <th>{{ t('admin.status') }}</th>
            <th>{{ t('nav.admin') }}</th>
            <th>{{ t('common.save') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.email }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <span :class="['status-pill', user.is_active ? 'active' : 'disabled']">
                {{ user.is_active ? t('admin.enabled') : t('admin.disabled') }}
              </span>
            </td>
            <td>{{ user.is_admin ? t('admin.yes') : t('admin.no') }}</td>
            <td>
              <div class="row-actions">
                <button type="button" @click="toggleUser(user)">
                  {{ user.is_active ? t('admin.disable') : t('admin.enable') }}
                </button>
                <button type="button" class="danger" @click="removeUser(user)">
                  {{ t('admin.delete') }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">-</p>
    </section>

    <section class="users-panel">
      <div class="section-heading">
        <h2>{{ t('suggestions.title') }}</h2>
        <span>{{ suggestions.length }}</span>
      </div>

      <table v-if="suggestions.length">
        <thead>
          <tr>
            <th>{{ t('suggestions.subject') }}</th>
            <th>{{ t('suggestions.author') }}</th>
            <th>{{ t('suggestions.public') }}</th>
            <th>{{ t('suggestions.support') }}</th>
            <th>{{ t('suggestions.oppose') }}</th>
            <th>{{ t('suggestions.statusLabel') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="suggestion in suggestions" :key="suggestion.id">
            <td>
              <strong>{{ suggestion.title }}</strong>
              <p class="suggestion-body">{{ suggestion.body }}</p>
            </td>
            <td>{{ suggestion.author_email }}</td>
            <td>{{ suggestion.is_public ? t('admin.yes') : t('admin.no') }}</td>
            <td>{{ suggestion.support_count }}</td>
            <td>{{ suggestion.oppose_count }}</td>
            <td>
              <select :value="suggestion.status" @change="changeSuggestionStatus(suggestion, $event)">
                <option v-for="status in suggestionStatuses" :key="status" :value="status">
                  {{ t(`suggestions.status.${status}`) }}
                </option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">-</p>
    </section>
    </template>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  deleteAdminUser,
  getAdminStats,
  listAdminSuggestions,
  listAdminUsers,
  updateAdminSuggestionStatus,
  updateAdminUserStatus,
  type AdminSuggestion,
  type AdminStats,
  type AdminUser,
} from '@/api/admin'
import type { SuggestionStatus } from '@/api/suggestions'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'

const { t } = useI18n()
const users = ref<AdminUser[]>([])
const suggestions = ref<AdminSuggestion[]>([])
const stats = ref<AdminStats | null>(null)
const isInitialLoading = ref(true)
const errorMessage = ref('')
const suggestionStatuses: SuggestionStatus[] = ['new', 'reviewing', 'planned', 'completed', 'declined']

onMounted(refresh)

async function refresh() {
  errorMessage.value = ''
  try {
    const [nextUsers, nextStats, nextSuggestions] = await Promise.all([
      listAdminUsers(),
      getAdminStats(),
      listAdminSuggestions(),
    ])
    users.value = nextUsers
    stats.value = nextStats
    suggestions.value = nextSuggestions
  } catch {
    errorMessage.value = t('errors.forbidden')
  } finally {
    isInitialLoading.value = false
  }
}

async function toggleUser(user: AdminUser) {
  const updated = await updateAdminUserStatus(user.id, !user.is_active)
  users.value = users.value.map((item) => (item.id === updated.id ? updated : item))
}

async function removeUser(user: AdminUser) {
  if (!window.confirm(t('admin.deleteConfirm'))) return
  await deleteAdminUser(user.id)
  users.value = users.value.filter((item) => item.id !== user.id)
  if (stats.value) {
    stats.value.total_users = Math.max(0, stats.value.total_users - 1)
  }
}

async function changeSuggestionStatus(suggestion: AdminSuggestion, event: Event) {
  const status = (event.target as HTMLSelectElement).value as SuggestionStatus
  const updated = await updateAdminSuggestionStatus(suggestion.id, status)
  suggestions.value = suggestions.value.map((item) => (item.id === updated.id ? updated : item))
}

function formatDate(value: string): string {
  if (!value) return '-'
  return new Date(value).toLocaleDateString()
}
</script>

<style scoped>
.page-shell {
  width: min(100%, 1280px);
  margin: 0 auto;
  padding: 24px clamp(12px, 3vw, 36px);
}

.topbar,
.section-heading,
.row-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.admin-loading {
  min-height: 360px;
  margin-top: 16px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
}

.stats-grid article,
.users-panel {
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}

.stats-grid article {
  display: grid;
  gap: 8px;
}

.stats-grid strong {
  font-size: 1.8rem;
}

.users-panel {
  margin-top: 16px;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border-top: 1px solid #eef2f7;
  padding: 10px;
  text-align: left;
  white-space: nowrap;
}

button,
select {
  min-height: 44px;
  border: 1px solid #c9d1dc;
  border-radius: 6px;
  background: #fff;
  padding: 0 14px;
  font: inherit;
  cursor: pointer;
}

select {
  padding: 0 10px;
}

.danger {
  border-color: #f3b8b3;
  color: #b42318;
}

.status-pill {
  display: inline-block;
  border-radius: 999px;
  padding: 4px 10px;
}

.status-pill.active {
  background: #dcfce7;
  color: #166534;
}

.status-pill.disabled {
  background: #fee2e2;
  color: #991b1b;
}

.muted {
  color: #607086;
}

.suggestion-body {
  max-width: 360px;
  margin: 4px 0 0;
  overflow: hidden;
  color: #607086;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.error {
  color: #b42318;
}

@media (max-width: 760px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
