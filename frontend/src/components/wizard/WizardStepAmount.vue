<template>
  <section class="wizard-step amount-step">
    <div class="date-selector">
      <button type="button" class="date-side-button" @click="selectPreviousDate">
        <span v-if="isTodaySelected">{{ t('transaction.yesterday') }}</span>
        <ChevronLeft v-else :size="22" aria-hidden="true" />
      </button>
      <strong>{{ selectedDateLabel }}</strong>
      <button
        type="button"
        class="calendar-button"
        :aria-label="t('transaction.openCalendar')"
        :title="t('transaction.openCalendar')"
        @click="openCalendar"
      >
        <CalendarDays :size="22" aria-hidden="true" />
      </button>
    </div>

    <div class="amount-display" aria-live="polite">
      <span>{{ localCurrency }}</span>
      <strong>{{ displayAmount }}</strong>
    </div>

    <div class="keypad" :aria-label="t('transaction.amountKeypad')">
      <button v-for="key in digitKeys" :key="key" type="button" @click="appendDigit(key)">
        {{ key }}
      </button>
      <button type="button" @click="clearAmount">{{ t('transaction.clear') }}</button>
      <button type="button" @click="appendDigit('0')">0</button>
      <button type="button" :disabled="fractionDigits === 0 || amountText.includes('.')" @click="appendDecimal">.</button>
      <button type="button" class="ok-key" :disabled="!numericAmount" @click="emitChange">OK</button>
    </div>

    <div v-if="isCalendarOpen" class="modal-backdrop" role="presentation" @click.self="isCalendarOpen = false">
      <section class="calendar-dialog" role="dialog" aria-modal="true" :aria-label="t('transaction.date')">
        <header class="calendar-header">
          <h2>{{ t('transaction.date') }}</h2>
          <button type="button" :aria-label="t('common.cancel')" :title="t('common.cancel')" @click="isCalendarOpen = false">
            <X :size="22" aria-hidden="true" />
          </button>
        </header>
        <VueDatePicker
          :model-value="props.transactionDate"
          model-type="yyyy-MM-dd"
          :max-date="todayIso"
          :locale="datepickerLocale"
          :week-start="datepickerWeekStart"
          :enable-time-picker="false"
          :month-change-on-scroll="false"
          inline
          auto-apply
          @update:model-value="selectCalendarDate"
        />
        <div class="calendar-shortcuts">
          <button type="button" @click="selectShortcutDate(todayIso)">{{ t('transaction.today') }}</button>
          <button type="button" @click="selectShortcutDate(yesterdayIso)">{{ t('transaction.yesterday') }}</button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { CalendarDays, ChevronLeft, X } from '@lucide/vue'
import { VueDatePicker } from '@vuepic/vue-datepicker'
import { enUS, ja, zhCN } from 'date-fns/locale'
import { currencyFractionDigits } from '@/utils/money'
import '@vuepic/vue-datepicker/dist/main.css'

const props = defineProps<{ amount: number | null; currencyCode: string; transactionDate: string }>()
const emit = defineEmits<{
  change: [value: { amount: number | null; currencyCode: string }]
  dateChange: [value: string]
}>()
const { t, locale } = useI18n()
const amountText = ref('')
const localCurrency = ref(props.currencyCode)
const isCalendarOpen = ref(false)
const digitKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
const todayIso = computed(() => formatIsoDate(new Date()))
const yesterdayIso = computed(() => addDays(todayIso.value, -1))
const isTodaySelected = computed(() => props.transactionDate === todayIso.value)
const fractionDigits = computed(() => currencyFractionDigits(localCurrency.value))
const numericAmount = computed(() => {
  const parsed = parseMinorAmount(amountText.value, fractionDigits.value)
  return parsed && Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null
})
const displayAmount = computed(() => formatDisplayAmount(amountText.value))
const selectedDateLabel = computed(() => formatDisplayDate(props.transactionDate, true))
const previousDateLabel = computed(() => formatDisplayDate(addDays(props.transactionDate, -1), false))
const datepickerLocale = computed(() => {
  if (locale.value === 'ja') return ja
  if (locale.value === 'en') return enUS
  return zhCN
})
const datepickerWeekStart = computed(() => (locale.value === 'en' ? 0 : 1))

watch(() => props.amount, (value) => {
  amountText.value = value ? formatMinorAmount(value, fractionDigits.value) : ''
}, { immediate: true })

watch(() => props.currencyCode, (value) => {
  localCurrency.value = value
})

function selectPreviousDate() {
  emit('dateChange', addDays(props.transactionDate, -1))
}

function openCalendar() {
  isCalendarOpen.value = true
}

function selectCalendarDate(value: string | Date | null) {
  if (!value) return
  const isoValue = typeof value === 'string' ? value : formatIsoDate(value)
  const selected = isoValue > todayIso.value ? todayIso.value : isoValue
  emit('dateChange', selected)
  isCalendarOpen.value = false
}

function selectShortcutDate(value: string) {
  emit('dateChange', value)
  isCalendarOpen.value = false
}

function appendDigit(digit: string) {
  triggerKeyFeedback()
  if (amountText.value === '0') {
    amountText.value = digit
    return
  }
  const decimalIndex = amountText.value.indexOf('.')
  if (decimalIndex >= 0 && amountText.value.length - decimalIndex - 1 >= fractionDigits.value) return
  if (amountText.value.replace('.', '').length < 12) {
    amountText.value += digit
  }
}

function appendDecimal() {
  triggerKeyFeedback()
  if (fractionDigits.value === 0 || amountText.value.includes('.')) return
  amountText.value = amountText.value ? `${amountText.value}.` : '0.'
}

