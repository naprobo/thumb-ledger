<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.location') }}</h2>
    <v-btn v-if="optional" class="skip-button" color="warning" variant="tonal" size="large" block @click="$emit('skip')">
      <AlertTriangle :size="20" aria-hidden="true" />
      <span>{{ t('transaction.skip') }}</span>
    </v-btn>
    <div class="chip-grid">
      <v-btn
        v-for="location in locations"
        :key="location"
        class="choice-button"
        :class="{ selected: location === modelValue }"
        :color="location === modelValue ? 'primary' : undefined"
        :variant="location === modelValue ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="$emit('select', location)"
      >
        {{ location }}
      </v-btn>
      <v-btn
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
import { AlertTriangle, Plus } from '@lucide/vue'

withDefaults(defineProps<{ locations: string[]; modelValue: string; optional?: boolean }>(), {
  optional: true,
})
const emit = defineEmits<{ select: [location: string]; add: [location: string]; skip: [] }>()
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
</style>
