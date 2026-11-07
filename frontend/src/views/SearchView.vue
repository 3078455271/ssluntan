<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api/client'
import type { BoardRead, Page, SearchHit, SearchSort } from '@/api/types'
import PaginationBar from '@/components/PaginationBar.vue'
import { formatDateTime } from '@/utils/format'

const PAGE_SIZE = 20

const route = useRoute()
const router = useRouter()

const boards = ref<BoardRead[]>([])
const pageData = ref<Page<SearchHit> | null>(null)
const loading = ref(false)
const error = ref('')
const formError = ref('')
let requestSeq = 0

const sortOptions: { value: SearchSort; label: string }[] = [
  { value: 'relevance', label: '标题优先' },
  { value: 'latest', label: '最新回复' },
]

const keyword = computed(() => (typeof route.query.q === 'string' ? route.query.q.trim() : ''))
const hasQuery = computed(() => keyword.value.length >= 2)
const tooShort = computed(() => keyword.value.length === 1)
const boardId = computed(() => {
  const raw = route.query.board
  const value = Number(Array.isArray(raw) ? raw[0] : raw)
  return Number.isInteger(value) && value > 0 ? value : null
})
const sort = computed<SearchSort>(() => (route.query.sort === 'latest' ? 'latest' : 'relevance'))
const page = computed(() => Math.max(1, Number(route.query.page) || 1))

const searchInput = ref(keyword.value)

async function loadBoards(): Promise<void> {
  try {
    boards.value = await api.getBoards()
  } catch {
    // Board filtering is optional; search results still work without it.
    boards.value = []
  }
}

async function loadResults(): Promise<void> {
  const current = ++requestSeq
  error.value = ''
  if (!hasQuery.value) {
    pageData.value = null
    loading.value = false
    return
  }

  loading.value = true
  // Drop the previous page so a new keyword never renders old snippets with the new highlight.
  pageData.value = null
  try {
    const result = await api.searchTopics({
      q: keyword.value,
      board_id: boardId.value ?? undefined,
      sort: sort.value,
      page: page.value,
      page_size: PAGE_SIZE,
    })
    if (current !== requestSeq) return
    pageData.value = result
  } catch (err) {
    if (current !== requestSeq) return
    error.value = err instanceof Error ? err.message : '搜索失败'
    pageData.value = null
  } finally {
    if (current === requestSeq) loading.value = false
  }
}

function submit(): void {
  formError.value = ''
  const value = searchInput.value.trim()
  if (value.length < 2) {
    formError.value = '请输入至少 2 个字符的关键词'
    return
  }

  void router.push({
    name: 'search',
    query: {
      q: value,
      ...(boardId.value ? { board: String(boardId.value) } : {}),
      ...(sort.value === 'latest' ? { sort: 'latest' } : {}),
    },
  })
}

function changeBoard(event: Event): void {
  const value = (event.target as HTMLSelectElement).value
  void router.push({
    name: 'search',
    query: { ...route.query, board: value || undefined, page: undefined },
  })
}

function changeSort(next: SearchSort): void {
  void router.push({
    name: 'search',
    query: { ...route.query, sort: next === 'relevance' ? undefined : next, page: undefined },
  })
}

function goPage(next: number): void {
  void router.push({
    name: 'search',
    query: { ...route.query, page: next > 1 ? String(next) : undefined },
  })
}

function clearFilters(): void {
  void router.push({ name: 'search', query: keyword.value ? { q: keyword.value } : {} })
}

function topicLink(hit: SearchHit) {
  const match = hit.match
  if (match.matched_in === 'content' && match.floor != null) {
    const targetPage = Math.ceil(match.floor / PAGE_SIZE)
    return {
      name: 'topic',
      params: { id: hit.topic.id },
      query: {
        ...(targetPage > 1 ? { page: String(targetPage) } : {}),
        ...(match.post_id != null ? { post: String(match.post_id) } : {}),
        floor: String(match.floor),
      },
    }
  }
  return { name: 'topic', params: { id: hit.topic.id } }
}

interface SnippetPart {
  text: string
  match: boolean
}

function snippetParts(snippet: string | null): SnippetPart[] {
  if (!snippet) return []
  const needle = keyword.value
  if (!needle) return [{ text: snippet, match: false }]

  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const pieces = snippet.split(new RegExp(`(${escaped})`, 'gi')).filter(Boolean)
  return pieces.map((text) => ({
    text,
    match: text.toLocaleLowerCase() === needle.toLocaleLowerCase(),
  }))
}

watch(keyword, (value) => {
  if (value !== searchInput.value.trim()) searchInput.value = value
})
watch([keyword, boardId, sort, page], () => void loadResults())

onMounted(async () => {
  await loadBoards()
  await loadResults()
})
</script>

