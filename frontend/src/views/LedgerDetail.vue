<template>
  <main class="page-shell" :class="{ recording: showWizard }">
    <WizardFlow
      v-if="ledger && showWizard"
      :ledger="ledger"
      @saved="handleTransactionSaved"
      @done="finishRecording"
      @update-ledger="updateLedgerSettings"
    />

    <template v-else>
      <header class="topbar">
        <div class="ledger-title-block">
          <div class="ledger-heading">
            <button
              type="button"
              class="back-button"
              :aria-label="t('common.back')"
              :title="t('common.back')"
              @click="router.push({ name: 'ledger-list' })"
            >
              <ChevronLeft :size="24" aria-hidden="true" />
            </button>
            <div>
              <h1>{{ ledger?.name || t('transaction.list') }}</h1>
              <p v-if="ledger">{{ ledger.default_currency_code }}</p>
            </div>
          </div>
          <div v-if="ledger" class="top-actions">
            <button
              class="icon-button record-button"
              type="button"
              :aria-label="t('transaction.new')"
              :title="t('transaction.new')"
              @click="showWizard = true"
            >
              <Plus :size="25" aria-hidden="true" />
            </button>
            <button
              class="icon-button"
              type="button"
              :aria-label="t('nav.settings')"
              :title="t('nav.settings')"
              @click="router.push({ name: 'ledger-settings', params: { id: ledger.id } })"
            >
              <SettingsIcon :size="22" aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      <section v-if="budget" class="budget-panel" :class="budgetWarningClass">
        <div>
          <strong>{{ t('budget.progress') }}</strong>
          <p>{{ formatAmount(budget.progress.monthly_spent, ledger?.default_currency_code || '') }} / {{ formatAmount(budget.progress.monthly_total, ledger?.default_currency_code || '') }}</p>
        </div>
        <div class="progress-track">
          <span :style="{ width: `${progressWidth}%` }" />
        </div>
        <p v-if="budget.progress.warning === 'soft'">{{ t('budget.warning80') }}</p>
        <p v-else-if="budget.progress.warning === 'over'">{{ t('budget.warning100') }}</p>
      </section>

      <section class="list-panel">
        <div class="section-heading">
          <h2>{{ t('transaction.list') }} · {{ currentMonthLabel }}</h2>
          <span>{{ transactionList.total }}</span>
        </div>

        <div v-if="Object.keys(transactionList.page_total_amounts).length" class="page-totals">
          <strong>{{ t('transaction.monthTotal') }}</strong>
          <span v-for="(amount, currency) in transactionList.page_total_amounts" :key="currency">
            {{ formatAmount(amount, currency) }}
          </span>
        </div>

        <ul v-if="transactionList.items.length" class="transaction-list">
          <li v-for="transaction in transactionList.items" :key="transaction.id">
            <strong>{{ formatAmount(transaction.amount, transaction.currency_code) }}</strong>
            <span class="transaction-name">{{ transactionLabel(transaction) }}</span>
            <span class="transaction-date">{{ transaction.transaction_date }}</span>
            <span v-if="ledger?.necessity_step_mode !== 'disabled'" class="transaction-necessity">
              {{ necessityLabel(transaction.necessity) }}
            </span>
            <span v-if="transaction.note" class="transaction-note">{{ transaction.note }}</span>
          </li>
        </ul>
        <p v-else class="muted">{{ t('transaction.noTransactions') }}</p>

        <div class="month-nav">
          <button type="button" @click="changeMonth(-1)">
            <ChevronLeft :size="18" aria-hidden="true" />
            <span>{{ previousMonthLabel }}</span>
          </button>
          <button type="button" @click="changeMonth(1)">
            <span>{{ nextMonthLabel }}</span>
            <ChevronRight :size="18" aria-hidden="true" />
          </button>
        </div>
      </section>
    </template>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft, ChevronRight, Plus, Settings as SettingsIcon } from '@lucide/vue'

import { getBudget, type Budget } from '@/api/budget'
import type { Ledger } from '@/api/ledgers'
import { listTransactions, type Transaction, type TransactionListResponse } from '@/api/transactions'
import WizardFlow from '@/components/WizardFlow.vue'
import { translateLabel } from '@/i18n/labels'
import { useLedgerStore } from '@/stores/ledgers'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const ledgerStore = useLedgerStore()
const ledgerId = computed(() => String(route.params.id))
const ledger = computed(() => ledgerStore.activeLedger)
const showWizard = ref(false)
const selectedMonth = ref(startOfMonth(new Date()))
const pageSize = 1000
const budget = ref<Budget | null>(null)
const transactionList = ref<TransactionListResponse>({
  items: [],
  page: 1,
  page_size: pageSize,
  total: 0,
  page_total_amounts: {},
})

const currentMonthLabel = computed(() => formatMonthHeading(selectedMonth.value))
const previousMonthLabel = computed(() => formatMonthButton(addMonths(selectedMonth.value, -1)))
const nextMonthLabel = computed(() => formatMonthButton(addMonths(selectedMonth.value, 1)))
const monthRange = computed(() => {
  const start = startOfMonth(selectedMonth.value)
  const end = new Date(start.getFullYear(), start.getMonth() + 1, 0)
  return {
    startDate: formatDate(start),
    endDate: formatDate(end),
  }
})
const progressWidth = computed(() => {
  if (!budget.value) return 0
  return Math.min(100, Math.round(budget.value.progress.percentage * 100))
})
const budgetWarningClass = computed(() => ({
  soft: budget.value?.progress.warning === 'soft',
  over: budget.value?.progress.warning === 'over',
}))

