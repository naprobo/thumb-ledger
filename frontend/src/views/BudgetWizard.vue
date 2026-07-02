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
        <h1>{{ t('budget.title') }}</h1>
      </div>
      <div class="step-count">
        <p>{{ step + 1 }}/4</p>
      </div>
    </header>

    <AppLoadingPanel v-if="isInitialLoading" class="budget-loading" />

    <form v-else class="budget-form" novalidate @submit.prevent="nextOrSave">
      <section v-if="step === 0">
        <h2>{{ t('budget.monthly') }}</h2>
        <input
          v-model="monthlyInput"
          inputmode="numeric"
          min="1"
          step="1"
          type="number"
          required
          @focus="clearZeroInput('monthly')"
          @input="handleMonthlyInput"
          @blur="validateMonthly"
        />
        <p v-if="monthlyError" class="error field-error">{{ monthlyError }}</p>
      </section>

      <section v-else-if="step === 1">
        <h2>{{ t('budget.annual') }}</h2>
        <input
          v-model="annualInput"
          inputmode="numeric"
          min="1"
          step="1"
          type="number"
          required
          @focus="clearZeroInput('annual')"
          @input="handleAnnualInput"
          @blur="validateAnnual"
        />
        <p v-if="annualError" class="error field-error">{{ annualError }}</p>
        <button type="button" @click="skipAnnual">{{ t('budget.skipDefault') }}</button>
      </section>

      <section v-else-if="step === 2">
        <h2>{{ t('budget.categoryBudget') }}</h2>
        <label class="switch-row">
          <input v-model="splitByCategory" type="checkbox" />
          <span>{{ t('budget.categoryBudget') }}</span>
        </label>
        <button type="button" @click="skipCategorySplit">{{ t('budget.skipDefault') }}</button>
      </section>

      <section v-else>
        <h2>{{ t('budget.categoryBudget') }}</h2>
        <div class="category-grid">
          <label v-for="category in categories" :key="category.id">
            <span>{{ translateLabel(category.name, t) }}</span>
            <input v-model.number="categoryAmounts[category.name]" inputmode="numeric" min="0" step="1" type="number" />
          </label>
        </div>
        <p v-if="categoryTotal > monthlyTotal" class="warning">{{ t('budget.categoryOverWarning') }}</p>
      </section>

      <div class="actions">
        <button type="button" :disabled="step === 0" @click="step--">{{ t('common.back') }}</button>
        <button type="button" @click="skipBudget">{{ t('common.cancel') }}</button>
        <button class="primary-button" type="submit" :disabled="!canContinue || isSaving">
          {{ step === 3 || (step === 2 && !splitByCategory) ? t('common.save') : t('common.next') }}
        </button>
      </div>
    </form>
    <p v-if="statusMessage" class="status">{{ statusMessage }}</p>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft } from '@lucide/vue'

import { getBudget, saveBudget } from '@/api/budget'
import { listCategories, type Category } from '@/api/ledgers'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'
import { translateLabel } from '@/i18n/labels'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const ledgerId = computed(() => String(route.params.id))
const step = ref(0)
const monthlyInput = ref<string | number>('')
const annualInput = ref<string | number>('')
const annualManuallyEdited = ref(false)
const monthlyError = ref('')
const annualError = ref('')
const splitByCategory = ref(false)
const categories = ref<Category[]>([])
const categoryAmounts = reactive<Record<string, number>>({})
const isInitialLoading = ref(true)
const isSaving = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')

const monthlyTotal = computed(() => parsePositiveInteger(monthlyInput.value) || 0)
const annualTotal = computed(() => parsePositiveInteger(annualInput.value) || 0)
const categoryTotal = computed(() => Object.values(categoryAmounts).reduce((sum, value) => sum + (Number(value) || 0), 0))
const canContinue = computed(() => {
  if (step.value === 0) return monthlyTotal.value > 0
  if (step.value === 1) return annualTotal.value > 0
  return true
})

onMounted(async () => {
  try {
    const [categoryRows, budget] = await Promise.all([
      listCategories(ledgerId.value),
      getBudget(ledgerId.value),
    ])
    categories.value = categoryRows
    if (budget) {
      monthlyInput.value = String(budget.monthly_total)
      annualInput.value = String(budget.annual_total || budget.monthly_total * 12)
      annualManuallyEdited.value = budget.annual_total !== budget.monthly_total * 12
      for (const category of budget.categories || []) {
        categoryAmounts[category.category] = category.amount
      }
    }
  } finally {
    isInitialLoading.value = false
  }
})

function applyDefaultCategoryAmounts(force = false) {
  if (!monthlyTotal.value || categories.value.length === 0) return
  const amount = Math.floor(monthlyTotal.value / categories.value.length)
  for (const category of categories.value) {
    if (force || categoryAmounts[category.name] === undefined) {
      categoryAmounts[category.name] = amount
    }
  }
}

