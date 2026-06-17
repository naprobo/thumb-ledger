import type { Ledger } from '@/api/ledgers'
import type { Necessity } from '@/api/transactions'

export type WizardStepId = 'amount' | 'category' | 'item' | 'necessity' | 'subject'

export interface WizardDraft {
  amount: number | null
  currencyCode: string
  transactionDate: string
  category: string
  itemName: string
  necessity: Necessity | null
  subjectName: string
  subjectIds: string[]
  note: string
}

export function buildWizardSteps(ledger: Ledger): WizardStepId[] {
  const steps: WizardStepId[] = ['amount']
  if (ledger.entry_mode === 'item') {
    steps.push('category', 'item')
  } else {
    steps.push('item')
  }
  if (ledger.necessity_step_mode !== 'disabled') {
    steps.push('necessity')
  }
  if (ledger.subject_enabled && ledger.subject_step_mode !== 'disabled') {
    steps.push('subject')
  }
  return steps
}
