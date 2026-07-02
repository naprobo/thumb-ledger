<template>
  <main class="page-shell">
    <header class="topbar">
      <div>
        <h1>{{ t('nav.ledgers') }}</h1>
        <p>{{ ledgerStore.ledgers.length }}/10</p>
      </div>
      <button
        class="create-icon-button"
        type="button"
        :disabled="!ledgerStore.canCreateLedger"
        :aria-label="t('ledger.create')"
        :title="t('ledger.create')"
        @click="openWizard"
      >
        <Plus :size="24" aria-hidden="true" />
      </button>
    </header>

    <section v-if="showWizard" class="tool-panel" aria-live="polite">
      <div class="wizard-header">
        <strong>{{ t('ledger.create') }}</strong>
        <span>{{ wizardStep + 1 }}/{{ wizardSteps.length }}</span>
      </div>

      <form class="wizard-form" @submit.prevent="submitLedger">
        <fieldset v-if="currentWizardStep === 'name'">
          <legend>{{ t('ledger.name') }}</legend>
          <input v-model.trim="draft.name" maxlength="50" required :placeholder="t('ledger.namePlaceholder')" />
        </fieldset>

        <fieldset v-else-if="currentWizardStep === 'entryMode'">
          <legend>{{ t('ledger.entryMode') }}</legend>
          <div class="choice-tags two-options">
            <button type="button" :class="{ selected: draft.entry_mode === 'receipt' }" :aria-pressed="draft.entry_mode === 'receipt'" @click="draft.entry_mode = 'receipt'">
              {{ t('ledger.entryModeReceipt') }}
            </button>
            <button type="button" :class="{ selected: draft.entry_mode === 'item' }" :aria-pressed="draft.entry_mode === 'item'" @click="draft.entry_mode = 'item'">
              {{ t('ledger.entryModeItem') }}
            </button>
          </div>
        </fieldset>

        <fieldset v-else-if="currentWizardStep === 'receiptDetails'">
          <legend>{{ t('ledger.receiptItemTracking') }}</legend>
          <div class="choice-tags two-options">
            <button type="button" :class="{ selected: draft.receipt_item_enabled }" :aria-pressed="draft.receipt_item_enabled" @click="draft.receipt_item_enabled = true">
              {{ t('ledger.receiptItemSometimes') }}
            </button>
            <button type="button" :class="{ selected: !draft.receipt_item_enabled }" :aria-pressed="!draft.receipt_item_enabled" @click="draft.receipt_item_enabled = false">
              {{ t('ledger.receiptItemNever') }}
            </button>
          </div>
        </fieldset>

        <fieldset v-else-if="currentWizardStep === 'subject'">
          <legend>{{ t('ledger.subjectTracking') }}</legend>
          <div class="choice-tags">
            <button type="button" :class="{ selected: draft.subject_enabled && draft.subject_step_mode === 'required' }" @click="setSubjectMode('required')">
              {{ t('ledger.trackingRequired') }}
            </button>
            <button type="button" :class="{ selected: draft.subject_enabled && draft.subject_step_mode === 'optional' }" @click="setSubjectMode('optional')">
              {{ t('ledger.trackingOptional') }}
            </button>
            <button type="button" :class="{ selected: !draft.subject_enabled }" @click="setSubjectMode('disabled')">
              {{ t('ledger.trackingDisabled') }}
            </button>
          </div>
        </fieldset>

        <fieldset v-else-if="currentWizardStep === 'necessity'">
          <legend>{{ t('ledger.necessityTracking') }}</legend>
          <div class="choice-tags">
            <button type="button" :class="{ selected: draft.necessity_step_mode === 'required' }" @click="draft.necessity_step_mode = 'required'">
              {{ t('ledger.trackingRequired') }}
            </button>
            <button type="button" :class="{ selected: draft.necessity_step_mode === 'optional' }" @click="draft.necessity_step_mode = 'optional'">
              {{ t('ledger.trackingOptional') }}
            </button>
            <button type="button" :class="{ selected: draft.necessity_step_mode === 'disabled' }" @click="draft.necessity_step_mode = 'disabled'">
              {{ t('ledger.trackingDisabled') }}
            </button>
          </div>
        </fieldset>

        <fieldset v-else-if="currentWizardStep === 'location'">
          <legend>{{ t('ledger.locationTracking') }}</legend>
          <div class="choice-tags">
            <button type="button" :class="{ selected: draft.location_step_mode === 'required' }" @click="draft.location_step_mode = 'required'">
              {{ t('ledger.trackingRequired') }}
            </button>
            <button type="button" :class="{ selected: draft.location_step_mode === 'optional' }" @click="draft.location_step_mode = 'optional'">
              {{ t('ledger.trackingOptional') }}
            </button>
            <button type="button" :class="{ selected: draft.location_step_mode === 'disabled' }" @click="draft.location_step_mode = 'disabled'">
              {{ t('ledger.trackingDisabled') }}
            </button>
          </div>
        </fieldset>

        <fieldset v-else-if="currentWizardStep === 'currency'">
          <legend>{{ t('ledger.defaultCurrency') }}</legend>
          <label>
            <span>{{ t('ledger.defaultCurrency') }}</span>
            <select v-model="draft.default_currency_code" required>
              <option v-for="currency in CURRENCY_OPTIONS" :key="currency.code" :value="currency.code">
                {{ currencyOptionLabel(currency) }}
              </option>
            </select>
          </label>
          <label class="switch-row">
            <input v-model="draft.budget_enabled" type="checkbox" />
            <span>{{ t('ledger.budgetEnabled') }}</span>
          </label>
        </fieldset>

        <div class="actions">
          <button type="button" @click="closeWizard">{{ t('common.cancel') }}</button>
          <button type="button" :disabled="wizardStep === 0" @click="wizardStep--">{{ t('common.back') }}</button>
          <button v-if="wizardStep < wizardSteps.length - 1" type="button" :disabled="!canAdvance" @click="wizardStep++">
            {{ t('common.next') }}
          </button>
          <button v-else class="primary-button" type="submit" :disabled="isSubmitting || !canAdvance">
            {{ t('common.save') }}
          </button>
        </div>
      </form>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </section>

    <AppLoadingPanel v-if="isInitialLoading" class="ledger-loading" />

    <section v-else class="ledger-grid">
      <article
        v-for="ledger in ledgerStore.ledgers"
        :key="ledger.id"
        class="ledger-card"
        role="button"
        tabindex="0"
        @click="openLedger(ledger.id)"
        @keydown.enter.prevent="openLedger(ledger.id)"
        @keydown.space.prevent="openLedger(ledger.id)"
      >
        <div class="ledger-main">
          <strong>{{ ledger.name }}</strong>
          <span>{{ modeLabel(ledger.entry_mode) }}</span>
        </div>
        <div class="ledger-amounts">
          <span class="ledger-total">{{ ledgerTotalLabel(ledger) }}</span>
          <small>{{ ledgerCurrentMonthLabel(ledger) }}</small>
        </div>
        <button
          v-if="canManageLedger(ledger)"
          type="button"
          class="settings-icon-button"
          :aria-label="t('nav.settings')"
          :title="t('nav.settings')"
          @click.stop="router.push({ name: 'ledger-settings', params: { id: ledger.id } })"
        >
          <SettingsIcon :size="20" aria-hidden="true" />
        </button>
      </article>
    </section>

    <p v-if="!ledgerStore.isLoading && ledgerStore.ledgers.length === 0" class="empty-state">
      {{ t('ledger.noLedgers') }}
    </p>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Plus, Settings as SettingsIcon } from '@lucide/vue'

