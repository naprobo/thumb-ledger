<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="title-row">
        <button
          type="button"
          class="back-button"
          :aria-label="t('common.back')"
          :title="t('common.back')"
          @click="router.push({ name: 'ledger-settings', params: { id: ledgerId } })"
        >
          <ChevronLeft :size="24" aria-hidden="true" />
        </button>
        <div>
          <h1>{{ t('recurring.title') }}</h1>
          <p v-if="ledger">{{ ledger.name }}</p>
        </div>
      </div>
      <button type="button" @click="loadRecurring">{{ t('common.refresh') }}</button>
    </header>

    <div v-if="toastMessage" :class="['toast', toastKind]" role="status">
      {{ toastMessage }}
    </div>

    <section class="section-block">
      <div class="section-heading">
        <h2>{{ draft.editing_id ? t('recurring.edit') : t('recurring.create') }}</h2>
        <button type="button" @click="isFormOpen = !isFormOpen">
          <Plus v-if="!isFormOpen" :size="18" aria-hidden="true" />
          <X v-else :size="18" aria-hidden="true" />
          <span>{{ isFormOpen ? t('common.cancel') : t('recurring.create') }}</span>
        </button>
      </div>

      <form v-if="isFormOpen" class="recurring-form" @submit.prevent="submitRecurring">
        <div class="grid-two">
          <label>
            <span>{{ t('transaction.amount') }} ({{ ledger?.default_currency_code || 'JPY' }})</span>
            <input v-model.number="draft.amount" inputmode="numeric" min="1" type="number" required />
          </label>
          <label>
            <span>{{ t('recurring.interval') }}</span>
            <select v-model="draft.interval">
              <option value="daily">{{ t('recurring.daily') }}</option>
              <option value="weekly">{{ t('recurring.weekly') }}</option>
              <option value="monthly">{{ t('recurring.monthly') }}</option>
              <option value="yearly">{{ t('recurring.yearly') }}</option>
            </select>
          </label>
        </div>

        <div class="grid-two">
          <label>
            <span>{{ t('recurring.nextRunDate') }}</span>
            <input v-model="draft.next_run_date" type="date" required />
          </label>
          <label>
            <span>{{ t('transaction.category') }}</span>
            <select v-model="draft.category_name">
              <option v-for="category in categories" :key="category.id" :value="category.name">
                {{ translateLabel(category.name, t) }}
              </option>
            </select>
          </label>
        </div>

        <label>
          <span>{{ t('transaction.itemName') }}</span>
          <input v-model.trim="draft.item_name" maxlength="100" :placeholder="t('transaction.customItemPlaceholder')" />
        </label>

        <label>
          <span>{{ t('transaction.necessity') }}</span>
          <select v-model="draft.necessity">
            <option value="essential">{{ t('transaction.essential') }}</option>
            <option value="non-essential">{{ t('transaction.nonEssential') }}</option>
          </select>
        </label>

        <button class="primary-button" type="submit" :disabled="isSaving || !canSubmit">
          {{ t('common.save') }}
        </button>
      </form>
    </section>

    <section class="section-block">
      <div class="section-heading">
        <h2>{{ t('recurring.templates') }}</h2>
        <span>{{ templates.length }}</span>
      </div>

      <ul v-if="templates.length" class="template-list">
        <li v-for="template in templates" :key="template.id">
          <div>
            <strong>
              {{ recurringLabel(template) }}
              <span :class="['status-pill', template.is_active ? 'active' : 'inactive']">
                {{ template.is_active ? t('recurring.active') : t('recurring.inactive') }}
              </span>
            </strong>
            <p>
              {{ formatAmount(template.template_data.amount, template.template_data.currency_code || ledger?.default_currency_code || '') }}
              · {{ intervalLabel(template.interval) }}
              · {{ t('recurring.nextRunDate') }} {{ template.next_run_date }}
            </p>
          </div>
          <button type="button" @click="toggleRecurring(template)">
            {{ template.is_active ? t('recurring.disable') : t('recurring.enable') }}
          </button>
          <button type="button" @click="startEdit(template)">
            {{ t('recurring.edit') }}
          </button>
          <button type="button" class="danger-button" @click="deleteRecurring(template.id)">
            {{ t('admin.delete') }}
          </button>
        </li>
      </ul>
      <p v-else class="muted">{{ t('recurring.empty') }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft, Plus, X } from '@lucide/vue'

import { listCategories, type Category } from '@/api/ledgers'
import {
  createRecurringTemplate,
  deleteRecurringTemplate,
  listRecurringTemplates,
  updateRecurringTemplate,
  type RecurringInterval,
  type RecurringTemplate,
} from '@/api/recurring'
import type { Necessity } from '@/api/transactions'
import { translateLabel } from '@/i18n/labels'
import { useLedgerStore } from '@/stores/ledgers'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const ledgerStore = useLedgerStore()
const ledgerId = computed(() => String(route.params.id))
const ledger = computed(() => ledgerStore.activeLedger)
const categories = ref<Category[]>([])
const templates = ref<RecurringTemplate[]>([])
const isFormOpen = ref(false)
const isSaving = ref(false)
const toastMessage = ref('')
const toastKind = ref<'success' | 'error'>('success')
let toastTimer: number | undefined

