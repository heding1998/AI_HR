import { request } from './http'

export interface TalentPoolEntry {
  id: number
  name: string
  contact: string
  score: number
  tier: string
  resume_id: number | null
  created_at: string
}

export function listTalentPool(tier?: string): Promise<TalentPoolEntry[]> {
  const params = tier ? `?tier=${encodeURIComponent(tier)}` : ''
  return request<TalentPoolEntry[]>(`/api/talent-pool${params}`)
}
