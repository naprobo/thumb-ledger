<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.subject') }}</h2>
    <div v-if="frequentSubjects.length" class="chip-grid">
      <v-btn
        v-for="subject in frequentSubjects"
        :key="subject.id"
        class="choice-button subject-chip"
        :class="{ selected: modelValue.includes(subject.id) }"
        :color="modelValue.includes(subject.id) ? 'primary' : undefined"
        :variant="modelValue.includes(subject.id) ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="deleteMode ? $emit('remove', subject) : $emit('toggle', subject)"
      >
        {{ translateLabel(subject.name, t) }}
        <span v-if="deleteMode" class="delete-overlay" aria-hidden="true">
          <Trash2 :size="24" />
        </span>
      </v-btn>
    </div>
    <v-btn class="primary-button subject-confirm" color="success" size="large" rounded="lg" :disabled="!optional && modelValue.length === 0" @click="$emit('confirm')">
      OK
    </v-btn>
    <div class="chip-grid">
      <v-btn
        v-for="subject in secondarySubjects"
        :key="subject.id"
        class="choice-button subject-chip"
        :class="{ selected: modelValue.includes(subject.id) }"
        :color="modelValue.includes(subject.id) ? 'primary' : undefined"
        :variant="modelValue.includes(subject.id) ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="deleteMode ? $emit('remove', subject) : $emit('toggle', subject)"
      >
        {{ translateLabel(subject.name, t) }}
        <span v-if="deleteMode" class="delete-overlay" aria-hidden="true">
          <Trash2 :size="24" />
        </span>
      </v-btn>
      <v-btn
        v-if="!deleteMode"
        class="choice-button add-chip"
        :disabled="customLimitReached"
        :class="{ selected: isCustomOpen }"
        :color="isCustomOpen ? 'primary' : undefined"
        :variant="isCustomOpen ? 'tonal' : 'outlined'"
        size="large"
        rounded="lg"
        block
        @click="openCustom"
      >
        <Plus :size="20" aria-hidden="true" />
        <span>{{ t('transaction.customSubject') }}</span>
      </v-btn>
    </div>
    <div v-if="isCustomOpen && !deleteMode" class="custom-subject-field">
      <v-text-field
        ref="customInput"
        v-model.trim="customValue"
        class="custom-input"
        :label="t('transaction.subject')"
        maxlength="50"
        :placeholder="t('transaction.customSubjectPlaceholder')"
        variant="outlined"
        density="comfortable"
        hide-details
        @keyup.enter="confirmCustom"
      />
      <v-btn class="primary-button" color="success" size="large" rounded="lg" :disabled="!customValue || customLimitReached" @click="confirmCustom">
        OK
      </v-btn>
    </div>
    <v-btn v-if="optional" class="ghost-button" variant="text" size="large" @click="$emit('skipForever')">
      {{ t('transaction.skipDontAsk') }}
    </v-btn>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Trash2 } from '@lucide/vue'
import type { Subject } from '@/api/preferences'
import { translateLabel } from '@/i18n/labels'

export interface SubjectChoice extends Subject {
  selection_count?: number
  last_selected_at?: string | null
}

const RECENT_USAGE_DAYS = 180

const props = defineProps<{ subjects: SubjectChoice[]; modelValue: string[]; optional: boolean; deleteMode: boolean; customLimitReached: boolean }>()
const emit = defineEmits<{ toggle: [subject: Subject]; confirm: []; create: [name: string]; remove: [subject: Subject]; skipForever: [] }>()
const { t } = useI18n()
const isCustomOpen = ref(false)
const customValue = ref('')
const customInput = ref<{ focus: () => void } | null>(null)

const frequentSubjects = computed(() => props.subjects.filter(isFrequentlyUsed))
const secondarySubjects = computed(() => {
  if (!frequentSubjects.value.length) return props.subjects
  return props.subjects.filter((subject) => !isFrequentlyUsed(subject))
})

function isFrequentlyUsed(subject: SubjectChoice): boolean {
  if (!subject.selection_count || !subject.last_selected_at) return false
  const lastSelectedAt = new Date(subject.last_selected_at).getTime()
  if (Number.isNaN(lastSelectedAt)) return false
  const recentThreshold = Date.now() - RECENT_USAGE_DAYS * 24 * 60 * 60 * 1000
  return lastSelectedAt >= recentThreshold
}

async function openCustom() {
  if (props.customLimitReached) return
  isCustomOpen.value = true
  await nextTick()
  customInput.value?.focus()
}

function confirmCustom() {
  if (!customValue.value || props.customLimitReached) return
  emit('create', customValue.value)
  customValue.value = ''
  isCustomOpen.value = false
}
</script>

<style scoped>
.subject-confirm {
  min-height: 76px;
  font-size: 1.05rem;
  font-weight: 800;
  text-transform: none;
}

.subject-chip {
  position: relative;
  overflow: hidden;
}

.delete-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgb(127 29 29 / 72%);
  color: #fff;
}

.add-chip {
  border-style: dashed;
}

.add-chip :deep(.v-btn__content) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.custom-subject-field {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 88px;
  align-items: center;
  gap: 10px;
}

.custom-subject-field .primary-button {
  min-width: 88px;
}
</style>
