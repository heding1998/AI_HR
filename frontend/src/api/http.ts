import { clearToken, getToken } from './auth'

async function parseResponse<T>(resp: Response): Promise<T> {
  if (resp.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('登录已过期，请重新登录')
  }
  if (!resp.ok) {
    const data = (await resp.json().catch(() => null)) as { detail?: string } | null
    throw new Error(data?.detail ?? '请求失败')
  }
  return resp.json() as Promise<T>
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const resp = await fetch(path, { ...options, headers })
  return parseResponse<T>(resp)
}

export async function upload<T>(path: string, form: FormData): Promise<T> {
  const token = getToken()
  const headers = new Headers()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const resp = await fetch(path, { method: 'POST', headers, body: form })
  return parseResponse<T>(resp)
}
