/** 统一 API 客户端：token 注入、错误处理、SSE、WebSocket。 */

const TOKEN_KEY = 'qinghe.token'

export function getToken(): string {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch {
    return ''
  }
}

export function setToken(token: string): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* 隐私模式忽略 */
  }
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function request<T = any>(
  path: string,
  options: { method?: string; body?: unknown; auth?: boolean } = {},
): Promise<T> {
  const { method = 'GET', body, auth = true } = options
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth) {
    const token = getToken()
    if (token) headers.Authorization = 'Bearer ' + token
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  let data: any = null
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const detail = data?.detail || data?.error || `请求失败（${response.status}）`
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), response.status)
  }
  return data as T
}

/** SSE 流式对话（可携带多轮上下文）。 */
export async function streamChat(
  message: string,
  handlers: {
    onMeta?: (meta: any) => void
    onDelta?: (text: string) => void
    onDone?: () => void
    onError?: (error: Error) => void
  },
  history: { role: string; content: string }[] = [],
): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }
  const token = getToken()
  if (token) headers.Authorization = 'Bearer ' + token

  let response: Response
  try {
    response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers,
      body: JSON.stringify({ message, history }),
    })
  } catch {
    handlers.onError?.(new Error('网络连接失败，请确认后端已启动'))
    return
  }

  if (!response.ok || !response.body) {
    let detail = 'AI 服务暂时不可用'
    try {
      const data = await response.json()
      detail = data?.detail || detail
    } catch {
      /* ignore */
    }
    handlers.onError?.(new Error(detail))
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatch = (raw: string) => {
    const lines = raw.split('\n')
    let event = 'message'
    const dataLines: string[] = []
    for (const line of lines) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
    }
    if (!dataLines.length) return
    let payload: any
    try {
      payload = JSON.parse(dataLines.join('\n'))
    } catch {
      return
    }
    if (event === 'meta') handlers.onMeta?.(payload)
    else if (event === 'delta') handlers.onDelta?.(payload.text || '')
    else if (event === 'done') handlers.onDone?.()
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let index = buffer.indexOf('\n\n')
      while (index >= 0) {
        const raw = buffer.slice(0, index)
        buffer = buffer.slice(index + 2)
        if (raw.trim()) dispatch(raw)
        index = buffer.indexOf('\n\n')
      }
    }
    if (buffer.trim()) dispatch(buffer)
  } catch (error: any) {
    handlers.onError?.(new Error('AI 回答中断：' + (error?.message || '未知错误')))
  }
}

/** WebSocket 地址（带 token）。 */
export function websocketUrl(): string {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${location.host}/ws?token=${encodeURIComponent(getToken())}`
}
