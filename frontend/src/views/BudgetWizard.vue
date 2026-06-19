<template>
  <main class="page-shell">
    <header class="topbar">
      <div>
        <h1>{{ t('budget.title') }}</h1>
        <p>{{ step + 1 }}/4</p>
      </div>
      <button type="button" @click="router.push({ name: 'ledger-settings', params: { id: ledgerId } })">
        {{ t('nav.settings') }}
      </button>
    </header>

    <form class="budget-form" @submit.prevent="nextOrSave">
      <section v-if="step === 0">
        <h2>{{ t('budget.monthly') }}</h2>
        <input v-model.number="monthlyTotal" inputmode="numeric" min="1" type="number" required />
      </section>

      <section v-else-if="step === 1">
        <h2>{{ t('budget.annual') }}</h2>
        <input v-model.number="annualTotal" inputmode="numeric" min="1" type="number" />
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
            <input v-model.number="categoryAmounts[category.name]" inputmode="numeric" min="0" type="number" />
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

import { saveBudget } from '@/api/budget'
import { listCategories, type Category } from '@/api/ledgers'
import { translateLabel } from '@/i18n/labels'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const ledgerId = computed(() => String(route.params.id))
const step = ref(0)
const monthlyTotal = ref<number>(0)
const annualTotal = ref<number | null>(null)
const splitByCategory = ref(false)
const categories = ref<Category[]>([])
const categoryAmounts = reactive<Record<string, number>>({})
const isSaving = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')

const categoryTotal = computed(() => Object.values(categoryAmounts).reduce((sum, value) => sum + (Number(value) || 0), 0))
const canContinue = computed(() => {
  if (step.value === 0) return monthlyTotal.value > 0
  return true
})

onMounted(async () => {
  categories.value = await listCategories(ledgerId.value)
  applyDefaultCategoryAmounts()
})

function applyDefaultCategoryAmounts() {
  if (!monthlyTotal.value || categories.value.length === 0) return
  const amount = Math.floor(monthlyTotal.value / categories.value.length)
  for (const category of categories.value) {
    categoryAmounts[category.name] = categoryAmounts[category.name] ?? amount
  }
}

function skipAnnual() {
  annualTotal.value = null
  step.value = 2
}

function skipCategorySplit() {
  splitByCategory.value = false
  submitBudget()
}

async function nextOrSave() {
  if (step.value === 0) {
    applyDefaultCategoryAmounts()
    step.value = 1
    return
  }
  if (step.value === 1) {
    step.value = 2
    return
  }
  if (step.value === 2 && splitByCategory.value) {
    applyDefaultCategoryAmounts()
    step.value = 3
    return
  }
  await submitBudget()
}

async function submitBudget() {
  if (!monthlyTotal.value) return
  isSaving.value = true
  errorMessage.value = ''
  try {
    await saveBudget(ledgerId.value, {
      monthly_total: monthlyTotal.value,
      annual_total: annualTotal.value || undefined,
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
.actions,
.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
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
</style>
