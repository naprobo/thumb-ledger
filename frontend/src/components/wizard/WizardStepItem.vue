<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.itemName') }}</h2>
    <div class="chip-grid">
      <button
        v-for="item in items"
        :key="item"
        type="button"
        :class="{ selected: item === modelValue }"
        @click="$emit('select', item)"
      >
        {{ translateLabel(item, t) }}
      </button>
      <button type="button" class="add-chip" :class="{ selected: isCustomOpen }" @click="openCustom">
        <Plus :size="20" aria-hidden="true" />
        <span>{{ t('transaction.customItem') }}</span>
      </button>
    </div>
    <label v-if="isCustomOpen" class="custom-item-field">
      <span>{{ t('transaction.itemName') }}</span>
      <input
        ref="customInput"
        v-model.trim="customValue"
        maxlength="100"
        :placeholder="t('transaction.customItemPlaceholder')"
        @keyup.enter="confirmCustom"
      />
      <button type="button" class="primary-button" :disabled="!customValue" @click="confirmCustom">
        OK
      </button>
    </label>
  </section>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus } from '@lucide/vue'
import { translateLabel } from '@/i18n/labels'

const props = defineProps<{ items: string[]; modelValue: string }>()
const emit = defineEmits<{ select: [item: string] }>()
const { t } = useI18n()
const isCustomOpen = ref(false)
const customValue = ref('')
const customInput = ref<HTMLInputElement | null>(null)

watch(() => props.modelValue, (value) => {
  if (!value || props.items.includes(value)) return
  customValue.value = value
  isCustomOpen.value = true
})

async function openCustom() {
  isCustomOpen.value = true
  await nextTick()
  customInput.value?.focus()
}

function confirmCustom() {
  if (customValue.value) emit('select', customValue.value)
}
</script>

<style scoped>
.add-chip {
  display: inline-grid;
  grid-auto-flow: column;
  place-content: center;
  align-items: center;
  gap: 8px;
  border-style: dashed;
}

.custom-item-field {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 88px;
  gap: 8px;
}

.custom-item-field span {
  grid-column: 1 / -1;
}

.primary-button {
  min-width: 88px;
  border-color: #16a34a;
  background: #16a34a;
  color: #fff;
  font-weight: 700;
}
</style>