function clearAmount() {
  triggerKeyFeedback()
  amountText.value = ''
}

function emitChange() {
  triggerKeyFeedback()
  emit('change', {
    amount: numericAmount.value,
    currencyCode: localCurrency.value.toUpperCase(),
  })
}

function triggerKeyFeedback() {
  if (typeof navigator === 'undefined' || typeof navigator.vibrate !== 'function') return
  navigator.vibrate(8)
}

function parseMinorAmount(value: string, scale: number): number | null {
  if (!value || value === '.') return null
  if (!/^\d+(\.\d*)?$/.test(value)) return null
  const [whole, fraction = ''] = value.split('.')
  if (fraction.length > scale) return null
  const major = Number(whole)
  if (!Number.isSafeInteger(major)) return null
  const minorText = fraction.padEnd(scale, '0')
  const minor = minorText ? Number(minorText) : 0
  const amount = major * 10 ** scale + minor
  return Number.isSafeInteger(amount) ? amount : null
}

function formatMinorAmount(value: number, scale: number): string {
  if (scale === 0) return String(value)
  const divisor = 10 ** scale
  const whole = Math.floor(value / divisor)
  const fraction = String(value % divisor).padStart(scale, '0').replace(/0+$/, '')
  return fraction ? `${whole}.${fraction}` : String(whole)
}

function formatDisplayAmount(value: string): string {
  if (!value) return '0'
  const [whole, fraction] = value.split('.')
  const groupedWhole = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  if (value.endsWith('.')) return `${groupedWhole}.`
  return fraction === undefined ? groupedWhole : `${groupedWhole}.${fraction}`
}

function formatDisplayDate(value: string, includeRelative: boolean): string {
  const [year, month, day] = value.split('-').map(Number)
  const dateText = `${year}/${month}/${day}`
  if (!includeRelative) {
    if (value === yesterdayIso.value) return t('transaction.yesterday')
    return dateText
  }
  if (value === todayIso.value) return `${dateText}(${t('transaction.today')})`
  if (value === yesterdayIso.value) return `${dateText}(${t('transaction.yesterday')})`
  return dateText
}

function addDays(value: string, days: number): string {
  const [year, month, day] = value.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  date.setDate(date.getDate() + days)
  return formatIsoDate(date)
}

function formatIsoDate(value: Date): string {
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${value.getFullYear()}-${month}-${day}`
}
</script>

<style scoped>
.amount-step {
  align-content: start;
  gap: 18px;
}

.date-selector {
  display: grid;
  grid-template-columns: minmax(76px, auto) minmax(0, 1fr) 52px;
  align-items: center;
  gap: 10px;
}

.date-selector strong {
  overflow: hidden;
  font-size: 1rem;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.date-side-button,
.calendar-button {
  display: inline-grid;
  place-items: center;
  min-height: 44px;
  border: 1px solid #c9d1dc;
  border-radius: 8px;
  background: #fff;
  font: inherit;
  font-weight: 800;
}

.calendar-button {
  padding: 0;
}

.amount-display {
  display: grid;
  gap: 4px;
  min-height: 108px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 16px;
  background: #f8fafc;
}

.amount-display span {
  color: #607086;
  font-weight: 700;
}

.amount-display strong {
  overflow-wrap: anywhere;
  font-size: 2.4rem;
  line-height: 1.15;
  text-align: right;
}

.keypad {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.keypad button {
  min-height: 64px;
  border: 1px solid #c9d1dc;
  border-radius: 8px;
  background: #fff;
  font: inherit;
  font-size: 1.25rem;
  font-weight: 800;
}

.keypad .ok-key {
  grid-column: 1 / -1;
  border-color: #16a34a;
  background: #16a34a;
  color: #fff;
}

.keypad button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: start center;
  overflow-y: auto;
  padding: 72px 16px 24px;
  background: rgb(15 23 42 / 42%);
}

.calendar-dialog {
  display: grid;
  width: min(100%, 440px);
  gap: 14px;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  box-shadow: 0 24px 60px rgb(15 23 42 / 22%);
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.calendar-header h2 {
  margin: 0;
  font-size: 1.15rem;
}

.calendar-header button {
  display: inline-grid;
  width: 44px;
  min-width: 44px;
  height: 44px;
  min-height: 44px;
  place-items: center;
  border: 1px solid #c9d1dc;
  border-radius: 50%;
  background: #fff;
  padding: 0;
}

.calendar-shortcuts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.calendar-shortcuts button {
  min-height: 52px;
  border: 1px solid #c9d1dc;
  border-radius: 8px;
  background: #fff;
  font: inherit;
  font-weight: 800;
}

:deep(.dp--main) {
  font-family: inherit;
}

:deep(.dp--menu) {
  width: 100%;
  border: 1px solid #d9dee7;
  border-radius: 8px;
}

:deep(.dp--calendar-header),
:deep(.dp--calendar-row) {
  gap: 4px;
}

:deep(.dp--calendar-header-item),
:deep(.dp--cell-inner) {
  width: 100%;
  min-width: 42px;
  height: 48px;
  border-radius: 8px;
  font-size: 1rem;
}

:deep(.dp--month-year-row) {
  height: 52px;
}

:deep(.dp--month-year-select),
:deep(.dp--btn) {
  min-height: 44px;
  border-radius: 8px;
  font: inherit;
  font-weight: 800;
}

@media (max-width: 640px) {
  .amount-display strong {
    font-size: 2rem;
  }

  .modal-backdrop {
    align-items: start;
    padding: 56px 12px 18px;
  }

  .calendar-dialog {
    width: 100%;
  }
}
</style>
