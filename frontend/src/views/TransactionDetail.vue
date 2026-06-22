<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="title-row">
        <v-btn
          class="back-button"
          variant="text"
          icon
          :aria-label="t('common.back')"
          :title="t('common.back')"
          @click="router.push({ name: 'ledger-detail', params: { id: ledgerId } })"
        >
          <ChevronLeft :size="24" aria-hidden="true" />
        </v-btn>
        <h1>{{ t('transaction.detail') }}</h1>
      </div>
    </header>

    <AppLoadingPanel v-if="isInitialLoading" class="detail-loading" />

    <v-card v-else-if="transaction" class="detail-card" variant="outlined" rounded="lg">
      <v-card-text>
        <div class="amount-line">
          <strong>{{ formatMoney(transaction.amount, transaction.currency_code) }}</strong>
          <span>{{ transaction.transaction_date }}</span>
        </div>

        <dl class="detail-list">
          <div>
            <dt>{{ t('transaction.category') }}</dt>
            <dd>{{ categoryLabel }}</dd>
          </div>
          <div>
            <dt>{{ t('transaction.itemName') }}</dt>
            <dd>{{ itemLabel }}</dd>
          </div>
          <div v-if="ledger?.necessity_step_mode !== 'disabled'">
            <dt>{{ t('transaction.necessity') }}</dt>
            <dd>{{ necessityLabel(transaction.necessity) }}</dd>
          </div>
          <div>
            <dt>{{ t('transaction.subject') }}</dt>
            <dd>{{ subjectLabels || t('transaction.noSubjects') }}</dd>
          </div>
          <div>
            <dt>{{ t('transaction.note') }}</dt>
            <dd>{{ transaction.note || '-' }}</dd>
          </div>
        </dl>

        <section v-if="transaction.items.length > 1" class="items-section">
          <h2>{{ t('transaction.categoryDetail') }}</h2>
          <ul>
            <li v-for="item in transaction.items" :key="item.id">
              <span>{{ translateLabel(item.item_name || item.category_name_snapshot, t) }}</span>
              <strong>{{ formatMoney(item.amount, item.currency_code) }}</strong>
            </li>
          </ul>
        </section>
      </v-card-text>

      <v-card-actions class="card-actions">
        <v-btn variant="tonal" color="primary" @click="startEdit">{{ t('transaction.edit') }}</v-btn>
        <v-btn variant="tonal" color="error" :loading="isDeleting" @click="deleteCurrentTransaction">
          {{ t('transaction.delete') }}
        </v-btn>
      </v-card-actions>
    </v-card>

    <v-card v-if="isEditing && transaction" class="edit-card" variant="outlined" rounded="lg">
      <v-card-title>{{ t('transaction.edit') }}</v-card-title>
      <v-card-text>
        <form class="edit-form" @submit.prevent="saveEdit">
          <v-text-field
            v-model="draft.amount"
            :label="t('transaction.amount')"
            inputmode="decimal"
            :disabled="!canEditSimpleEntry"
            variant="outlined"
            density="comfortable"
          />
          <v-text-field
            v-model="draft.transactionDate"
            :label="t('transaction.date')"
            type="date"
            variant="outlined"
            density="comfortable"
          />
          <v-select
            v-model="draft.category"
            :items="categoryOptions"
            item-title="label"
            item-value="value"
            :label="t('transaction.category')"
            :disabled="!canEditSimpleEntry"
            variant="outlined"
            density="comfortable"
          />
          <v-text-field
            v-model.trim="draft.itemName"
            :label="t('transaction.itemName')"
            :disabled="!canEditSimpleEntry"
            maxlength="100"
            variant="outlined"
            density="comfortable"
          />
          <v-select
            v-if="ledger?.necessity_step_mode !== 'disabled'"
            v-model="draft.necessity"
            :items="necessityOptions"
            item-title="label"
            item-value="value"
            :label="t('transaction.necessity')"
            variant="outlined"
            density="comfortable"
          />
          <v-select
            v-if="ledger?.subject_step_mode !== 'disabled'"
            v-model="draft.subjectIds"
            :items="subjectOptions"
            item-title="label"
            item-value="value"
            :label="t('transaction.subject')"
            multiple
            chips
            closable-chips
            variant="outlined"
            density="comfortable"
          />
          <v-textarea
            v-model.trim="draft.note"
            :label="t('transaction.note')"
            maxlength="500"
            variant="outlined"
            density="comfortable"
            rows="3"
          />
          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
          <div class="form-actions">
            <v-btn variant="text" type="button" @click="isEditing = false">{{ t('common.cancel') }}</v-btn>
            <v-btn color="primary" type="submit" :loading="isSaving">{{ t('common.save') }}</v-btn>
          </div>
        </form>
      </v-card-text>
    </v-card>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft } from '@lucide/vue'

