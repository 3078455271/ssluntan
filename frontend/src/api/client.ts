import type {
  BoardCreatePayload,
  BoardRead,
  BoardUpdatePayload,
  Page,
  PostRead,
  ProfileUpdate,
  RegisterPayload,
  SearchHit,
  SearchQuery,
  TokenWithUser,
  TopicCreatePayload,
  TopicQuery,
  TopicRead,
  TopicUpdatePayload,
  UserPrivate,
  UserPublic,
} from '@/api/types'

export const TOKEN_KEY = 'ssluntan.access_token'

const API_BASE = (import.meta.env.VITE_API_BASE ?? '/api').replace(/\/+$/, '')

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

let unauthorizedHandler: (() => void) | null = null
let forbiddenHandler: ((message: string) => void) | null = null

/** Let the router react when the backend rejects an expired token. */
export function setUnauthorizedHandler(handler: () => void): void {
  unauthorizedHandler = handler
}

/** Let the UI surface a unified message for every 403 response. */
export function setForbiddenHandler(handler: (message: string) => void): void {
  forbiddenHandler = handler
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

interface ValidationIssue {
  loc?: (string | number)[]
  msg?: string
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === 'string' && payload.trim()) {
    return payload
  }
  if (!payload || typeof payload !== 'object') {
    return fallback
  }

  const data = payload as { detail?: unknown; message?: unknown }
  if (typeof data.detail === 'string') {
    return data.detail
  }
  if (Array.isArray(data.detail)) {
    const first = data.detail[0] as ValidationIssue | undefined
    if (first?.msg) {
      const location = (first.loc ?? []).filter((part) => part !== 'body').join('.')
      return location ? `${location}: ${first.msg}` : first.msg
    }
  }
  if (typeof data.message === 'string') {
    return data.message
  }
  return fallback
}

type JsonRequestInit = Omit<RequestInit, 'body'> & {
  body?: unknown
  /** Skip the global 401 redirect, e.g. when restoring a session in the background. */
  skipAuthRedirect?: boolean
}

async function request<T>(path: string, options: JsonRequestInit = {}): Promise<T> {
  const { body: rawBody, skipAuthRedirect = false, ...init } = options
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')

  const token = getToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let body = rawBody as BodyInit | null | undefined
  if (
    body &&
    typeof body === 'object' &&
    !(body instanceof FormData) &&
    !(body instanceof URLSearchParams) &&
    !(body instanceof Blob) &&
    !(body instanceof ArrayBuffer)
  ) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(body)
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, { ...init, headers, body })
  } catch {
    throw new ApiError('网络连接失败，请确认后端服务已启动', 0)
  }

  const text = await response.text()
  let payload: unknown = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = text
    }
  }

  // A 401 without a token means a bad username/password on the login form,
  // not an expired session: never clear or redirect in that case.
  if (response.status === 401 && token) {
    setToken(null)
    if (!skipAuthRedirect) unauthorizedHandler?.()
  }

  if (!response.ok) {
    const message = extractErrorMessage(payload, `请求失败（${response.status}）`)
    if (response.status === 403) forbiddenHandler?.(message)
    throw new ApiError(message, response.status)
  }
  return payload as T
}

function buildTopicQuery(params: TopicQuery): string {
  const search = new URLSearchParams()
  if (params.board_id != null) search.set('board_id', String(params.board_id))
  if (params.q) search.set('q', params.q)
  if (params.sort) search.set('sort', params.sort)
  search.set('page', String(params.page ?? 1))
  search.set('page_size', String(params.page_size ?? 20))
  return search.toString()
}

function buildSearchQuery(params: SearchQuery): string {
  const search = new URLSearchParams({ q: params.q })
  if (params.board_id != null) search.set('board_id', String(params.board_id))
  if (params.sort) search.set('sort', params.sort)
  search.set('page', String(params.page ?? 1))
  search.set('page_size', String(params.page_size ?? 20))
  return search.toString()
}

export const api = {
  health: () => request<{ status: string; app: string }>('/health'),

  getBoards: (options: { includeInactive?: boolean } = {}) =>
    request<BoardRead[]>(options.includeInactive ? '/boards?include_inactive=true' : '/boards'),
  getBoard: (slug: string) => request<BoardRead>(`/boards/${encodeURIComponent(slug)}`),
  createBoard: (payload: BoardCreatePayload) =>
    request<BoardRead>('/boards', { method: 'POST', body: payload }),
  updateBoard: (boardId: number, payload: BoardUpdatePayload) =>
    request<BoardRead>(`/boards/${boardId}`, { method: 'PATCH', body: payload }),

  getTopics: (params: TopicQuery = {}) => request<Page<TopicRead>>(`/topics?${buildTopicQuery(params)}`),
  getTopic: (topicId: number) => request<TopicRead>(`/topics/${topicId}`),
  searchTopics: (params: SearchQuery) =>
    request<Page<SearchHit>>(`/search?${buildSearchQuery(params)}`),
  createTopic: (payload: TopicCreatePayload) =>
    request<TopicRead>('/topics', { method: 'POST', body: payload }),
  updateTopic: (topicId: number, payload: TopicUpdatePayload) =>
    request<TopicRead>(`/topics/${topicId}`, { method: 'PATCH', body: payload }),
  deleteTopic: (topicId: number) => request<void>(`/topics/${topicId}`, { method: 'DELETE' }),

  getPosts: (topicId: number, page = 1, pageSize = 20) =>
    request<Page<PostRead>>(
      `/topics/${topicId}/posts?${new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      }).toString()}`,
    ),
  replyToTopic: (topicId: number, content: string) =>
    request<PostRead>(`/topics/${topicId}/posts`, { method: 'POST', body: { content } }),
  deletePost: (postId: number) => request<void>(`/posts/${postId}`, { method: 'DELETE' }),

  login: (username: string, password: string) =>
    request<TokenWithUser>('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({ username, password }),
    }),
  register: (payload: RegisterPayload) =>
    request<UserPrivate>('/auth/register', { method: 'POST', body: payload }),

  getMe: (options: { skipAuthRedirect?: boolean } = {}) =>
    request<UserPrivate>('/users/me', options),
  updateMe: (payload: ProfileUpdate) =>
    request<UserPrivate>('/users/me', { method: 'PATCH', body: payload }),
  getUser: (username: string) => request<UserPublic>(`/users/${encodeURIComponent(username)}`),
}
