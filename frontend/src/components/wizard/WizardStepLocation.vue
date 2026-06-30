<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.location') }}</h2>
    <v-btn v-if="optional && !managementMode" class="skip-button" color="warning" variant="tonal" size="large" block @click="$emit('skip')">
      <AlertTriangle :size="20" aria-hidden="true" />
      <span>{{ t('transaction.skip') }}</span>
    </v-btn>
    <div class="chip-grid">
      <v-btn
        v-for="location in locations"
        :key="location.id || location.value"
        class="choice-button"
        :class="{ selected: location.value === modelValue, 'managed-chip': managementMode }"
        :color="location.value === modelValue ? 'primary' : undefined"
        :variant="location.value === modelValue ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="managementMode ? $emit('manage', location) : $emit('select', location)"
      >
        {{ location.value }}
        <span v-if="managementMode" class="manage-overlay" aria-hidden="true">
          <Pencil v-if="managementMode === 'edit'" :size="24" />
          <Trash2 v-else :size="24" />
        </span>
      </v-btn>
      <v-btn
        v-if="!managementMode"
        class="choice-button add-chip"
        :class="{ selected: isAddOpen }"
        :color="isAddOpen ? 'primary' : undefined"
        :variant="isAddOpen ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="openAdd"
      >
        <Plus :size="20" aria-hidden="true" />
        <span>{{ t('transaction.addLocation') }}</span>
      </v-btn>
    </div>
    <div v-if="isAddOpen" class="location-field">
      <v-text-field
        ref="locationInput"
        v-model.trim="locationValue"
        :label="t('transaction.location')"
        maxlength="100"
        :placeholder="t('transaction.locationPlaceholder')"
        variant="outlined"
        density="comfortable"
        hide-details
        @keyup.enter="confirmAdd"
      />
      <v-btn color="success" size="large" rounded="lg" :disabled="!locationValue" @click="confirmAdd">
        OK
      </v-btn>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { AlertTriangle, Pencil, Plus, Trash2 } from '@lucide/vue'
import type { TagChoice } from '@/api/preferences'
import type { TagManagementMode } from '@/components/wizard/types'

withDefaults(defineProps<{ locations: TagChoice[]; modelValue: string; optional?: boolean; managementMode: TagManagementMode }>(), {
  optional: true,
})
const emit = defineEmits<{ select: [location: TagChoice]; add: [location: string]; manage: [location: TagChoice]; skip: [] }>()
const { t } = useI18n()
const isAddOpen = ref(false)
const locationValue = ref('')
const locationInput = ref<{ focus: () => void } | null>(null)

async function openAdd() {
  isAddOpen.value = true
  await nextTick()
  locationInput.value?.focus()
}

function confirmAdd() {
  const value = locationValue.value.trim()
  if (!value) return
  emit('add', value)
  locationValue.value = ''
  isAddOpen.value = false
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

.location-field {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 88px;
  align-items: center;
  gap: 10px;
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
