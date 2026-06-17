<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.category') }}</h2>
    <div class="chip-grid">
      <button
        v-for="category in categories"
        :key="category"
        type="button"
        :class="{ selected: category === modelValue }"
        @click="$emit('select', category)"
      >
        {{ translateLabel(category, t) }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { translateLabel } from '@/i18n/labels'

defineProps<{ categories: string[]; modelValue: string }>()
defineEmits<{ select: [category: string] }>()
const { t } = useI18n()
</script>