import { listCategories, type Category } from '@/api/ledgers'
import { deleteTransaction, getTransaction, updateTransaction, type Necessity, type Transaction } from '@/api/transactions'
import { listSubjects, type Subject } from '@/api/preferences'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'
import { translateLabel } from '@/i18n/labels'
import { useLedgerStore } from '@/stores/ledgers'
import { formatMoney, formatMoneyInputValue, parseMoneyInputValue } from '@/utils/money'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const ledgerStore = useLedgerStore()
const ledgerId = computed(() => String(route.params.id))
const transactionId = computed(() => String(route.params.transactionId))
const ledger = computed(() => ledgerStore.activeLedger)
const transaction = ref<Transaction | null>(null)
const categories = ref<Category[]>([])
const subjects = ref<Subject[]>([])
const isEditing = ref(false)
const isInitialLoading = ref(true)
const isSaving = ref(false)
const isDeleting = ref(false)
const errorMessage = ref('')

const draft = reactive({
  amount: '',
  transactionDate: '',
  category: '',
  itemName: '',
  originalItemName: '',
  necessity: 'essential' as Necessity,
  note: '',
  subjectIds: [] as string[],
})

const firstItem = computed(() => transaction.value?.items[0])
const canEditSimpleEntry = computed(() => (transaction.value?.items.length || 0) <= 1)
const categoryLabel = computed(() => translateLabel(firstItem.value?.category_name_snapshot, t))
const itemLabel = computed(() => (firstItem.value?.item_name ? translateLabel(firstItem.value.item_name, t) : '-'))
const subjectOptions = computed(() => subjects.value.map((subject) => ({ label: translateLabel(subject.name, t), value: subject.id })))
const categoryOptions = computed(() => categories.value.map((category) => ({ label: translateLabel(category.name, t), value: category.name })))
const necessityOptions = computed(() => [
  { label: t('transaction.essential'), value: 'essential' },
  { label: t('transaction.nonEssential'), value: 'non-essential' },
])
const subjectLabels = computed(() => {
  const selected = transaction.value?.transaction_subjects.map((row) => row.subject_id) || []
  return subjects.value
    .filter((subject) => selected.includes(subject.id))
    .map((subject) => translateLabel(subject.name, t))
    .join(', ')
})

onMounted(async () => {
  try {
    await ledgerStore.fetchLedger(ledgerId.value)
    const [loadedTransaction, loadedCategories, loadedSubjects] = await Promise.all([
      getTransaction(ledgerId.value, transactionId.value),
      listCategories(ledgerId.value),
      listSubjects(ledgerId.value),
    ])
    transaction.value = loadedTransaction
    categories.value = loadedCategories
    subjects.value = loadedSubjects
  } finally {
    isInitialLoading.value = false
  }
})

