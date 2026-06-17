<template>
  <main class="page-shell">
    <header class="topbar">
      <div>
        <h1>{{ t('nav.ledgers') }}</h1>
        <p>{{ ledgerStore.ledgers.length }}/10</p>
      </div>
    </header>

    <section v-if="showWizard" class="tool-panel" aria-live="polite">
      <div class="wizard-header">
        <strong>{{ t('ledger.create') }}</strong>
        <span>{{ wizardStep + 1 }}/5</span>
      </div>

      <form class="wizard-form" @submit.prevent="submitLedger">
        <fieldset v-if="wizardStep === 0">
          <legend>{{ t('ledger.name') }}</legend>
          <input v-model.trim="draft.name" maxlength="50" required :placeholder="t('ledger.namePlaceholder')" />
        </fieldset>

        <fieldset v-else-if="wizardStep === 1">
          <legend>{{ t('ledger.entryMode') }}</legend>
          <div class="segmented">
            <label>
              <input v-model="draft.entry_mode" type="radio" value="receipt" />
              <span>{{ t('ledger.entryModeReceipt') }}</span>
            </label>
            <label>
              <input v-model="draft.entry_mode" type="radio" value="item" />
              <span>{{ t('ledger.entryModeItem') }}</span>
            </label>
          </div>
        </fieldset>

        <fieldset v-else-if="wizardStep === 2">
          <legend>{{ t('ledger.subjectTracking') }}</legend>
          <label class="switch-row">
            <input v-model="draft.subject_enabled" type="checkbox" />
            <span>{{ t('ledger.subjectTracking') }}</span>
          </label>
          <select v-model="draft.subject_step_mode" :disabled="!draft.subject_enabled">
            <option value="required">{{ t('ledger.subjectRequired') }}</option>
            <option value="optional">{{ t('ledger.subjectOptional') }}</option>
            <option value="disabled">{{ t('common.disabled') }}</option>
          </select>
        </fieldset>

        <fieldset v-else-if="wizardStep === 3">
          <legend>{{ t('ledger.necessityTracking') }}</legend>
          <label>
            <span>{{ t('ledger.necessityTracking') }}</span>
            <select v-model="draft.necessity_step_mode">
              <option value="required">{{ t('ledger.subjectRequired') }}</option>
              <option value="optional">{{ t('ledger.subjectOptional') }}</option>
              <option value="disabled">{{ t('common.disabled') }}</option>
            </select>
          </label>
          <label class="switch-row">
            <input v-model="draft.budget_enabled" type="checkbox" />
            <span>{{ t('ledger.budgetEnabled') }}</span>
          </label>
        </fieldset>

        <fieldset v-else>
          <legend>{{ t('ledger.defaultCurrency') }}</legend>
          <div class="grid-two">
            <label>
              <span>{{ t('ledger.defaultCurrency') }}</span>
              <select v-model="draft.default_currency_code" required>
                <option v-for="currency in CURRENCY_OPTIONS" :key="currency.code" :value="currency.code">
                  {{ currencyOptionLabel(currency) }}
                </option>
              </select>
            </label>
            <label>
              <span>{{ t('ledger.timezone') }}</span>
              <input v-model.trim="draft.timezone" maxlength="50" required />
            </label>
          </div>
        </fieldset>

        <div class="actions">
          <button type="button" @click="closeWizard">{{ t('common.cancel') }}</button>
          <button type="button" :disabled="wizardStep === 0" @click="wizardStep--">{{ t('common.back') }}</button>
          <button v-if="wizardStep < 4" type="button" :disabled="!canAdvance" @click="wizardStep++">
            {{ t('common.next') }}
          </button>
          <button v-else class="primary-button" type="submit" :disabled="isSubmitting || !canAdvance">
            {{ t('common.save') }}
          </button>
        </div>
      </form>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </section>

    <section class="ledger-grid">
      <article v-for="ledger in ledgerStore.ledgers" :key="ledger.id" class="ledger-card">
        <button class="ledger-main" type="button" @click="router.push({ name: 'ledger-detail', params: { id: ledger.id } })">
          <strong>{{ ledger.name }}</strong>
          <span>{{ modeLabel(ledger.entry_mode) }} · {{ ledger.default_currency_code }}</span>
        </button>
        <button
          type="button"
          class="settings-icon-button"
          :aria-label="t('nav.settings')"
          :title="t('nav.settings')"
          @click="router.push({ name: 'ledger-settings', params: { id: ledger.id } })"
        >
          <SettingsIcon :size="20" aria-hidden="true" />
        </button>
      </article>
    </section>

    <p v-if="!ledgerStore.isLoading && ledgerStore.ledgers.length === 0" class="empty-state">
      {{ t('ledger.noLedgers') }}
    </p>

    <div class="bottom-actions">
      <button class="primary-button" type="button" :disabled="!ledgerStore.canCreateLedger" @click="openWizard">
        {{ t('ledger.create') }}
      </button>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Settings as SettingsIcon } from '@lucide/vue'

import { useLedgerStore } from '@/stores/ledgers'
import type { EntryMode, LedgerCreatePayload } from '@/api/ledgers'
import { CURRENCY_OPTIONS, currencyOptionLabel } from '@/constants/currencies'

const { t } = useI18n()
const router = useRouter()
const ledgerStore = useLedgerStore()

const showWizard = ref(false)
const wizardStep = ref(0)
const isSubmitting = ref(false)
const errorMessage = ref('')
const draft = reactive<LedgerCreatePayload>({
  name: '',
  entry_mode: 'receipt',
  subject_enabled: false,
  subject_step_mode: 'required',
  necessity_step_mode: 'disabled',
  default_currency_code: 'JPY',
  timezone: 'Asia/Tokyo',
  budget_enabled: false,
})

const canAdvance = computed(() => {
  if (wizardStep.value === 0) return draft.name.length >= 1 && draft.name.length <= 50
  if (wizardStep.value === 4) return CURRENCY_OPTIONS.some((currency) => currency.code === draft.default_currency_code) && draft.timezone.length > 0
  return true
})

onMounted(() => {
  ledgerStore.fetchLedgers()
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

async function submitLedger() {
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    if (!draft.subject_enabled) draft.subject_step_mode = 'disabled'
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
  max-width: 960px;
  margin: 0 auto;
  padding: 24px;
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

.segmented,
.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.segmented label,
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

.bottom-actions {
  display: grid;
  margin-top: 18px;
}

.ledger-card {
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.ledger-main {
  display: grid;
  justify-items: start;
  flex: 1;
  min-width: 0;
  border: 0;
  padding: 0;
}

.ledger-main span {
  color: #607086;
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
    align-items: stretch;
    flex-direction: column;
  }

  .segmented,
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>
