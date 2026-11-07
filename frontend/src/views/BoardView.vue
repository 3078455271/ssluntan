<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError, api } from '@/api/client'
import type { BoardRead, Page, TopicRead, TopicSort } from '@/api/types'
import PaginationBar from '@/components/PaginationBar.vue'
import TopicList from '@/components/TopicList.vue'

const props = defineProps<{ slug: string }>()
const route = useRoute()
const router = useRouter()

const board = ref<BoardRead | null>(null)
const pageData = ref<Page<TopicRead> | null>(null)
const loading = ref(true)
const error = ref('')
const notFound = ref(false)

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

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  notFound.value = false
  try {
    const boardInfo = await api.getBoard(props.slug)
    board.value = boardInfo
    pageData.value = await api.getTopics({
      board_id: boardInfo.id,
      page: page.value,
      page_size: 20,
      sort: sort.value,
    })
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound.value = true
    } else {
      error.value = err instanceof Error ? err.message : '加载失败'
    }
  } finally {
    loading.value = false
  }
}

function goPage(next: number): void {
  void router.push({
    name: 'board',
    params: { slug: props.slug },
    query: { ...route.query, page: next > 1 ? String(next) : undefined },
  })
}

function changeSort(next: TopicSort): void {
  void router.push({
    name: 'board',
    params: { slug: props.slug },
    query: { ...route.query, sort: next === 'latest' ? undefined : next, page: undefined },
  })
}

watch([() => props.slug, page, sort], () => void load())
onMounted(load)
</script>

<template>
  <div>
    <nav class="breadcrumb">
      <RouterLink to="/">首页</RouterLink>
      <span>/</span>
      <span>{{ board?.name ?? '版块' }}</span>
    </nav>

    <div v-if="notFound" class="empty-state">
      <strong>版块不存在</strong>
      <p>它可能已被删除，或者链接写错了。</p>
      <RouterLink to="/" class="btn btn-primary btn-sm">返回首页</RouterLink>
    </div>

    <div v-else-if="error" class="alert alert-error">
      {{ error }}
      <button type="button" class="btn btn-ghost btn-sm" @click="load">重试</button>
    </div>

    <template v-else>
      <section class="board-hero">
        <div>
          <p class="section-kicker">BOARD</p>
          <h1>{{ board?.name ?? '加载中…' }}</h1>
          <p class="board-description">{{ board?.description || '这个版块还没有介绍。' }}</p>
        </div>
        <div class="board-hero-side">
          <span class="board-count">{{ board?.topic_count ?? 0 }} 个主题</span>
          <RouterLink
            v-if="board"
            :to="{ name: 'new-topic', query: { board_id: board.id } }"
            class="btn btn-primary"
          >
            发布主题
          </RouterLink>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <div>
            <p class="section-kicker">TOPICS</p>
            <h2>主题列表</h2>
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
          <TopicList :topics="pageData?.items ?? []" empty-text="这个版块还没有主题。" />
          <PaginationBar
            :page="pageData?.page ?? 1"
            :pages="pageData?.pages ?? 1"
            @update:page="goPage"
          />
        </template>
      </section>
    </template>
  </div>
</template>
