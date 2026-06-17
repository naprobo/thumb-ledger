import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createLedger,
  deleteLedger,
  getLedger,
  listLedgers,
  updateLedger,
  type Ledger,
  type LedgerCreatePayload,
  type LedgerUpdatePayload,
} from '@/api/ledgers'

export const useLedgerStore = defineStore('ledgers', () => {
  const ledgers = ref<Ledger[]>([])
  const activeLedger = ref<Ledger | null>(null)
  const isLoading = ref(false)

  const canCreateLedger = computed(() => ledgers.value.length < 10)

  async function fetchLedgers(): Promise<void> {
    isLoading.value = true
    try {
      ledgers.value = await listLedgers()
    } finally {
      isLoading.value = false
    }
  }

  async function fetchLedger(ledgerId: string): Promise<Ledger> {
    activeLedger.value = await getLedger(ledgerId)
    return activeLedger.value
  }

  async function addLedger(payload: LedgerCreatePayload): Promise<Ledger> {
    const ledger = await createLedger(payload)
    ledgers.value = [ledger, ...ledgers.value]
    activeLedger.value = ledger
    return ledger
  }

  async function saveLedger(ledgerId: string, payload: LedgerUpdatePayload): Promise<Ledger> {
    const ledger = await updateLedger(ledgerId, payload)
    activeLedger.value = ledger
    ledgers.value = ledgers.value.map((item) => (item.id === ledger.id ? ledger : item))
    return ledger
  }

  async function removeLedger(ledgerId: string): Promise<void> {
    await deleteLedger(ledgerId)
    ledgers.value = ledgers.value.filter((ledger) => ledger.id !== ledgerId)
    if (activeLedger.value?.id === ledgerId) {
      activeLedger.value = null
    }
  }

  return {
    ledgers,
    activeLedger,
    isLoading,
    canCreateLedger,
    fetchLedgers,
    fetchLedger,
    addLedger,
    saveLedger,
    removeLedger,
  }
})

