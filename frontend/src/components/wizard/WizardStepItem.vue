<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.itemName') }}</h2>
    <v-btn v-if="optional" class="skip-button" color="warning" variant="tonal" size="large" block @click="$emit('skip')">
      <AlertTriangle :size="20" aria-hidden="true" />
      <span>{{ t('transaction.skip') }}</span>
    </v-btn>
    <div class="chip-grid">
      <v-btn
        v-for="item in items"
        :key="item"
        class="choice-button"
        :class="{ selected: item === modelValue }"
        :color="item === modelValue ? 'primary' : undefined"
        :variant="item === modelValue ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="$emit('select', item)"
      >
        {{ translateLabel(item, t) }}
      </v-btn>
      <v-btn
        class="choice-button add-chip"
        :class="{ selected: isCustomOpen }"
        :color="isCustomOpen ? 'primary' : undefined"
        :variant="isCustomOpen ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="openCustom"
      >
        <Plus :size="20" aria-hidden="true" />
        <span>{{ t('transaction.customItem') }}</span>
      </v-btn>
    </div>
    <div v-if="isCustomOpen" class="custom-item-field">
      <v-text-field
        ref="customInput"
        v-model.trim="customValue"
        class="custom-input"
        :label="t('transaction.itemName')"
        maxlength="100"
        :placeholder="t('transaction.customItemPlaceholder')"
        variant="outlined"
        density="comfortable"
        hide-details
        @keyup.enter="confirmCustom"
      />
      <v-btn class="primary-button" color="success" size="large" rounded="lg" :disabled="!customValue" @click="confirmCustom">
        OK
      </v-btn>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { AlertTriangle, Plus } from '@lucide/vue'
import { translateLabel } from '@/i18n/labels'

const props = withDefaults(defineProps<{ items: string[]; modelValue: string; optional?: boolean }>(), {
  optional: false,
})
const emit = defineEmits<{ select: [item: string]; skip: [] }>()
const { t } = useI18n()
const isCustomOpen = ref(false)
const customValue = ref('')
const customInput = ref<{ focus: () => void } | null>(null)

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
  border-style: dashed;
}

.add-chip :deep(.v-btn__content) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.custom-item-field {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 88px;
  align-items: center;
  gap: 10px;
}

.primary-button {
  min-width: 88px;
  font-weight: 700;
}

.skip-button {
  margin-bottom: 4px;
  font-weight: 800;
}

.skip-button :deep(.v-btn__content) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>
