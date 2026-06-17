import { apiClient } from '@/api'

export type SuggestionStatus = 'new' | 'reviewing' | 'planned' | 'completed' | 'declined'
export type SuggestionVoteType = 'support' | 'oppose'

export interface Suggestion {
  id: string
  author_id: string
  title: string
  body: string
  is_public: boolean
  status: SuggestionStatus
  support_count: number
  oppose_count: number
  my_vote: SuggestionVoteType | null
  created_at: string
  updated_at: string
}

export interface SuggestionCreatePayload {
  title: string
  body: string
  is_public: boolean
}

export async function createSuggestion(payload: SuggestionCreatePayload): Promise<Suggestion> {
  const response = await apiClient.post<Suggestion>('/suggestions', payload)
  return response.data
}

export async function listMySuggestions(): Promise<Suggestion[]> {
  const response = await apiClient.get<Suggestion[]>('/suggestions/mine')
  return response.data
}

export async function listPublicSuggestions(): Promise<Suggestion[]> {
  const response = await apiClient.get<Suggestion[]>('/suggestions/public')
  return response.data
}

export async function voteSuggestion(suggestionId: string, voteType: SuggestionVoteType): Promise<Suggestion> {
  const response = await apiClient.post<Suggestion>(`/suggestions/${suggestionId}/vote`, {
    vote_type: voteType,
  })
  return response.data
}
