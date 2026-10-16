export interface LoginResponse {
  access_token: string
  token_type: string
}

const TOKEN_KEY = 'aihr_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const resp = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!resp.ok) {
    const data = await resp.json().catch(() => null)
    throw new Error(data?.detail ?? '登录失败')
  }
  return resp.json()
}
