<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError, api } from '@/api/client'
import type { Page, PostRead, TopicRead } from '@/api/types'
import PaginationBar from '@/components/PaginationBar.vue'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime, initialOf, roleLabel } from '@/utils/format'

const props = defineProps<{ id: string }>()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const PAGE_SIZE = 20

const topic = ref<TopicRead | null>(null)
const postPage = ref<Page<PostRead> | null>(null)
const loadingTopic = ref(true)
const loadingPosts = ref(false)
const error = ref('')
const notFound = ref(false)
const replyContent = ref('')
const replyError = ref('')
const submittingReply = ref(false)
const deleting = ref(false)
const deletingPost = ref<number | null>(null)
const postError = ref('')
const highlightedPostId = ref<number | null>(null)
const targetMissing = ref(false)
let postRequestSeq = 0

const topicId = computed(() => Number(props.id))

function queryNumber(value: unknown): number | null {
  const raw = Array.isArray(value) ? value[0] : value
  const number = Number(raw)
  return Number.isInteger(number) && number > 0 ? number : null
}

const targetPostId = computed(() => queryNumber(route.query.post))
const targetFloor = computed(() => queryNumber(route.query.floor))
const page = computed(() => Math.max(1, Number(route.query.page) || 1))
const isOwner = computed(() => auth.user?.id === topic.value?.author.id)
const canManage = computed(
  () => isOwner.value || auth.user?.role === 'admin' || auth.user?.role === 'moderator',
)

async function loadTopic(): Promise<void> {
  loadingTopic.value = true
  error.value = ''
  notFound.value = false
  try {
    topic.value = await api.getTopic(topicId.value)
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound.value = true
    } else {
      error.value = err instanceof Error ? err.message : '主题加载失败'
    }
  } finally {
    loadingTopic.value = false
  }
}

async function loadPosts(targetPage = page.value): Promise<boolean> {
  const current = ++postRequestSeq
  loadingPosts.value = true
  try {
    const result = await api.getPosts(topicId.value, targetPage, PAGE_SIZE)
    if (current !== postRequestSeq) return false
    postPage.value = result
    return true
  } catch (err) {
    if (current !== postRequestSeq) return false
    error.value = err instanceof Error ? err.message : '楼层加载失败'
    return false
  } finally {
    if (current === postRequestSeq) loadingPosts.value = false
  }
}