const draft = reactive({
  editing_id: '',
  amount: 0,
  interval: 'monthly' as RecurringInterval,
  next_run_date: formatDate(new Date()),
  category_name: 'category.other',
  item_name: '',
  necessity: 'essential' as Necessity,
})

const canSubmit = computed(() => draft.amount > 0 && !!draft.next_run_date && !!draft.category_name)

onMounted(async () => {
  await ledgerStore.fetchLedger(ledgerId.value)
  await Promise.all([loadCategories(), loadRecurring()])
})

watch(categories, (rows) => {
  if (!rows.length) return
  if (!rows.some((category) => category.name === draft.category_name)) {
    draft.category_name = rows[0].name
  }
})

async function loadCategories() {
  categories.value = await listCategories(ledgerId.value)
}

async function loadRecurring() {
  templates.value = await listRecurringTemplates(ledgerId.value)
}

async function submitRecurring() {
  if (!canSubmit.value || !ledger.value) return
  isSaving.value = true
  try {
    const payload = {
      interval: draft.interval,
      next_run_date: draft.next_run_date,
      template_data: {
        amount: draft.amount,
        currency_code: ledger.value.default_currency_code,
        necessity: draft.necessity,
        items: [
          {
            category_name: draft.category_name,
            item_name: draft.item_name || undefined,
            amount: draft.amount,
            currency_code: ledger.value.default_currency_code,
          },
        ],
        subject_ids: [],
      },
    }
    if (draft.editing_id) {
      await updateRecurringTemplate(ledgerId.value, draft.editing_id, payload)
    } else {
      await createRecurringTemplate(ledgerId.value, payload)
    }
    resetDraft()
    isFormOpen.value = false
    showToast(t('common.saved'), 'success')
    await loadRecurring()
  } catch {
    showToast(t('errors.validationError'), 'error')
  } finally {
    isSaving.value = false
  }
}

async function toggleRecurring(template: RecurringTemplate) {
  try {
    const updated = await updateRecurringTemplate(ledgerId.value, template.id, { is_active: !template.is_active })
    templates.value = templates.value.map((item) => (item.id === updated.id ? updated : item))
    showToast(t('common.saved'), 'success')
  } catch {
    showToast(t('errors.validationError'), 'error')
  }
}

async function deleteRecurring(recurringId: string) {
  try {
    await deleteRecurringTemplate(ledgerId.value, recurringId)
    templates.value = templates.value.filter((template) => template.id !== recurringId)
    showToast(t('common.saved'), 'success')
  } catch {
    showToast(t('errors.validationError'), 'error')
  }
}

function resetDraft() {
  draft.editing_id = ''
  draft.amount = 0
  draft.interval = 'monthly'
  draft.next_run_date = formatDate(new Date())
  draft.category_name = categories.value[0]?.name || 'category.other'
  draft.item_name = ''
  draft.necessity = 'essential'
}

function startEdit(template: RecurringTemplate) {
  const item = template.template_data.items?.[0]
  draft.editing_id = template.id
  draft.amount = template.template_data.amount
  draft.interval = template.interval
  draft.next_run_date = template.next_run_date
  draft.category_name = item?.category_name || categories.value[0]?.name || 'category.other'
  draft.item_name = item?.item_name || ''
  draft.necessity = template.template_data.necessity || 'essential'
  isFormOpen.value = true
}

function recurringLabel(template: RecurringTemplate): string {
  const item = template.template_data.items?.[0]
  return translateLabel(item?.item_name || item?.category_name, t)
}

function intervalLabel(interval: RecurringInterval): string {
  return t(`recurring.${interval}`)
}

function formatAmount(amount: number, currencyCode: string): string {
  return `${amount.toLocaleString()} ${currencyCode}`
}

function formatDate(value: Date): string {
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${value.getFullYear()}-${month}-${day}`
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
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.topbar,
.title-row,
.section-heading {
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
  border-radius: 50%;
  padding: 0;
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

.section-block {
  display: grid;
  gap: 12px;
  margin-top: 16px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}

.recurring-form {
  display: grid;
  gap: 12px;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
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

.danger-button {
  border-color: #dc2626;
  color: #b42318;
  font-weight: 700;
}

.template-list {
  display: grid;
  gap: 8px;
  padding: 0;
  list-style: none;
}

.template-list li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 12px;
  border-top: 1px solid #eef2f7;
  padding: 12px 0;
}

.template-list p {
  margin-bottom: 0;
  color: #607086;
}

.status-pill {
  display: inline-block;
  margin-left: 8px;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 0.78rem;
  font-weight: 800;
}

.status-pill.active {
  background: #dcfce7;
  color: #166534;
}

.status-pill.inactive {
  background: #eef2f7;
  color: #607086;
}

.muted {
  color: #607086;
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

@media (max-width: 640px) {
  .topbar,
  .section-heading,
  .template-list li {
    align-items: stretch;
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .title-row {
    align-items: center;
    flex-direction: row;
  }

  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>
