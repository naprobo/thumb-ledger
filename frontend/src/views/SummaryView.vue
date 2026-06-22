<template>
  <main class="page-shell">
    <header class="topbar">
      <h1>{{ t('summary.title') }}</h1>
      <button type="button" @click="router.push({ name: 'ledger-detail', params: { id: ledgerId } })">
        {{ t('transaction.list') }}
      </button>
    </header>

    <section class="filters">
      <div class="segmented">
        <button v-for="option in ranges" :key="option.value" type="button" :class="{ selected: timeRange === option.value }" @click="selectRange(option.value)">
          {{ option.label }}
        </button>
      </div>
      <div v-if="timeRange === 'custom'" class="date-grid">
        <input v-model="startDate" type="date" />
        <input v-model="endDate" type="date" />
        <button type="button" @click="loadSummary">{{ t('common.refresh') }}</button>
      </div>
    </section>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <AppLoadingPanel v-if="isInitialLoading" class="summary-loading" />

    <section v-else class="summary-grid">
      <SummaryGroupList :title="t('summary.byCategory')" :items="displaySummary.categories" />
      <SummaryGroupList :title="t('summary.bySubject')" :items="displaySummary.subjects" />
      <SummaryGroupList :title="t('summary.byNecessity')" :items="displaySummary.necessities" />
    </section>
  </main>
</template>

<script setup lang="ts">
import { defineComponent, h, onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { getLedgerSummary, type LedgerSummary, type SummaryGroup } from '@/api/transactions'
import AppLoadingPanel from '@/components/AppLoadingPanel.vue'
import { translateLabel } from '@/i18n/labels'
import { formatMoney } from '@/utils/money'

type TimeRange = 'week' | 'month' | 'year' | 'custom'

const SummaryGroupList = defineComponent({
  props: {
    title: { type: String, required: true },
    items: { type: Array as () => SummaryGroup[], required: true },
  },
  setup(props) {
    return () =>
      h('section', { class: 'summary-card' }, [
        h('h2', props.title),
        props.items.length
          ? h(
              'ul',
              props.items.map((item) =>
                h('li', { key: `${item.key}-${item.currency_code}` }, [
                  h('span', item.key),
                  h('strong', formatMoney(item.amount, item.currency_code)),
                ]),
              ),
            )
          : h('p', { class: 'muted' }, '-'),
      ])
  },
})

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const ledgerId = computed(() => String(route.params.id))
const timeRange = ref<TimeRange>('month')
const startDate = ref('')
const endDate = ref('')
const isInitialLoading = ref(true)
const errorMessage = ref('')
const summary = ref<LedgerSummary>({ categories: [], subjects: [], necessities: [] })
const displaySummary = computed<LedgerSummary>(() => ({
  categories: summary.value.categories.map((item) => ({ ...item, key: translateLabel(item.key, t) })),
  subjects: summary.value.subjects.map((item) => ({ ...item, key: translateLabel(item.key, t) })),
  necessities: summary.value.necessities.map((item) => ({
    ...item,
    key: item.key === 'non-essential' ? t('transaction.nonEssential') : t('transaction.essential'),
  })),
}))
const ranges = computed(() => [
  { value: 'week' as const, label: t('summary.thisWeek') },
  { value: 'month' as const, label: t('summary.thisMonth') },
  { value: 'year' as const, label: t('summary.thisYear') },
  { value: 'custom' as const, label: t('summary.custom') },
])

onMounted(loadSummary)

async function selectRange(range: TimeRange) {
  timeRange.value = range
  if (range !== 'custom') await loadSummary()
}

async function loadSummary() {
  errorMessage.value = ''
  try {
    summary.value = await getLedgerSummary(ledgerId.value, {
      time_range: timeRange.value,
      start_date: timeRange.value === 'custom' ? startDate.value : undefined,
      end_date: timeRange.value === 'custom' ? endDate.value : undefined,
    })
  } catch {
    errorMessage.value = t('errors.invalidDateRange')
  } finally {
    isInitialLoading.value = false
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
.date-grid,
:deep(.summary-card li) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

button,
input {
  min-height: 44px;
  border-radius: 6px;
  font: inherit;
}

button {
  border: 1px solid #c9d1dc;
  background: #fff;
  padding: 0 14px;
}

input {
  border: 1px solid #b8c0cc;
  padding: 10px 12px;
}

.filters {
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
}

.segmented {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.selected {
  border-color: #2563eb;
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 700;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-loading {
  min-height: 280px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
}

:deep(.summary-card) {
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}

:deep(.summary-card ul) {
  display: grid;
  gap: 8px;
  padding: 0;
  list-style: none;
}

.muted {
  color: #607086;
}

.error {
  color: #b42318;
}

@media (max-width: 760px) {
  .segmented,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .topbar,
  .date-grid,
  :deep(.summary-card li) {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