import { useLedgerStore } from '@/stores/ledgers'
import type { EntryMode, Ledger, LedgerCreatePayload } from '@/api/ledgers'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'
import { CURRENCY_OPTIONS, currencyOptionLabel } from '@/constants/currencies'
import { useAuthStore } from '@/stores/auth'
import { formatMoneyWithTrailingSymbol } from '@/utils/money'

type LedgerWizardStep = 'name' | 'entryMode' | 'receiptDetails' | 'subject' | 'necessity' | 'location' | 'currency'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const ledgerStore = useLedgerStore()

const showWizard = ref(false)
const wizardStep = ref(0)
const isInitialLoading = ref(true)
const isSubmitting = ref(false)
const errorMessage = ref('')
const draft = reactive<LedgerCreatePayload>({
  name: '',
  entry_mode: 'receipt',
  receipt_item_enabled: false,
  location_step_mode: 'optional',
  subject_enabled: false,
  subject_step_mode: 'required',
  necessity_step_mode: 'disabled',
  default_currency_code: 'JPY',
  timezone: 'Asia/Tokyo',
  budget_enabled: false,
})

const wizardSteps = computed<LedgerWizardStep[]>(() => {
  const steps: LedgerWizardStep[] = ['name', 'entryMode']
  if (draft.entry_mode === 'receipt') steps.push('receiptDetails')
  steps.push('subject', 'necessity', 'location', 'currency')
  return steps
})
const currentWizardStep = computed(() => wizardSteps.value[wizardStep.value])
const canAdvance = computed(() => {
  if (currentWizardStep.value === 'name') return draft.name.length >= 1 && draft.name.length <= 50
  if (currentWizardStep.value === 'currency') return CURRENCY_OPTIONS.some((currency) => currency.code === draft.default_currency_code)
  return true
})

onMounted(async () => {
  try {
    await ledgerStore.fetchLedgers()
  } finally {
    isInitialLoading.value = false
  }
})

