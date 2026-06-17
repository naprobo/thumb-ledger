<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.necessity') }}</h2>
    <div class="chip-grid">
      <button type="button" :class="{ selected: modelValue === 'essential' }" @click="$emit('select', 'essential')">
        {{ t('transaction.essential') }}
      </button>
      <button type="button" :class="{ selected: modelValue === 'non-essential' }" @click="$emit('select', 'non-essential')">
        {{ t('transaction.nonEssential') }}
      </button>
      <button v-if="optional" type="button" @click="$emit('disable')">
        {{ t('transaction.closeStep') }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { Necessity } from '@/api/transactions'

defineProps<{ modelValue: Necessity | null; optional: boolean }>()
const emit = defineEmits<{ select: [value: Necessity]; disable: [] }>()
const { t } = useI18n()
</script>
