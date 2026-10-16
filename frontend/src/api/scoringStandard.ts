import { request } from './http'

export interface StandardARow {
  id?: number
  category: string
  subcategory: string
  category_score: number
  subcategory_score: number
}

export interface StandardBRow {
  id?: number
  category: string
  subcategory: string
  level1_indicator: string
  level2_indicator: string
  weight: number
}

export interface ScoringStandard {
  a: StandardARow[]
  b: StandardBRow[]
}

export function getScoringStandard(jobId: number): Promise<ScoringStandard> {
  return request<ScoringStandard>(`/api/jobs/${jobId}/scoring-standard`)
}

export function saveStandardA(jobId: number, rows: StandardARow[]): Promise<StandardARow[]> {
  return request<StandardARow[]>(`/api/jobs/${jobId}/scoring-standard/a`, {
    method: 'PUT',
    body: JSON.stringify(rows),
  })
}

export function saveStandardB(jobId: number, rows: StandardBRow[]): Promise<StandardBRow[]> {
  return request<StandardBRow[]>(`/api/jobs/${jobId}/scoring-standard/b`, {
    method: 'PUT',
    body: JSON.stringify(rows),
  })
}