onMounted(async () => {
  await ledgerStore.fetchLedger(ledgerId.value)
  await Promise.all([loadTransactions(), loadBudget()])
})

async function loadTransactions() {
  transactionList.value = await listTransactions(
    ledgerId.value,
    1,
    pageSize,
    monthRange.value.startDate,
    monthRange.value.endDate,
  )
}

async function loadBudget() {
  if (!ledger.value?.budget_enabled) {
    budget.value = null
    return
  }
  budget.value = await getBudget(ledgerId.value)
}

async function changeMonth(delta: number) {
  selectedMonth.value = addMonths(selectedMonth.value, delta)
  await loadTransactions()
}

async function handleTransactionSaved() {
  await Promise.all([loadTransactions(), loadBudget()])
}

function finishRecording() {
  showWizard.value = false
}

async function updateLedgerSettings(payload: Partial<Ledger>) {
  await ledgerStore.saveLedger(ledgerId.value, {
    subject_step_mode: payload.subject_step_mode,
    necessity_step_mode: payload.necessity_step_mode,
  })
}

function formatAmount(amount: number, currencyCode: string): string {
  return `${amount.toLocaleString()} ${currencyCode}`
}

function transactionLabel(transaction: Transaction): string {
  const item = transaction.items[0]
  return translateLabel(item?.item_name || item?.category_name_snapshot, t)
}

function necessityLabel(value: string): string {
  return value === 'non-essential' ? t('transaction.nonEssential') : t('transaction.essential')
}

function startOfMonth(value: Date): Date {
  return new Date(value.getFullYear(), value.getMonth(), 1)
}

function addMonths(value: Date, delta: number): Date {
  return new Date(value.getFullYear(), value.getMonth() + delta, 1)
}

function formatDate(value: Date): string {
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${value.getFullYear()}-${month}-${day}`
}

function formatMonthHeading(value: Date): string {
  return `${value.getFullYear()}年${value.getMonth() + 1}月`
}

function formatMonthButton(value: Date): string {
  return `${value.getMonth() + 1}月`
}
</script>

<style scoped>
.page-shell {
  max-width: 920px;
  margin: 0 auto;
  padding: 24px;
}

.page-shell.recording {
  max-width: 560px;
  min-height: 100dvh;
  padding: 0 16px;
}

.topbar,
.top-actions,
.section-heading,
.page-totals,
.month-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

h1,
h2,
p {
  margin-top: 0;
}

.topbar {
  margin-bottom: 20px;
}

.ledger-title-block {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  width: 100%;
}

.ledger-heading {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 10px;
}

.ledger-title-block h1 {
  margin-bottom: 4px;
}

.ledger-title-block p {
  margin-bottom: 0;
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

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.primary-button {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
  font-weight: 700;
}

.top-actions {
  gap: 18px;
}

.icon-button {
  display: inline-grid;
  width: 48px;
  min-width: 48px;
  height: 48px;
  min-height: 48px;
  place-items: center;
  border-radius: 50%;
  padding: 0;
  font-size: 1.45rem;
  font-weight: 800;
  line-height: 1;
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

.record-button {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.budget-panel,
.list-panel {
  margin-top: 16px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}

.budget-panel.soft {
  border-color: #f59e0b;
}

.budget-panel.over {
  border-color: #dc2626;
}

.progress-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;
}

.progress-track span {
  display: block;
  height: 100%;
  background: #2563eb;
}

.soft .progress-track span {
  background: #f59e0b;
}

.over .progress-track span {
  background: #dc2626;
}

.transaction-list {
  display: grid;
  gap: 0;
  padding: 0;
  list-style: none;
}

.transaction-list li {
  display: grid;
  grid-template-columns: minmax(88px, auto) minmax(0, 1fr) auto auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  min-height: 40px;
  border-top: 1px solid #eef2f7;
  padding: 6px 0;
}

.transaction-list strong,
.transaction-name,
.transaction-date,
.transaction-necessity,
.transaction-note {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.transaction-name {
  font-weight: 700;
}

.transaction-date,
.transaction-necessity,
.transaction-note,
.muted {
  color: #607086;
}

.transaction-date,
.transaction-necessity {
  font-size: 0.9rem;
}

.transaction-note {
  font-size: 0.9rem;
}

.month-nav {
  margin-top: 16px;
}

.month-nav button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 112px;
}

@media (max-width: 640px) {
  .topbar,
  .top-actions,
  .page-totals,
  .month-nav {
    align-items: center;
  }

  .ledger-title-block {
    gap: 16px;
  }

  .transaction-list li {
    grid-template-columns: minmax(76px, auto) minmax(0, 1fr) auto;
  }

  .transaction-necessity,
  .transaction-note {
    display: none;
  }
}

@media (max-width: 420px) {
  .transaction-date {
    max-width: 5.5em;
  }
}
</style>
