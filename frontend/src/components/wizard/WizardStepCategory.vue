<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.category') }}</h2>
    <div class="chip-grid">
      <v-btn
        v-for="category in categories"
        :key="category"
        class="choice-button"
        :class="{ selected: category === modelValue }"
        :color="category === modelValue ? 'primary' : undefined"
        :variant="category === modelValue ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="$emit('select', category)"
      >
        {{ translateLabel(category, t) }}
      </v-btn>
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
