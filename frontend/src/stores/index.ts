/** 轻量状态：登录态、主题、Toast。不引入 Pinia，保持依赖精简。 */
import { reactive } from 'vue'
import { api, type User } from '@/api'
import { getToken, setToken } from '@/api/client'

const THEME_KEY = 'qinghe.theme'

export const auth = reactive({
  user: null as User | null,
  token: getToken(),
  ready: false,
})

export const ui = reactive({
  theme: 'light' as 'light' | 'dark',
  toasts: [] as { id: number; message: string; type: 'ok' | 'err' }[],
  search: '',
  composerOpen: false,
  version: 0,
})

let toastSeq = 0

export function toast(message: string, type: 'ok' | 'err' = 'ok', duration = 2600): void {
  const id = ++toastSeq
  ui.toasts.push({ id, message, type })
  setTimeout(() => {
    const index = ui.toasts.findIndex((item) => item.id === id)
    if (index >= 0) ui.toasts.splice(index, 1)
  }, duration)
}

export function applyTheme(theme: 'light' | 'dark'): void {
  ui.theme = theme
  document.documentElement.classList.toggle('dark', theme === 'dark')
  localStorage.setItem(THEME_KEY, theme)
}

export function toggleTheme(): void {
  applyTheme(ui.theme === 'dark' ? 'light' : 'dark')
}

export async function bootstrap(): Promise<void> {
  const saved = localStorage.getItem(THEME_KEY)
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  applyTheme(saved === 'dark' || (!saved && prefersDark) ? 'dark' : 'light')

  if (getToken()) {
    try {
      auth.user = await api.me()
    } catch {
      setToken('')
      auth.token = ''
      auth.user = null
    }
  }
  auth.ready = true
}

export async function login(username: string, password: string): Promise<User> {
  const data = await api.login(username, password)
  setToken(data.token)
  auth.token = data.token
  auth.user = data.user
  return data.user
}

export async function register(payload: { username: string; password: string; nickname?: string }): Promise<User> {
  const data = await api.register(payload)
  setToken(data.token)
  auth.token = data.token
  auth.user = data.user
  return data.user
}

export function setUser(user: User): void {
  auth.user = user
}

export function logout(): void {
  setToken('')
  auth.token = ''
  auth.user = null
}
