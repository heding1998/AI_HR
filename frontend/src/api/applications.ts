import { request } from './http'

export interface Application {
  id: number
  job_id: number
  resume_id: number
  candidate_name: string
  candidate_contact: string
  score: number
  status: string
  created_at: string
}

export function listApplications(jobId?: number): Promise<Application[]> {
  const params = jobId != null ? `?job_id=${jobId}` : ''
  return request<Application[]>(`/api/applications${params}`)
}
