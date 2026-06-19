<template>
  <section ref="wizardShell" class="wizard-shell">
    <header class="wizard-titlebar">
      <button
        v-if="!showDone"
        type="button"
        class="back-button"
        :aria-label="t('common.back')"
        :title="t('common.back')"
        @click="goBack"
      >
        <ChevronLeft :size="26" aria-hidden="true" />
      </button>
      <span v-else class="title-spacer" aria-hidden="true" />
      <h2>{{ titleText }}</h2>
      <button
        v-if="!showDone && currentStep === 'subject'"
        type="button"
        class="title-action-button"
        :aria-label="subjectDeleteMode ? t('common.cancel') : t('admin.delete')"
        :title="subjectDeleteMode ? t('common.cancel') : t('admin.delete')"
        @click="subjectDeleteMode = !subjectDeleteMode"
      >
        <X v-if="subjectDeleteMode" :size="24" aria-hidden="true" />
        <Trash2 v-else :size="24" aria-hidden="true" />
      </button>
      <span v-else class="title-spacer" aria-hidden="true" />
    </header>

    <template v-if="!showDone">
      <WizardStepAmount
        v-if="currentStep === 'amount'"
        :amount="draft.amount"
        :currency-code="draft.currencyCode"
        :transaction-date="draft.transactionDate"
        @change="handleAmount"
        @date-change="draft.transactionDate = $event"
      />
      <WizardStepCategory
        v-else-if="currentStep === 'category'"
        :categories="categories"
        :model-value="draft.category"
        @select="selectCategory"
      />
      <WizardStepItem
        v-else-if="currentStep === 'item'"
        :items="items"
        :model-value="draft.itemName"
        @select="selectItem"
      />
      <WizardStepNecessity
        v-else-if="currentStep === 'necessity'"
        :model-value="draft.necessity"
        :optional="ledger.necessity_step_mode === 'optional'"
        @select="selectNecessity"
        @disable="disableNecessityStep"
      />
      <WizardStepSubject
        v-else-if="currentStep === 'subject'"
        :subjects="subjects"
        :model-value="draft.subjectIds"
        :optional="ledger.subject_step_mode === 'optional'"
        :delete-mode="subjectDeleteMode"
        :custom-limit-reached="customSubjectCount >= 20"
        @toggle="toggleSubject"
        @confirm="confirmSubjects"
        @create="createCustomSubject"
        @remove="removeSubject"
        @skip-forever="disableSubjectStep"
      />

      <p v-if="isSaving" class="status">{{ t('app.loading') }}</p>
    </template>

    <div v-else class="done-panel">
      <p>{{ t('transaction.saved') }}</p>
      <button type="button" class="primary-button" @click="recordAnother">{{ t('transaction.saveAnother') }}</button>
      <button type="button" @click="$emit('done')">{{ t('transaction.done') }}</button>
    </div>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronLeft, Trash2, X } from '@lucide/vue'

import type { Ledger } from '@/api/ledgers'
import { createSubject, deleteSubject, getPreferredCategories, getPreferredItems, getSubjectPreferenceDetails, listSubjects, type Subject } from '@/api/preferences'
import { createTransaction, type Necessity } from '@/api/transactions'
import WizardStepAmount from '@/components/wizard/WizardStepAmount.vue'
import WizardStepCategory from '@/components/wizard/WizardStepCategory.vue'
import WizardStepItem from '@/components/wizard/WizardStepItem.vue'
import WizardStepNecessity from '@/components/wizard/WizardStepNecessity.vue'
import WizardStepSubject, { type SubjectChoice } from '@/components/wizard/WizardStepSubject.vue'
import { buildWizardSteps, type WizardDraft } from '@/components/wizard/types'

const props = defineProps<{ ledger: Ledger }>()
const emit = defineEmits<{ saved: []; done: []; updateLedger: [payload: Partial<Ledger>] }>()
const { t } = useI18n()

const categories = ref<string[]>([])
const items = ref<string[]>([])
const subjects = ref<SubjectChoice[]>([])
const currentIndex = ref(0)
const isSaving = ref(false)
const showDone = ref(false)
const errorMessage = ref('')
const subjectDeleteMode = ref(false)
const wizardShell = ref<HTMLElement | null>(null)
const draft = reactive<WizardDraft>(defaultDraft())

