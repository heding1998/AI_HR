import { request } from './http'

export interface Job {
  id: number
  code: string
  name: string
  location: string
  is_active: boolean
}

export interface JobCreate {
  code: string
  name: string
  location: string
}

export interface JobUpdate {
  name?: string
  location?: string
  is_active?: boolean
}

export function listJobs(): Promise<Job[]> {
  return request<Job[]>('/api/jobs')
}

export function createJob(data: JobCreate): Promise<Job> {
  return request<Job>('/api/jobs', { method: 'POST', body: JSON.stringify(data) })
}

export function updateJob(id: number, data: JobUpdate): Promise<Job> {
  return request<Job>(`/api/jobs/${id}`, { method: 'PUT', body: JSON.stringify(data) })
}
