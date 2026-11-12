/** 业务 API 封装。 */
import { request } from './client'

export interface User {
  id: number
  username: string
  nickname: string
  avatar: string
  color: string
  major: string
  grade: string
  bio: string
  tags: string[]
  is_admin: boolean
  created_at: string
}

export interface Post {
  id: number
  title: string
  content: string
  category: string
  category_name: string
  category_icon: string
  tags: string[]
  author: User
  views: number
  like_count: number
  comment_count: number
  liked: boolean
  heat: number
  summary: string
  created_at: string
}

export interface Comment {
  id: number
  content: string
  author: User
  created_at: string
}

export interface Meta {
  app: { name: string; subtitle: string; version: string }
  categories: { id: string; name: string; icon: string; color: string }[]
  ai: { mode: string; provider: string; model: string }
  demo_account: { username: string; password: string }
  stats: Stats
  database: string
}

export interface Stats {
  users: number
  posts: number
  comments: number
  ai_calls: number
  posts_today: number
  active_users: number
  categories: { id: string; name: string; icon: string; color: string; count: number }[]
}

export const api = {
  meta: () => request<Meta>('/api/meta', { auth: false }),
  stats: () => request<Stats>('/api/stats', { auth: false }),

  login: (username: string, password: string) =>
    request<{ token: string; user: User }>('/api/auth/login', {
      method: 'POST',
      body: { username, password },
      auth: false,
    }),
  register: (payload: { username: string; password: string; nickname?: string }) =>
    request<{ token: string; user: User }>('/api/auth/register', {
      method: 'POST',
      body: payload,
      auth: false,
    }),
  me: () => request<User>('/api/auth/me'),
  updateMe: (payload: Partial<User> & { tags?: string[] }) =>
    request<User>('/api/users/me', { method: 'PUT', body: payload }),

  users: () => request<User[]>('/api/users', { auth: false }),
  user: (id: number) => request<{ user: User; posts: Post[] }>(`/api/users/${id}`),

  posts: (params: Record<string, string | number> = {}) => {
    const search = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== '' && value !== undefined && value !== null) search.set(key, String(value))
    })
    const query = search.toString()
    return request<{ total: number; items: Post[] }>('/api/posts' + (query ? '?' + query : ''), {
      auth: false,
    })
  },
  post: (id: number) =>
    request<{ post: Post; comments: Comment[]; related: Post[] }>(`/api/posts/${id}`),
  createPost: (payload: { title: string; content: string; category: string; tags: string[] }) =>
    request<Post>('/api/posts', { method: 'POST', body: payload }),
  like: (id: number) =>
    request<{ liked: boolean; like_count: number }>(`/api/posts/${id}/like`, { method: 'POST' }),
  comments: (id: number) => request<Comment[]>(`/api/posts/${id}/comments`, { auth: false }),
  addComment: (id: number, content: string) =>
    request<Comment>(`/api/posts/${id}/comments`, { method: 'POST', body: { content } }),

  aiWrite: (text: string) =>
    request<{
      title: string
      content: string
      category: string
      category_name: string
      category_confidence: number
      tags: string[]
      summary: string
      issues: string[]
      tips: string[]
      safety: { safe: boolean; hits: string[]; message: string }
      changed: boolean
      mode: string
    }>('/api/ai/write', { method: 'POST', body: { text } }),
  aiMatch: () =>
    request<{ matches: { user: User; score: number; reason: string }[]; message: string; mode: string }>(
      '/api/ai/match',
      { method: 'POST', body: {} },
    ),
  aiLogs: () =>
    request<{ id: number; kind: string; input: string; mode: string; chars: number }[]>('/api/ai/logs'),

  conversations: () =>
    request<{ user: User; last_message: string; last_at: string; unread: number; online: boolean }[]>(
      '/api/messages/conversations',
    ),
  messages: (peerId: number) =>
    request<{ id: number; sender_id: number; receiver_id: number; content: string; is_read: boolean; created_at: string }[]>(
      `/api/messages/${peerId}`,
    ),
  sendMessage: (peerId: number, content: string) =>
    request<{ id: number; sender_id: number; receiver_id: number; content: string; created_at: string }>(
      `/api/messages/${peerId}`,
      { method: 'POST', body: { content } },
    ),

  adminOverview: () =>
    request<{
      totals: { users: number; posts: number; comments: number; ai_calls: number }
      recent_posts: Post[]
      top_users: (User & { post_count: number })[]
    }>('/api/admin/overview'),
  adminUsers: () => request<(User & { post_count: number })[]>('/api/admin/users'),
  adminDeletePost: (id: number) => request<{ ok: boolean }>(`/api/admin/posts/${id}`, { method: 'DELETE' }),
  adminToggleAdmin: (id: number) =>
    request<{ id: number; is_admin: boolean }>(`/api/admin/users/${id}/toggle-admin`, { method: 'POST' }),
}
