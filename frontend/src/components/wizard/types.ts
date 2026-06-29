import type { Ledger } from '@/api/ledgers'
import type { Necessity } from '@/api/transactions'

export type WizardStepId = 'amount' | 'category' | 'item' | 'location' | 'necessity' | 'subject'

export interface WizardDraft {
  amount: number | null
  currencyCode: string
  transactionDate: string
  category: string
  itemName: string
  locationName: string
  necessity: Necessity | null
  subjectName: string
  subjectIds: string[]
  note: string
}

export function buildWizardSteps(ledger: Ledger): WizardStepId[] {
  const steps: WizardStepId[] = ['amount', 'category']
  if (ledger.entry_mode === 'item' || ledger.receipt_item_enabled) {
    steps.push('item')
  }
  if (ledger.location_step_mode !== 'disabled') {
    steps.push('location')
  }
  if (ledger.necessity_step_mode !== 'disabled') {
    steps.push('necessity')
  }
  if (ledger.subject_enabled && ledger.subject_step_mode !== 'disabled') {
    steps.push('subject')
  }
  return steps
}