const steps = computed(() => buildWizardSteps(props.ledger))
const currentStep = computed(() => steps.value[currentIndex.value])
const isFinalStep = computed(() => currentIndex.value >= steps.value.length - 1)
const customSubjectCount = computed(() => subjects.value.filter((subject) => !subject.is_preset).length)
const titleText = computed(() => {
  if (showDone.value) return t('transaction.saved')
  switch (currentStep.value) {
    case 'amount':
      return t('transaction.amountInput')
    case 'category':
      return t('transaction.category')
    case 'item':
      return t('transaction.itemName')
    case 'necessity':
      return t('transaction.necessity')
    case 'subject':
      return t('transaction.subject')
    default:
      return ''
  }
})

onMounted(async () => {
  await loadPreferences()
})

watch(
  () => props.ledger.id,
  async () => {
    reset()
    await loadPreferences()
  },
)

watch(
  () => draft.category,
  async (category) => {
    if (category && props.ledger.entry_mode === 'item') {
      items.value = await getPreferredItems(props.ledger.id, category)
    }
  },
)

watch([currentIndex, showDone], async () => {
  await resetWizardScroll()
})

function defaultDraft(): WizardDraft {
  return {
    amount: null,
    currencyCode: props.ledger.default_currency_code,
    transactionDate: formatDate(new Date()),
    category: '',
    itemName: '',
    necessity: null,
    subjectName: '',
    subjectIds: [],
    note: '',
  }
}

async function loadPreferences() {
  categories.value = await getPreferredCategories(props.ledger.id)
  const preferredSubjects = await getSubjectPreferenceDetails(props.ledger.id)
  const subjectRows = await listSubjects(props.ledger.id)
  subjects.value = preferredSubjects
    .map((preference) => {
      const subject = subjectRows.find((row) => row.name === preference.value)
      if (!subject) return null
      return {
        ...subject,
        selection_count: preference.selection_count,
        last_selected_at: preference.last_selected_at,
      }
    })
    .filter((subject): subject is SubjectChoice => !!subject)
}

function handleAmount(value: { amount: number | null; currencyCode: string }) {
  draft.amount = value.amount
  draft.currencyCode = value.currencyCode
  if (draft.amount) next()
}

async function selectCategory(category: string) {
  draft.category = category
  if (props.ledger.entry_mode === 'item') {
    next()
    return
  }
  await advanceOrSave()
}

async function selectItem(item: string) {
  draft.itemName = item
  if (item.trim()) await advanceOrSave()
}

async function selectNecessity(necessity: Necessity) {
  draft.necessity = necessity
  await advanceOrSave()
}

function toggleSubject(subject: Subject) {
  if (draft.subjectIds.includes(subject.id)) {
    draft.subjectIds = draft.subjectIds.filter((subjectId) => subjectId !== subject.id)
    return
  }
  draft.subjectIds = [...draft.subjectIds, subject.id]
}

async function confirmSubjects() {
  if (props.ledger.subject_step_mode === 'required' && draft.subjectIds.length === 0) return
  await advanceOrSave()
}

async function createCustomSubject(name: string) {
  if (!name.trim() || customSubjectCount.value >= 20) return
  const subject = await createSubject(props.ledger.id, name.trim())
  subjects.value = [...subjects.value, subject]
  draft.subjectIds = [...draft.subjectIds, subject.id]
}

async function removeSubject(subject: Subject) {
  await deleteSubject(props.ledger.id, subject.id)
  draft.subjectIds = draft.subjectIds.filter((subjectId) => subjectId !== subject.id)
  subjects.value = subjects.value.filter((item) => item.id !== subject.id)
}

function next() {
  if (currentIndex.value < steps.value.length - 1) {
    currentIndex.value += 1
  }
}

function goBack() {
  if (currentIndex.value <= 0) {
    emit('done')
    return
  }
  currentIndex.value -= 1
}

async function advanceOrSave() {
  if (isFinalStep.value) {
    await save()
    return
  }
  next()
}

async function disableNecessityStep() {
  const shouldSave = isFinalStep.value
  draft.necessity = 'essential'
  emit('updateLedger', { necessity_step_mode: 'disabled' })
  if (shouldSave) {
    await save()
  }
}