function startEdit() {
  if (!transaction.value) return
  const item = transaction.value.items[0]
  draft.amount = formatMoneyInputValue(transaction.value.amount, transaction.value.currency_code)
  draft.transactionDate = transaction.value.transaction_date
  draft.category = item?.category_name_snapshot || ''
  draft.originalItemName = item?.item_name || ''
  draft.itemName = item?.item_name ? translateLabel(item.item_name, t) : ''
  draft.necessity = transaction.value.necessity === 'non-essential' ? 'non-essential' : 'essential'
  draft.note = transaction.value.note || ''
  draft.subjectIds = transaction.value.transaction_subjects.map((subject) => subject.subject_id)
  errorMessage.value = ''
  isEditing.value = true
}

async function saveEdit() {
  if (!transaction.value) return
  errorMessage.value = ''
  const parsedAmount = parseMoneyInputValue(draft.amount, transaction.value.currency_code)
  if (canEditSimpleEntry.value && parsedAmount <= 0) {
    errorMessage.value = t('errors.validationError')
    return
  }
  isSaving.value = true
  try {
    const payload = {
      transaction_date: draft.transactionDate,
      necessity: draft.necessity,
      note: draft.note || null,
      subject_ids: draft.subjectIds,
    }
    if (canEditSimpleEntry.value) {
      Object.assign(payload, {
        amount: parsedAmount,
        currency_code: transaction.value.currency_code,
        items: [
          {
            category_name: draft.category,
            item_name: itemNameForSave(),
            amount: parsedAmount,
            currency_code: transaction.value.currency_code,
          },
        ],
      })
    }
    transaction.value = await updateTransaction(ledgerId.value, transactionId.value, payload)
    isEditing.value = false
  } catch {
    errorMessage.value = t('errors.validationError')
  } finally {
    isSaving.value = false
  }
}

function itemNameForSave(): string | undefined {
  const trimmed = draft.itemName.trim()
  if (!trimmed) return undefined
  if (draft.originalItemName && trimmed === translateLabel(draft.originalItemName, t)) return draft.originalItemName
  return trimmed
}

async function deleteCurrentTransaction() {
  if (!window.confirm(t('transaction.deleteConfirm'))) return
  isDeleting.value = true
  await deleteTransaction(ledgerId.value, transactionId.value)
  await router.push({ name: 'ledger-detail', params: { id: ledgerId.value } })
}

function necessityLabel(value: string): string {
  return value === 'non-essential' ? t('transaction.nonEssential') : t('transaction.essential')
}
</script>

<style scoped>
.page-shell {
  width: min(100%, 960px);
  margin: 0 auto;
  padding: 24px clamp(12px, 3vw, 36px);
}

.topbar,
.title-row,
.card-actions,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title-row {
  justify-content: flex-start;
}

h1,
h2 {
  margin: 0;
}

h1 {
  font-size: 1.35rem;
}

h2 {
  font-size: 1rem;
}

.back-button {
  width: 44px;
  min-width: 44px;
  height: 44px;
  min-height: 44px;
  border: 0;
  background: transparent;
}

.detail-card,
.edit-card,
.detail-loading {
  margin-top: 16px;
}

.detail-loading {
  min-height: 320px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
}

.amount-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.amount-line strong {
  font-size: 1.8rem;
}

.amount-line span,
.detail-list dt {
  color: #607086;
}

.detail-list {
  display: grid;
  gap: 12px;
  margin: 0;
}

.detail-list div {
  display: grid;
  grid-template-columns: minmax(88px, 0.3fr) minmax(0, 1fr);
  gap: 12px;
}

.detail-list dt,
.detail-list dd {
  margin: 0;
}

.detail-list dd {
  min-width: 0;
  overflow-wrap: anywhere;
  font-weight: 700;
}

.items-section {
  display: grid;
  gap: 10px;
  margin-top: 20px;
}

.items-section ul {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.items-section li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.edit-form {
  display: grid;
  gap: 12px;
}

.form-actions {
  justify-content: flex-end;
}

.error {
  margin: 0;
  color: #b42318;
}
</style>
