// Gọi API admin bằng cookie, mọi request kèm credentials.
// Gặp 401 thì thử refresh một lần, thất bại thì thôi để UI về login.

const API = 'http://127.0.0.1:8000'

export async function apiText(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${API}${path}`, { ...init, credentials: 'include' })
  if (res.status !== 401) return res
  const refresh = await fetch(`${API}/admin/auth/refresh`, { method: 'POST', credentials: 'include' })
  if (!refresh.ok) return res
  return fetch(`${API}${path}`, { ...init, credentials: 'include' })
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await apiText(path, init)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}
