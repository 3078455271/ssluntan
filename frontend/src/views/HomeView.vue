<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api/client'
import type { BoardRead, Page, TopicRead, TopicSort } from '@/api/types'
import PaginationBar from '@/components/PaginationBar.vue'
import TopicList from '@/components/TopicList.vue'

const route = useRoute()
const router = useRouter()

const boards = ref<BoardRead[]>([])
const pageData = ref<Page<TopicRead> | null>(null)
const loading = ref(true)
const error = ref('')

const sortOptions: { value: TopicSort; label: string }[] = [
  { value: 'latest', label: '最新回复' },
  { value: 'hot', label: '热门' },
  { value: 'new', label: '最新发布' },
]

const page = computed(() => Math.max(1, Number(route.query.page) || 1))
const sort = computed<TopicSort>(() => {
  const value = route.query.sort
  return value === 'hot' || value === 'new' ? value : 'latest'
})
const keyword = computed(() => (typeof route.query.q === 'string' ? route.query.q.trim() : ''))

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const [boardList, topics] = await Promise.all([
      api.getBoards(),
      api.getTopics({
        page: page.value,
        page_size: 10,
        sort: sort.value,
        q: keyword.value || undefined,
      }),
    ])
    boards.value = boardList
    pageData.value = topics
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function goPage(next: number): void {
  void router.push({
    name: 'home',
    query: { ...route.query, page: next > 1 ? String(next) : undefined },
  })
}

function changeSort(next: TopicSort): void {
  void router.push({
    name: 'home',
    query: { ...route.query, sort: next === 'latest' ? undefined : next, page: undefined },
  })
}

function clearSearch(): void {
  void router.push({ name: 'home', query: {} })
}

watch([page, sort, keyword], () => void load())
onMounted(load)
</script>

<template>
  <div>
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">SSluntan · 一个轻量社区</p>
        <h1>在这里，聊点你真正关心的事</h1>
        <p class="hero-text">
          按版块浏览主题、追最新回复，或者直接开一个新帖。FastAPI 提供 JSON API，Vue 3 负责所有界面。
        </p>
        <div class="hero-actions">
          <RouterLink to="/topics/new" class="btn btn-light">发布主题</RouterLink>
          <RouterLink to="/register" class="btn btn-outline-light">加入社区</RouterLink>
        </div>
      </div>
      <div class="hero-panel">
        <div class="hero-stat">
          <strong>{{ boards.length }}</strong>
          <span>个版块</span>
        </div>
        <div class="hero-stat">
          <strong>{{ pageData?.total ?? 0 }}</strong>
          <span>个主题</span>
        </div>
        <div class="hero-stat">
          <strong>Vue</strong>
          <span>前端</span>
        </div>
      </div>
    </section>

    <div v-if="error" class="alert alert-error">
      {{ error }}
      <button type="button" class="btn btn-ghost btn-sm" @click="load">重试</button>
    </div>

    <section class="section">
      <div class="section-head">
        <div>
          <p class="section-kicker">BOARDS</p>
          <h2>浏览版块</h2>
        </div>
        <span class="section-note">选择感兴趣的区域</span>
      </div>

      <div v-if="loading && boards.length === 0" class="skeleton-block">正在加载版块…</div>
      <div v-else class="board-grid">
        <RouterLink
          v-for="board in boards"
          :key="board.id"
          :to="{ name: 'board', params: { slug: board.slug } }"
          class="board-card"
        >
          <span class="board-index">{{ String(board.sort_order).padStart(2, '0') }}</span>
          <h3>{{ board.name }}</h3>
          <p>{{ board.description || '还没有版块说明' }}</p>
          <footer>
            <span>{{ board.topic_count }} 个主题</span>
            <span class="arrow">→</span>
          </footer>
        </RouterLink>
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <div>
          <p class="section-kicker">TOPICS</p>
          <h2>{{ keyword ? `搜索：${keyword}` : '最新主题' }}</h2>
        </div>
        <div class="tabs">
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
      </div>

      <div v-if="loading && !pageData" class="skeleton-block">正在加载主题…</div>
      <template v-else>
        <TopicList :topics="pageData?.items ?? []" :empty-text="keyword ? '换个关键词试试。' : undefined" />
        <div class="list-footer">
          <button v-if="keyword" type="button" class="link-button" @click="clearSearch">
            清除搜索「{{ keyword }}」
          </button>
          <PaginationBar
            :page="pageData?.page ?? 1"
            :pages="pageData?.pages ?? 1"
            @update:page="goPage"
          />
        </div>
      </template>
    </section>
  </div>
</template>