<template>
  <div class="search-page">
    <nav class="breadcrumb">
      <RouterLink to="/">首页</RouterLink>
      <span>/</span>
      <span>搜索</span>
    </nav>

    <section class="search-hero">
      <p class="section-kicker">SEARCH</p>
      <h1>搜索社区</h1>
      <p class="search-lede">同时检索主题标题和每一层回复，正文命中的结果会直接带你跳到对应楼层。</p>

      <form class="search-query-form" role="search" @submit.prevent="submit">
        <input
          v-model="searchInput"
          type="search"
          placeholder="输入至少 2 个字符的关键词，例如「FastAPI」"
          aria-label="搜索关键词"
          maxlength="100"
        />
        <button type="submit" class="btn btn-primary">搜索</button>
      </form>
      <div v-if="formError" class="alert alert-error search-form-error">{{ formError }}</div>

      <div class="search-filters">
        <label class="search-filter">
          <span>版块</span>
          <select :value="boardId ?? ''" @change="changeBoard">
            <option value="">全部版块</option>
            <option v-for="board in boards" :key="board.id" :value="board.id">
              {{ board.name }}
            </option>
          </select>
        </label>

        <div class="tabs search-sort-tabs">
          <button
            v-for="item in sortOptions"
            :key="item.value"
            type="button"
            class="tab"
            :class="{ active: sort === item.value }"
            @click="changeSort(item.value)"
          >
            {{ item.label }}
          </button>
        </div>

        <button
          v-if="boardId || sort !== 'relevance'"
          type="button"
          class="link-button"
          @click="clearFilters"
        >
          清除筛选
        </button>
      </div>
    </section>

    <section v-if="!hasQuery" class="section">
      <div class="empty-state">
        <strong>{{ tooShort ? '关键词太短' : '输入关键词开始搜索' }}</strong>
        <p>
          {{
            tooShort
              ? '至少需要 2 个字符，才能同时检索标题和楼层内容。'
              : '结果按标题命中优先排序，正文命中会附带上下文片段。'
          }}
        </p>
        <RouterLink to="/" class="btn btn-ghost btn-sm">返回首页</RouterLink>
      </div>
    </section>

    <section v-else class="section">
      <div class="section-head">
        <div>
          <p class="section-kicker">RESULTS</p>
          <h2>「{{ keyword }}」的搜索结果</h2>
        </div>
        <span class="section-note">
          <template v-if="loading">正在检索…</template>
          <template v-else-if="pageData">共 {{ pageData.total }} 个主题</template>
        </span>
      </div>

      <div v-if="error" class="alert alert-error">
        {{ error }}
        <button type="button" class="btn btn-ghost btn-sm" @click="loadResults">重试</button>
      </div>

      <div v-else-if="loading && !pageData" class="skeleton-block">正在搜索…</div>

      <div v-else-if="pageData && pageData.items.length === 0" class="empty-state">
        <strong>没有找到相关主题</strong>
        <p>试试更短的关键词，或者换一个版块/排序方式。</p>
        <button type="button" class="btn btn-ghost btn-sm" @click="clearFilters">重置筛选</button>
      </div>
      <template v-else>
        <ul v-if="pageData" class="search-results">
          <li
            v-for="(hit, index) in pageData.items"
            :key="hit.topic.id"
            class="search-result"
            :style="{ animationDelay: `${index * 35}ms` }"
          >
            <div class="search-result-head">
              <span class="search-match-badge" :class="`is-${hit.match.matched_in}`">
                {{
                  hit.match.matched_in === 'title'
                    ? '标题命中'
                    : hit.match.floor != null
                      ? `第 ${hit.match.floor} 楼`
                      : '正文命中'
                }}
              </span>
              <RouterLink :to="topicLink(hit)" class="search-result-title">
                {{ hit.topic.title }}
              </RouterLink>
            </div>

            <div class="topic-meta search-result-meta">
              <span class="meta-author">{{ hit.topic.author.username }}</span>
              <span class="dot">·</span>
              <RouterLink
                :to="{ name: 'board', params: { slug: hit.topic.board.slug } }"
                class="meta-board"
              >
                {{ hit.topic.board.name }}
              </RouterLink>
              <span class="dot">·</span>
              <span>{{ formatDateTime(hit.topic.last_reply_at ?? hit.topic.created_at) }}</span>
              <span class="dot">·</span>
              <span>{{ hit.topic.reply_count }} 回复</span>
              <span class="dot">·</span>
              <span>{{ hit.topic.views }} 浏览</span>
            </div>

            <p v-if="hit.match.snippet" class="search-snippet">
              <template
                v-for="(part, partIndex) in snippetParts(hit.match.snippet)"
                :key="partIndex"
              >
                <mark v-if="part.match">{{ part.text }}</mark>
                <span v-else>{{ part.text }}</span>
              </template>
            </p>

            <RouterLink :to="topicLink(hit)" class="search-result-link">
              {{
                hit.match.matched_in === 'content' && hit.match.floor != null
                  ? `查看第 ${hit.match.floor} 楼上下文`
                  : '打开主题'
              }}
              <span class="arrow">→</span>
            </RouterLink>
          </li>
        </ul>

        <PaginationBar
          :page="pageData?.page ?? 1"
          :pages="pageData?.pages ?? 1"
          @update:page="goPage"
        />
      </template>
    </section>
  </div>
</template>
