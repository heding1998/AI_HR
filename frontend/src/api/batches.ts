import { request, upload } from './http'

export interface Batch {
  id: number
  job_id: number
  status: string
  total_count: number
  processed_count: number
  error: string | null
  created_at: string
}

export interface Resume {
  id: number
  batch_id: number
  job_id: number
  original_filename: string
  status: string
  error: string | null
  created_at: string
  extracted_content: Record<string, unknown> | null
}

export interface ResumeDetail extends Resume {
  extracted_text: string
}

export interface BatchDetail extends Batch {
  resumes: Resume[]
}

export function listBatches(): Promise<Batch[]> {
  return request<Batch[]>('/api/batches')
}

export function getBatch(id: number): Promise<BatchDetail> {
  return request<BatchDetail>(`/api/batches/${id}`)
}

export function getResume(id: number): Promise<ResumeDetail> {
  return request<ResumeDetail>(`/api/resumes/${id}`)
}

export function uploadBatch(jobId: number, file: File): Promise<Batch> {
  const form = new FormData()
  form.append('job_id', String(jobId))
  form.append('file', file)
  return upload<Batch>('/api/batches', form)
}
