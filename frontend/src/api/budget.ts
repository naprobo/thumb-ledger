import { apiClient } from '@/api'

export interface BudgetProgress {
  monthly_spent: number
  monthly_total: number
  percentage: number
  warning: 'soft' | 'over' | null
  category_spending: Record<string, number>
}

export interface Budget {
  id: string
  ledger_id: string
  monthly_total: number
  annual_total: number | null
  is_enabled: boolean
  progress: BudgetProgress
}

export interface BudgetCategoryPayload {
  category: string
  amount: number
}

export interface BudgetUpsertPayload {
  monthly_total: number
  annual_total?: number
  categories?: BudgetCategoryPayload[]
}

export async function saveBudget(ledgerId: string, payload: BudgetUpsertPayload): Promise<Budget> {
  const response = await apiClient.post<Budget>(`/ledgers/${ledgerId}/budget`, payload)
  return response.data
}

export async function getBudget(ledgerId: string): Promise<Budget | null> {
  try {
    const response = await apiClient.get<Budget>(`/ledgers/${ledgerId}/budget`)
    return response.data
  } catch (error: any) {
    if (error.response?.status === 404) return null
    throw error
  }
}