async function disableSubjectStep() {
  const shouldSave = isFinalStep.value
  emit('updateLedger', { subject_step_mode: 'disabled' })
  if (shouldSave) {
    await save()
  }
}

async function save() {
  if (!draft.amount || isSaving.value || showDone.value) return
  isSaving.value = true
  errorMessage.value = ''
  try {
    const items = draft.category
      ? [
          {
            category_name: draft.category,
            item_name: props.ledger.entry_mode === 'item' ? draft.itemName : undefined,
            amount: draft.amount,
            currency_code: draft.currencyCode,
          },
        ]
      : []
    const payload = {
      amount: draft.amount,
      currency_code: draft.currencyCode,
      transaction_date: draft.transactionDate,
      necessity: props.ledger.necessity_step_mode !== 'disabled' ? draft.necessity || 'essential' : 'essential',
      note: draft.note || undefined,
      items,
      subject_ids: draft.subjectIds,
    }
    await createTransaction(props.ledger.id, payload)
    emit('saved')
    showDone.value = true
  } catch {
    errorMessage.value = t('errors.validationError')
  } finally {
    isSaving.value = false
  }
}

async function recordAnother() {
  reset()
  showDone.value = false
  await loadPreferences()
}

function reset() {
  Object.assign(draft, defaultDraft())
  currentIndex.value = 0
  errorMessage.value = ''
  subjectDeleteMode.value = false
}

function formatDate(value: Date): string {
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${value.getFullYear()}-${month}-${day}`
}

async function resetWizardScroll() {
  await nextTick()
  const scrollTargets: Array<HTMLElement | Element | null | undefined> = [
    wizardShell.value,
    wizardShell.value?.parentElement,
    document.scrollingElement,
  ]
  for (const target of scrollTargets) {
    if (!target) continue
    if ('scrollTo' in target && typeof target.scrollTo === 'function') {
      target.scrollTo({ top: 0, left: 0, behavior: 'auto' })
    } else {
      target.scrollTop = 0
    }
  }
  if (navigator.userAgent.includes('jsdom')) return
  try {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  } catch {
    // Some test environments expose scrollTo without implementing it.
  }
}
</script>

<style scoped>
.wizard-shell {
  display: grid;
  gap: 16px;
  min-height: 100dvh;
  align-content: start;
  padding: 16px 0;
  background: #fff;
}

.wizard-titlebar,
.done-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.wizard-titlebar {
  min-height: 48px;
}

.wizard-titlebar h2 {
  min-width: 0;
  margin: 0;
  overflow: hidden;
  font-size: 1.25rem;
  font-weight: 800;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.back-button,
.title-spacer,
.title-action-button {
  width: 48px;
  min-width: 48px;
  height: 48px;
}

.back-button,
.title-action-button {
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
  padding: 0;
  line-height: 1;
}

.title-spacer {
  display: block;
}

.done-panel {
  align-content: start;
  align-items: stretch;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  min-height: 0;
}

.done-panel p {
  display: none;
}

.done-panel button {
  min-height: 132px;
  font-size: 1.05rem;
  font-weight: 800;
  white-space: normal;
}

:deep(.wizard-step) {
  align-content: start;
  display: grid;
  gap: 14px;
  min-height: 0;
}

:deep(.wizard-step h2) {
  display: none;
}

:deep(label) {
  display: grid;
  gap: 6px;
  font-weight: 700;
}

:deep(input),
button {
  min-height: 44px;
  border-radius: 6px;
  font: inherit;
}

:deep(input) {
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
  border-color: #16a34a;
  background: #16a34a;
  color: #fff;
  font-weight: 700;
}

:deep(.chip-grid) {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

:deep(.chip-grid button) {
  min-height: 104px;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 1.05rem;
  font-weight: 800;
  line-height: 1.25;
  white-space: normal;
}

:deep(.selected) {
  border-color: #2563eb;
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 700;
}

:deep(.ghost-button) {
  justify-self: start;
}

.error {
  color: #b42318;
}

.status {
  color: #607086;
}

@media (max-width: 640px) {
  .done-panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 420px) {
  :deep(.chip-grid) {
    grid-template-columns: 1fr;
  }
}
</style>
