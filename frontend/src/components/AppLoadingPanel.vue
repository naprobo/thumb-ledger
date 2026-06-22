<template>
  <section class="loading-panel" role="status" aria-live="polite">
    <v-progress-circular indeterminate color="primary" :size="size" />
    <span>{{ label || t('app.loading') }}</span>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

withDefaults(defineProps<{
  label?: string
  size?: number
}>(), {
  label: '',
  size: 32,
})

const { t } = useI18n()
</script>

<style scoped>
.loading-panel {
  display: grid;
  min-height: 220px;
  place-items: center;
  align-content: center;
  gap: 12px;
  color: #607086;
  font-weight: 700;
}
</style>