/** Highlight and scroll to the floor opened from a search result. */
async function focusTargetPost(): Promise<void> {
  const postId = targetPostId.value
  if (!postId) {
    highlightedPostId.value = null
    targetMissing.value = false
    return
  }

  await nextTick()
  const exists = postPage.value?.items.some((post) => post.id === postId) ?? false
  if (!exists) {
    highlightedPostId.value = null
    targetMissing.value = true
    return
  }

  targetMissing.value = false
  highlightedPostId.value = postId
  document
    .getElementById(`post-${postId}`)
    ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function loadPostsAndFocus(page: number): Promise<void> {
  if (await loadPosts(page)) await focusTargetPost()
}

function goPage(next: number): void {
  void router.push({
    name: 'topic',
    params: { id: props.id },
    query: next > 1 ? { page: String(next) } : {},
  })
}

async function submitReply(): Promise<void> {
  replyError.value = ''
  const content = replyContent.value.trim()
  if (!content) {
    replyError.value = '回复内容不能为空'
    return
  }

  submittingReply.value = true
  try {
    const post = await api.replyToTopic(topicId.value, content)
    replyContent.value = ''
    if (topic.value) topic.value.reply_count += 1

    const targetPage = Math.ceil(post.floor / PAGE_SIZE)
    if (targetPage === page.value) {
      await loadPosts(targetPage)
    } else {
      await router.push({
        name: 'topic',
        params: { id: props.id },
        query: targetPage > 1 ? { page: String(targetPage) } : {},
      })
    }
    await nextTick()
    window.setTimeout(() => {
      document
        .getElementById(`post-${post.id}`)
        ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 300)
  } catch (err) {
    replyError.value = err instanceof Error ? err.message : '回复失败'
  } finally {
    submittingReply.value = false
  }
}

async function removeTopic(): Promise<void> {
  if (!topic.value) return
  if (!window.confirm(`确定删除主题「${topic.value.title}」？`)) return

  deleting.value = true
  try {
    await api.deleteTopic(topic.value.id)
    await router.push({ name: 'board', params: { slug: topic.value.board.slug } })
  } catch (err) {
    error.value = err instanceof Error ? err.message : '删除失败'
  } finally {
    deleting.value = false
  }
}

function canManagePost(post: PostRead): boolean {
  if (auth.user?.id === post.author.id) return true
  return auth.user?.role === 'admin' || auth.user?.role === 'moderator'
}

async function removePost(post: PostRead): Promise<void> {
  if (!window.confirm(`确定删除 #${post.floor} 楼？`)) return

  deletingPost.value = post.id
  postError.value = ''
  try {
    await api.deletePost(post.id)
    if (topic.value) topic.value.reply_count = Math.max(0, topic.value.reply_count - 1)
    const currentPage = page.value
    await loadPosts(currentPage)
    if ((postPage.value?.items.length ?? 0) === 0 && currentPage > 1) {
      goPage(currentPage - 1)
    }
  } catch (err) {
    postError.value = err instanceof Error ? err.message : '删除楼层失败'
  } finally {
    deletingPost.value = null
  }
}

watch(
  () => props.id,
  async () => {
    await loadTopic()
    if (!notFound.value) await loadPostsAndFocus(1)
  },
)
watch([page, targetPostId], () => void loadPostsAndFocus(page.value))

onMounted(async () => {
  await loadTopic()
  if (!notFound.value) await loadPostsAndFocus(page.value)
})
</script>

<template>
  <div class="topic-page">
    <div v-if="notFound" class="empty-state">
      <strong>主题不存在</strong>
      <p>它可能已被作者删除，或者链接写错了。</p>
      <RouterLink to="/" class="btn btn-primary btn-sm">返回首页</RouterLink>
    </div>

    <div v-else-if="error" class="alert alert-error">
      {{ error }}
      <button type="button" class="btn btn-ghost btn-sm" @click="loadTopic">重试</button>
    </div>

    <template v-else>
      <section class="topic-hero">
        <nav class="breadcrumb">
          <RouterLink to="/">首页</RouterLink>
          <span>/</span>
          <RouterLink v-if="topic" :to="{ name: 'board', params: { slug: topic.board.slug } }">
            {{ topic.board.name }}
          </RouterLink>
          <span>/</span>
          <span>主题</span>
        </nav>

        <div class="topic-head">
          <div>
            <div class="topic-badges">
              <span v-if="topic?.is_pinned" class="badge badge-pin">置顶</span>
              <span v-if="topic?.is_locked" class="badge badge-lock">已锁定</span>
            </div>
            <h1>{{ topic?.title ?? '加载中…' }}</h1>
            <p v-if="topic" class="topic-sub">
              <span class="meta-author">{{ topic.author.username }}</span>
              <span class="dot">·</span>
              <span>{{ formatDateTime(topic.created_at) }}</span>
              <span class="dot">·</span>
              <span>{{ topic.views }} 浏览</span>
              <span class="dot">·</span>
              <span>{{ topic.reply_count }} 回复</span>
            </p>
          </div>
          <button
            v-if="canManage && topic"
            type="button"
            class="btn btn-danger btn-sm"
            :disabled="deleting"
            @click="removeTopic"
          >
            {{ deleting ? '删除中…' : '删除主题' }}
          </button>
        </div>
      </section>

      <div v-if="loadingTopic && !topic" class="skeleton-block">正在加载主题…</div>

      <section v-else class="section">
        <div class="section-head">
          <div>
            <p class="section-kicker">REPLIES</p>
            <h2>全部楼层</h2>
          </div>
          <span class="section-note">{{ postPage?.total ?? topic?.reply_count ?? 0 }} 层</span>
        </div>

        <div v-if="targetMissing" class="alert alert-info">
          <span>没有找到{{ targetFloor ? `第 ${targetFloor} 楼` : '目标楼层' }}，它可能已被删除。</span>
          <button type="button" class="btn btn-ghost btn-sm" @click="targetMissing = false">
            关闭
          </button>
        </div>

        <div v-if="postError" class="alert alert-error">{{ postError }}</div>

        <div v-if="loadingPosts && !postPage" class="skeleton-block">正在加载楼层…</div>
        <ul v-else class="post-list">
          <li
            v-for="post in postPage?.items ?? []"
            :key="post.id"
            :id="`post-${post.id}`"
            class="post-card"
            :class="{ 'post-op': post.is_op, 'post-target': highlightedPostId === post.id }"
          >
            <aside class="post-side">
              <img
                v-if="post.author.avatar_url"
                :src="post.author.avatar_url"
                :alt="post.author.username"
                class="post-avatar"
              />
              <span v-else class="post-avatar post-avatar-fallback">
                {{ initialOf(post.author.username) }}
              </span>
              <strong>{{ post.author.username }}</strong>
              <small>{{ roleLabel(post.author.role) }}</small>
            </aside>

            <div class="post-body">
              <header class="post-head">
                <span class="floor">#{{ post.floor }}</span>
                <span v-if="post.is_op" class="badge badge-op">楼主</span>
                <span class="post-time">{{ formatDateTime(post.created_at) }}</span>
                <span v-if="post.updated_at !== post.created_at" class="post-time">已编辑</span>
                <button
                  v-if="!post.is_op && canManagePost(post)"
                  type="button"
                  class="btn btn-ghost btn-sm post-delete"
                  :disabled="deletingPost === post.id"
                  @click="removePost(post)"
                >
                  {{ deletingPost === post.id ? '删除中…' : '删除' }}
                </button>
              </header>
              <p class="post-content">{{ post.content }}</p>
            </div>
          </li>
        </ul>

        <PaginationBar
          :page="postPage?.page ?? 1"
          :pages="postPage?.pages ?? 1"
          @update:page="goPage"
        />
      </section>


      <section class="section reply-section">
        <div class="section-head">
          <div>
            <p class="section-kicker">REPLY</p>
            <h2>参与讨论</h2>
          </div>
        </div>

        <div v-if="!auth.isAuthenticated" class="alert alert-info">
          请先
          <RouterLink :to="{ name: 'login', query: { redirect: route.fullPath } }">登录</RouterLink>
          后再回复。
        </div>
        <div v-else-if="topic?.is_locked" class="alert alert-warning">
          该主题已被锁定，暂时不能回复。
        </div>
        <form v-else class="reply-box" @submit.prevent="submitReply">
          <div v-if="replyError" class="alert alert-error">{{ replyError }}</div>
          <textarea
            v-model="replyContent"
            rows="5"
            maxlength="20000"
            placeholder="写下你的回复…"
            :disabled="submittingReply"
          ></textarea>
          <div class="reply-actions">
            <small>{{ replyContent.length }} / 20000</small>
            <button type="submit" class="btn btn-primary" :disabled="submittingReply">
              {{ submittingReply ? '发送中…' : '发表回复' }}
            </button>
          </div>
        </form>
      </section>
    </template>
  </div>
</template>

