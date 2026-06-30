<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.category') }}</h2>
    <div class="chip-grid">
      <v-btn
        v-for="category in categories"
        :key="category.id"
        class="choice-button"
        :class="{ selected: category.name === modelValue, 'managed-chip': managementMode && !category.is_system }"
        :color="category.name === modelValue ? 'primary' : undefined"
        :variant="category.name === modelValue ? 'tonal' : 'outlined'"
        :disabled="managementMode !== null && category.is_system"
        size="large"
        rounded="lg"
        block
        @click="managementMode ? $emit('manage', category) : $emit('select', category.name)"
      >
        {{ translateLabel(category.name, t) }}
        <span v-if="managementMode && !category.is_system" class="manage-overlay" aria-hidden="true">
          <Pencil v-if="managementMode === 'edit'" :size="24" />
          <Trash2 v-else :size="24" />
        </span>
      </v-btn>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Pencil, Trash2 } from '@lucide/vue'
import type { Category } from '@/api/ledgers'
import { translateLabel } from '@/i18n/labels'
import type { TagManagementMode } from '@/components/wizard/types'

defineProps<{ categories: Category[]; modelValue: string; managementMode: TagManagementMode }>()
defineEmits<{ select: [category: string]; manage: [category: Category] }>()
const { t } = useI18n()
</script>

<style scoped>
.managed-chip {
  position: relative;
  overflow: hidden;
}

.manage-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgb(30 41 59 / 72%);
  color: #fff;
}
</style>