function openWizard() {
  showWizard.value = true
  wizardStep.value = 0
  errorMessage.value = ''
}

function closeWizard() {
  showWizard.value = false
}

function modeLabel(mode: EntryMode): string {
  return mode === 'receipt' ? t('ledger.entryModeReceipt') : t('ledger.entryModeItem')
}

function setSubjectMode(mode: 'required' | 'optional' | 'disabled') {
  draft.subject_enabled = mode !== 'disabled'
  draft.subject_step_mode = mode
}

function ledgerTotalLabel(ledger: Ledger): string {
  const totals = Object.entries(ledger.total_amounts || {})
  if (!totals.length) return `${t('summary.total')} ${formatMoneyWithTrailingSymbol(0, ledger.default_currency_code)}`
  return `${t('summary.total')} ${totals.map(([currency, amount]) => formatMoneyWithTrailingSymbol(amount, currency)).join(' / ')}`
}

function ledgerCurrentMonthLabel(ledger: Ledger): string {
  const totals = Object.entries(ledger.current_month_amounts || {})
  if (!totals.length) return `${t('transaction.monthTotal')} ${formatMoneyWithTrailingSymbol(0, ledger.default_currency_code)}`
  return `${t('transaction.monthTotal')} ${totals.map(([currency, amount]) => formatMoneyWithTrailingSymbol(amount, currency)).join(' / ')}`
}

function canManageLedger(ledger: Ledger): boolean {
  return !authStore.user || ledger.owner_id === authStore.user.id
}

function openLedger(id: string) {
  router.push({ name: 'ledger-detail', params: { id } })
}

async function submitLedger() {
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    if (!draft.subject_enabled) draft.subject_step_mode = 'disabled'
    if (draft.entry_mode === 'item') draft.receipt_item_enabled = false
    const ledger = await ledgerStore.addLedger({ ...draft })
    showWizard.value = false
    if (ledger.budget_enabled) {
      await router.push({ name: 'budget-wizard', params: { id: ledger.id } })
    } else {
      await router.push({ name: 'ledger-detail', params: { id: ledger.id } })
    }
  } catch {
    errorMessage.value = t('errors.validationError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.page-shell {
  width: min(100%, 1280px);
  margin: 0 auto;
  padding: 24px clamp(12px, 3vw, 36px);
}

.topbar,
.wizard-header,
.actions,
.ledger-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

h1 {
  margin: 0;
  font-size: 1.7rem;
}

.topbar p {
  margin: 4px 0 0;
  color: #607086;
}

.create-icon-button {
  display: inline-grid;
  width: 48px;
  min-width: 48px;
  height: 48px;
  min-height: 48px;
  place-items: center;
  border-radius: 50%;
  padding: 0;
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.tool-panel {
  margin: 20px 0;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 18px;
  background: #fff;
}

.wizard-form {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

fieldset {
  display: grid;
  gap: 14px;
  min-height: 138px;
  margin: 0;
  padding: 0;
  border: 0;
}

legend {
  margin-bottom: 10px;
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

.choice-tags {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.choice-tags.two-options {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.choice-tags button {
  min-height: 72px;
  border: 2px solid #c9d1dc;
  padding: 12px;
  background: #fff;
  font-weight: 700;
}

.choice-tags button.selected {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
  box-shadow: inset 0 0 0 1px #2563eb;
}

.choice-tags button:focus-visible {
  outline: 3px solid #93c5fd;
  outline-offset: 2px;
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
}

.ledger-grid {
  display: grid;
  gap: 10px;
}

.ledger-loading {
  min-height: 320px;
  margin-top: 16px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
}

.ledger-card {
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
  cursor: pointer;
}

.ledger-card:focus-visible {
  outline: 3px solid #93c5fd;
  outline-offset: 2px;
}

.ledger-card:hover {
  background: #f8fafc;
}

.ledger-main {
  display: grid;
  justify-items: start;
  gap: 4px;
  flex: 1;
  min-width: 0;
  border: 0;
  padding: 0;
  background: transparent;
}

.ledger-main span {
  color: #607086;
}

.ledger-total {
  min-width: max-content;
  color: #0f172a;
  font-size: 1.05rem;
  font-weight: 800;
}

.ledger-amounts {
  display: grid;
  min-width: max-content;
  gap: 3px;
  justify-items: end;
}

.ledger-amounts small {
  color: #607086;
  font-size: 0.78rem;
  font-weight: 700;
}

.settings-icon-button {
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

.empty-state,
.error {
  color: #b42318;
}

@media (max-width: 640px) {
  .topbar,
  .actions {
    align-items: center;
  }

  .choice-tags,
  .choice-tags.two-options {
    grid-template-columns: 1fr;
  }

  .ledger-card {
    align-items: center;
  }

  .ledger-total {
    font-size: 0.95rem;
  }
}
</style>
