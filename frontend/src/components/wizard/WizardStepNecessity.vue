<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.necessity') }}</h2>
    <div class="chip-grid">
      <v-btn
        class="choice-button"
        :class="{ selected: modelValue === 'essential' }"
        :color="modelValue === 'essential' ? 'primary' : undefined"
        :variant="modelValue === 'essential' ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="$emit('select', 'essential')"
      >
        {{ t('transaction.essential') }}
      </v-btn>
      <v-btn
        class="choice-button"
        :class="{ selected: modelValue === 'non-essential' }"
        :color="modelValue === 'non-essential' ? 'primary' : undefined"
        :variant="modelValue === 'non-essential' ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="$emit('select', 'non-essential')"
      >
        {{ t('transaction.nonEssential') }}
      </v-btn>
      <v-btn
        v-if="optional"
        class="choice-button"
        variant="outlined"
        color="secondary"
        size="large"
        rounded="lg"
        block
        @click="$emit('disable')"
      >
        {{ t('transaction.closeStep') }}
      </v-btn>
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