function skipAnnual() {
  annualInput.value = String(monthlyTotal.value * 12)
  annualManuallyEdited.value = false
  annualError.value = ''
  step.value = 2
}

async function skipCategorySplit() {
  splitByCategory.value = false
  await submitBudget()
}

async function nextOrSave() {
  if (step.value === 0) {
    if (!validateMonthly()) return
    if (!annualManuallyEdited.value) {
      annualInput.value = String(monthlyTotal.value * 12)
    }
    applyDefaultCategoryAmounts(false)
    step.value = 1
    return
  }
  if (step.value === 1) {
    if (!validateAnnual()) return
    step.value = 2
    return
  }
  if (step.value === 2 && splitByCategory.value) {
    applyDefaultCategoryAmounts(false)
    step.value = 3
    return
  }
  await submitBudget()
}

async function submitBudget() {
  if (!validateMonthly() || !validateAnnual() || !validateCategoryAmounts()) return
  isSaving.value = true
  errorMessage.value = ''
  try {
    await saveBudget(ledgerId.value, {
      monthly_total: monthlyTotal.value,
      annual_total: annualTotal.value,
      categories: splitByCategory.value
        ? categories.value.map((category) => ({
            category: category.name,
            amount: Number(categoryAmounts[category.name]) || 0,
          }))
        : undefined,
    })
    statusMessage.value = t('common.saved')
    await router.push({ name: 'ledger-detail', params: { id: ledgerId.value } })
  } catch {
    errorMessage.value = t('errors.validationError')
  } finally {
    isSaving.value = false
  }
}

function handleMonthlyInput() {
  monthlyError.value = ''
  if (!annualManuallyEdited.value) {
    const monthly = parsePositiveInteger(monthlyInput.value)
    annualInput.value = monthly ? String(monthly * 12) : ''
  }
}

function handleAnnualInput() {
  annualManuallyEdited.value = true
  annualError.value = ''
}

function clearZeroInput(field: 'monthly' | 'annual') {
  if (field === 'monthly' && Number(monthlyInput.value) === 0) monthlyInput.value = ''
  if (field === 'annual' && Number(annualInput.value) === 0) annualInput.value = ''
}

function parsePositiveInteger(value: string | number): number | null {
  const normalized = String(value).trim()
  if (!/^\d+$/.test(normalized)) return null
  const amount = Number(normalized)
  return Number.isSafeInteger(amount) && amount > 0 ? amount : null
}

function validateMonthly(): boolean {
  if (parsePositiveInteger(monthlyInput.value)) {
    monthlyError.value = ''
    return true
  }
  monthlyError.value = t('budget.positiveAmountError')
  return false
}

function validateAnnual(): boolean {
  if (parsePositiveInteger(annualInput.value)) {
    annualError.value = ''
    return true
  }
  annualError.value = t('budget.positiveAmountError')
  return false
}

function validateCategoryAmounts(): boolean {
  if (!splitByCategory.value) return true
  const isValid = categories.value.every((category) => {
    const amount = Number(categoryAmounts[category.name])
    return Number.isSafeInteger(amount) && amount >= 0
  })
  if (!isValid) errorMessage.value = t('errors.validationError')
  return isValid
}

async function skipBudget() {
  await router.push({ name: 'ledger-detail', params: { id: ledgerId.value } })
}
</script>

<style scoped>
.page-shell {
  width: min(100%, 1080px);
  margin: 0 auto;
  padding: 24px clamp(12px, 3vw, 36px);
}

.topbar,
.title-row,
.actions,
.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title-row {
  min-width: 0;
  justify-content: flex-start;
}

.back-button {
  display: inline-grid;
  width: 44px;
  min-width: 44px;
  height: 44px;
  min-height: 44px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  padding: 0;
  background: transparent;
  line-height: 1;
}

.step-count p {
  margin: 0;
  color: #607086;
  font-weight: 700;
}

.budget-form {
  display: grid;
  gap: 16px;
  margin-top: 20px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}

.budget-loading {
  min-height: 320px;
  margin-top: 20px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
}

section,
.category-grid {
  display: grid;
  gap: 14px;
}

label {
  display: grid;
  gap: 6px;
  font-weight: 700;
}

input,
button {
  min-height: 44px;
  border-radius: 6px;
  font: inherit;
}

input {
  border: 1px solid #b8c0cc;
  padding: 10px 12px;
}

button {
  border: 1px solid #c9d1dc;
  background: #fff;
  padding: 0 14px;
}

.primary-button {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
  font-weight: 700;
}

.warning,
.error {
  color: #b42318;
}

.status {
  color: #166534;
}

.field-error {
  margin: -6px 0 0;
  font-size: 0.9rem;
}
</style>
