<template>
  <section class="wizard-step">
    <h2>{{ t('transaction.subject') }}</h2>
    <div v-if="frequentSubjects.length" class="chip-grid">
      <button
        v-for="subject in frequentSubjects"
        :key="subject.id"
        type="button"
        class="subject-chip"
        :class="{ selected: modelValue.includes(subject.id) }"
        @click="deleteMode ? $emit('remove', subject) : $emit('toggle', subject)"
      >
        {{ translateLabel(subject.name, t) }}
        <span v-if="deleteMode" class="delete-overlay" aria-hidden="true">
          <Trash2 :size="24" />
        </span>
      </button>
    </div>
    <button type="button" class="primary-button subject-confirm" :disabled="!optional && modelValue.length === 0" @click="$emit('confirm')">
      OK
    </button>
    <div class="chip-grid">
      <button
        v-for="subject in secondarySubjects"
        :key="subject.id"
        type="button"
        class="subject-chip"
        :class="{ selected: modelValue.includes(subject.id) }"
        @click="deleteMode ? $emit('remove', subject) : $emit('toggle', subject)"
      >
        {{ translateLabel(subject.name, t) }}
        <span v-if="deleteMode" class="delete-overlay" aria-hidden="true">
          <Trash2 :size="24" />
        </span>
      </button>
      <button v-if="!deleteMode" type="button" class="add-chip" :disabled="customLimitReached" :class="{ selected: isCustomOpen }" @click="openCustom">
        <Plus :size="20" aria-hidden="true" />
        <span>{{ t('transaction.customSubject') }}</span>
      </button>
    </div>
    <label v-if="isCustomOpen && !deleteMode" class="custom-subject-field">
      <span>{{ t('transaction.subject') }}</span>
      <input
        ref="customInput"
        v-model.trim="customValue"
        maxlength="50"
        :placeholder="t('transaction.customSubjectPlaceholder')"
        @keyup.enter="confirmCustom"
      />
      <button type="button" class="primary-button" :disabled="!customValue || customLimitReached" @click="confirmCustom">
        OK
      </button>
    </label>
    <button v-if="optional" type="button" class="ghost-button" @click="$emit('skipForever')">
      {{ t('transaction.skipDontAsk') }}
    </button>
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
const customInput = ref<HTMLInputElement | null>(null)

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
  min-height: 72px;
  font-size: 1.05rem;
  font-weight: 800;
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
  display: inline-grid;
  grid-auto-flow: column;
  place-content: center;
  align-items: center;
  gap: 8px;
  border-style: dashed;
}

.custom-subject-field {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 88px;
  gap: 8px;
}

.custom-subject-field span {
  grid-column: 1 / -1;
}

.custom-subject-field .primary-button {
  min-width: 88px;
}
</style>
