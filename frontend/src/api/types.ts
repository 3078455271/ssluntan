export interface UserPublic {
  id: number
  username: string
  avatar_url: string | null
  bio: string | null
  role: 'member' | 'moderator' | 'admin'
  created_at: string
}

export interface UserPrivate extends UserPublic {
  email: string
  is_active: boolean
}

export interface BoardBrief {
  id: number
  name: string
  slug: string
}

export interface BoardRead extends BoardBrief {
  description: string
  sort_order: number
  is_active: boolean
  topic_count: number
}

export interface TopicRead {
  id: number
  title: string
  board: BoardBrief
  author: UserPublic
  is_pinned: boolean
  is_locked: boolean
  views: number
  reply_count: number
  last_reply_at: string | null
  created_at: string
}

export interface PostRead {
  id: number
  topic_id: number
  author: UserPublic
  content: string
  floor: number
  is_op: boolean
  created_at: string
  updated_at: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface TokenWithUser {
  access_token: string
  token_type: string
  expires_in: number
  user: UserPrivate
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export interface ProfileUpdate {
  avatar_url?: string | null
  bio?: string | null
}

export interface TopicCreatePayload {
  board_id: number
  title: string
  content: string
}

export type TopicSort = 'latest' | 'hot' | 'new'

export interface TopicQuery {
  board_id?: number
  q?: string
  sort?: TopicSort
  page?: number
  page_size?: number
}

export interface BoardCreatePayload {
  name: string
  slug: string
  description?: string
  sort_order?: number
}

export interface BoardUpdatePayload {
  name?: string
  slug?: string
  description?: string
  sort_order?: number
  is_active?: boolean
}

export interface TopicUpdatePayload {
  title?: string
  is_pinned?: boolean
  is_locked?: boolean
}

export type SearchSort = 'relevance' | 'latest'

export interface SearchMatch {
  matched_in: 'title' | 'content'
  post_id: number | null
  floor: number | null
  snippet: string | null
}

export interface SearchHit {
  topic: TopicRead
  match: SearchMatch
}

export interface SearchQuery {
  q: string
  board_id?: number
  sort?: SearchSort
  page?: number
  page_size?: number
}
