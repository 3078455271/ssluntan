<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError, api } from '@/api/client'
import type { BoardRead, Page, TopicQuery, TopicRead, TopicSort } from '@/api/types'
import PaginationBar from '@/components/PaginationBar.vue'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/format'

const PAGE_SIZE = 20

const auth = useAuthStore()
const router = useRouter()

const boards = ref<BoardRead[]>([])
const topics = ref<Page<TopicRead> | null>(null)
const loadingBoards = ref(true)
const loadingTopics = ref(true)
const boardsError = ref('')
const topicError = ref('')
const boardError = ref('')
const savingBoard = ref(false)
const busyTopic = ref<number | null>(null)

const boardFormOpen = ref(false)
const editingBoardId = ref<number | null>(null)
const form = reactive({
  name: '',
  slug: '',
  description: '',
  sort_order: 0,
  is_active: true,
})

const filterBoard = ref('')
const sort = ref<TopicSort>('latest')
const page = ref(1)
const isEditingBoard = computed(() => editingBoardId.value !== null)

// If the account is switched in another tab (or its role is downgraded), leave
// the admin console instead of showing an inert UI full of 403 responses.
watch(
  () => auth.user?.role,
  (role) => {
    if (role && role !== 'admin') void router.replace({ name: 'forbidden' })
  },
)

watch(
  () => auth.isAuthenticated,
  (authenticated) => {
    if (!authenticated) {
      const redirect = router.currentRoute.value.fullPath
      void router.replace({
        name: 'login',
        query: { redirect, notice: '登录状态已失效，请重新登录。' },
      })
    }
  },
)

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback
}

function isForbidden(err: unknown): boolean {
  return err instanceof ApiError && err.status === 403
}

async function loadBoards(): Promise<void> {
  loadingBoards.value = true
  boardsError.value = ''
  try {
    boards.value = await api.getBoards({ includeInactive: true })
  } catch (err) {
    if (!isForbidden(err)) boardsError.value = errorMessage(err, '版块加载失败')
  } finally {
    loadingBoards.value = false
  }
}

async function loadTopics(): Promise<void> {
  loadingTopics.value = true
  topicError.value = ''
  try {
    const params: TopicQuery = {
      page: page.value,
      page_size: PAGE_SIZE,
      sort: sort.value,
    }
    if (filterBoard.value) params.board_id = Number(filterBoard.value)
    topics.value = await api.getTopics(params)
  } catch (err) {
    if (!isForbidden(err)) topicError.value = errorMessage(err, '主题加载失败')
  } finally {
    loadingTopics.value = false
  }
}

async function reloadAll(): Promise<void> {
  await Promise.all([loadBoards(), loadTopics()])
}

function startCreate(): void {
  editingBoardId.value = null
  form.name = ''
  form.slug = ''
  form.description = ''
  form.sort_order = 0
  form.is_active = true
  boardError.value = ''
  boardFormOpen.value = true
}

function startEdit(board: BoardRead): void {
  editingBoardId.value = board.id
  form.name = board.name
  form.slug = board.slug
  form.description = board.description
  form.sort_order = board.sort_order
  form.is_active = board.is_active
  boardError.value = ''
  boardFormOpen.value = true
}

function closeBoardForm(): void {
  boardFormOpen.value = false
  boardError.value = ''
}

function validateBoard(): string | null {
  if (!form.name.trim()) return '版块名称不能为空'
  if (!/^[a-z0-9-]+$/.test(form.slug.trim())) {
    return 'slug 只能包含小写字母、数字和连字符'
  }
  if (!Number.isInteger(Number(form.sort_order))) return '排序必须是整数'
  return null
}

async function saveBoard(): Promise<void> {
  boardError.value = ''
  const validation = validateBoard()
  if (validation) {
    boardError.value = validation
    return
  }

  savingBoard.value = true
  try {
    const payload = {
      name: form.name.trim(),
      slug: form.slug.trim(),
      description: form.description.trim(),
      sort_order: Number(form.sort_order),
    }
    if (editingBoardId.value !== null) {
      await api.updateBoard(editingBoardId.value, { ...payload, is_active: form.is_active })
    } else {
      await api.createBoard(payload)
    }
    boardFormOpen.value = false
    await loadBoards()
    await loadTopics()
  } catch (err) {
    boardError.value = errorMessage(err, '保存版块失败')
  } finally {
    savingBoard.value = false
  }
}

async function toggleBoard(board: BoardRead): Promise<void> {
  const action = board.is_active ? '停用' : '启用'
  if (!window.confirm(`确定${action}版块「${board.name}」？`)) return

  boardsError.value = ''
  try {
    await api.updateBoard(board.id, { is_active: !board.is_active })
    await loadBoards()
  } catch (err) {
    boardsError.value = errorMessage(err, `${action}版块失败`)
  }
}

function applyFilter(): void {
  page.value = 1
  void loadTopics()
}

function changeSort(next: TopicSort): void {
  if (sort.value === next) return
  sort.value = next
  page.value = 1
  void loadTopics()
}

function goPage(next: number): void {
  page.value = next
  void loadTopics()
}

function replaceTopic(updated: TopicRead): void {
  if (!topics.value) return
  topics.value.items = topics.value.items.map((topic) =>
    topic.id === updated.id ? updated : topic,
  )
}

async function togglePin(topic: TopicRead): Promise<void> {
  busyTopic.value = topic.id
  topicError.value = ''
  try {
    const updated = await api.updateTopic(topic.id, { is_pinned: !topic.is_pinned })
    replaceTopic(updated)
  } catch (err) {
    topicError.value = errorMessage(err, '更新置顶状态失败')
  } finally {
    busyTopic.value = null
  }
}

async function toggleLock(topic: TopicRead): Promise<void> {
  busyTopic.value = topic.id
  topicError.value = ''
  try {
    const updated = await api.updateTopic(topic.id, { is_locked: !topic.is_locked })
    replaceTopic(updated)
  } catch (err) {
    topicError.value = errorMessage(err, '更新锁定状态失败')
  } finally {
    busyTopic.value = null
  }
}

async function removeTopic(topic: TopicRead): Promise<void> {
  if (!window.confirm(`确定删除主题「${topic.title}」？此操作不可恢复。`)) return

  busyTopic.value = topic.id
  topicError.value = ''
  try {
    await api.deleteTopic(topic.id)
    if (page.value > 1 && topics.value?.items.length === 1) page.value -= 1
    await loadTopics()
  } catch (err) {
    topicError.value = errorMessage(err, '删除主题失败')
  } finally {
    busyTopic.value = null
  }
}

onMounted(() => {
  void reloadAll()
})
</script>

<template>
  <div class="admin-page">
    <nav class="breadcrumb">
      <RouterLink to="/">首页</RouterLink>
      <span>/</span>
      <span>管理</span>
    </nav>

    <section class="admin-hero">
      <div>
        <p class="section-kicker">ADMIN CONSOLE</p>
        <h1>站点管理</h1>
        <p class="admin-hero-sub">
          管理版块、置顶与锁定主题，并处理违规内容。所有操作会立即写入后端。
        </p>
      </div>
      <div class="admin-hero-side">
        <div class="admin-stat">
          <strong>{{ boards.length }}</strong>
          <span>版块</span>
        </div>
        <div class="admin-stat">
          <strong>{{ topics?.total ?? 0 }}</strong>
          <span>主题</span>
        </div>
      </div>
    </section>

    <div v-if="topicError" class="alert alert-error">
      {{ topicError }}
      <button type="button" class="btn btn-ghost btn-sm" @click="loadTopics">重试</button>
    </div>

    <section class="section admin-section">
      <div class="section-head">
        <div>
          <p class="section-kicker">BOARDS</p>
          <h2>版块管理</h2>
        </div>
        <button type="button" class="btn btn-primary btn-sm" @click="startCreate">新建版块</button>
      </div>

      <div v-if="boardFormOpen" class="panel admin-form-panel">
        <div class="admin-form-head">
          <strong>{{ isEditingBoard ? '编辑版块' : '新建版块' }}</strong>
          <button type="button" class="btn btn-ghost btn-sm" @click="closeBoardForm">关闭</button>
        </div>
        <div v-if="boardError" class="alert alert-error">{{ boardError }}</div>
        <form class="form-grid" @submit.prevent="saveBoard">
          <div class="form-row">
            <label class="form-field">
              <span>名称</span>
              <input
                v-model="form.name"
                type="text"
                maxlength="64"
                required
                :disabled="savingBoard"
              />
            </label>
            <label class="form-field">
              <span>slug</span>
              <input
                v-model="form.slug"
                type="text"
                maxlength="64"
                pattern="[a-z0-9-]+"
                placeholder="例如 python"
                required
                :disabled="savingBoard"
              />
              <small>小写字母、数字和连字符，用于 URL。</small>
            </label>
          </div>
          <label class="form-field">
            <span>描述</span>
            <textarea
              v-model="form.description"
              rows="2"
              maxlength="255"
              :disabled="savingBoard"
            ></textarea>
          </label>
          <div class="form-row">
            <label class="form-field">
              <span>排序</span>
              <input v-model.number="form.sort_order" type="number" step="1" :disabled="savingBoard" />
              <small>数字越小越靠前。</small>
            </label>
            <label v-if="isEditingBoard" class="form-field">
              <span>状态</span>
              <span class="checkbox-line">
                <input v-model="form.is_active" type="checkbox" :disabled="savingBoard" />
                启用该版块
              </span>
            </label>
          </div>
          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="savingBoard">
              {{ savingBoard ? '保存中…' : '保存版块' }}
            </button>
          </div>
        </form>
      </div>

      <div v-if="boardsError" class="alert alert-error">
        {{ boardsError }}
        <button type="button" class="btn btn-ghost btn-sm" @click="loadBoards">重试</button>
      </div>

      <div v-if="loadingBoards && boards.length === 0" class="skeleton-block">正在加载版块…</div>
      <div v-else-if="boards.length === 0" class="empty-state">
        <strong>还没有版块</strong>
        <p>使用「新建版块」创建第一个讨论区。</p>
      </div>
      <div v-else class="table-scroll">
        <table class="admin-table">
          <thead>
            <tr>
              <th>版块</th>
              <th>slug</th>
              <th>主题</th>
              <th>排序</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="board in boards" :key="board.id">
              <td>
                <strong>{{ board.name }}</strong>
                <p class="admin-sub">{{ board.description || '暂无描述' }}</p>
              </td>
              <td><code>{{ board.slug }}</code></td>
              <td>{{ board.topic_count }}</td>
              <td>{{ board.sort_order }}</td>
              <td>
                <span class="badge" :class="board.is_active ? 'badge-op' : 'badge-lock'">
                  {{ board.is_active ? '启用中' : '已停用' }}
                </span>
              </td>
              <td>
                <div class="admin-actions">
                  <button type="button" class="btn btn-ghost btn-sm" @click="startEdit(board)">
                    编辑
                  </button>
                  <button type="button" class="btn btn-ghost btn-sm" @click="toggleBoard(board)">
                    {{ board.is_active ? '停用' : '启用' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="section admin-section">
      <div class="section-head">
        <div>
          <p class="section-kicker">TOPICS</p>
          <h2>主题管理</h2>
        </div>
        <span class="section-note">共 {{ topics?.total ?? 0 }} 个主题</span>
      </div>

      <div class="admin-toolbar">
        <label class="admin-filter">
          <span>版块</span>
          <select v-model="filterBoard" @change="applyFilter">
            <option value="">全部版块</option>
            <option v-for="board in boards" :key="board.id" :value="String(board.id)">
              {{ board.name }}{{ board.is_active ? '' : '（已停用）' }}
            </option>
          </select>
        </label>

        <div class="tabs admin-sort-tabs">
          <button
            type="button"
            class="tab"
            :class="{ active: sort === 'latest' }"
            @click="changeSort('latest')"
          >
            最新回复
          </button>
          <button
            type="button"
            class="tab"
            :class="{ active: sort === 'new' }"
            @click="changeSort('new')"
          >
            最新发布
          </button>
          <button
            type="button"
            class="tab"
            :class="{ active: sort === 'hot' }"
            @click="changeSort('hot')"
          >
            热门
          </button>
        </div>

        <button
          type="button"
          class="btn btn-ghost btn-sm"
          :disabled="loadingTopics"
          @click="loadTopics"
        >
          {{ loadingTopics ? '加载中…' : '刷新' }}
        </button>
      </div>

      <div v-if="loadingTopics && !topics" class="skeleton-block">正在加载主题…</div>
      <ul v-else-if="topics && topics.items.length > 0" class="admin-topic-list">
        <li v-for="topic in topics.items" :key="topic.id" class="admin-topic-row">
          <div class="admin-topic-main">
            <div class="topic-title-line">
              <span v-if="topic.is_pinned" class="badge badge-pin">置顶</span>
              <span v-if="topic.is_locked" class="badge badge-lock">已锁定</span>
              <RouterLink
                :to="{ name: 'topic', params: { id: topic.id } }"
                class="topic-title"
              >
                {{ topic.title }}
              </RouterLink>
            </div>
            <p class="topic-meta">
              <span class="meta-author">{{ topic.author.username }}</span>
              <span class="dot">·</span>
              <RouterLink
                class="meta-board"
                :to="{ name: 'board', params: { slug: topic.board.slug } }"
              >
                {{ topic.board.name }}
              </RouterLink>
              <span class="dot">·</span>
              <span>{{ formatDateTime(topic.created_at) }}</span>
            </p>
          </div>

          <div class="admin-topic-stats">
            <span><strong>{{ topic.reply_count }}</strong> 回复</span>
            <span><strong>{{ topic.views }}</strong> 浏览</span>
          </div>

          <div class="admin-actions">
            <button
              type="button"
              class="btn btn-ghost btn-sm"
              :disabled="busyTopic === topic.id"
              @click="togglePin(topic)"
            >
              {{ topic.is_pinned ? '取消置顶' : '置顶' }}
            </button>
            <button
              type="button"
              class="btn btn-ghost btn-sm"
              :disabled="busyTopic === topic.id"
              @click="toggleLock(topic)"
            >
              {{ topic.is_locked ? '解锁' : '锁定' }}
            </button>
            <button
              type="button"
              class="btn btn-danger btn-sm"
              :disabled="busyTopic === topic.id"
              @click="removeTopic(topic)"
            >
              删除
            </button>
          </div>
        </li>
      </ul>

      <div v-else class="empty-state">
        <strong>没有符合条件的主题</strong>
        <p>换一个版块或排序条件试试。</p>
      </div>

      <PaginationBar
        v-if="topics"
        :page="topics.page"
        :pages="topics.pages"
        @update:page="goPage"
      />
    </section>
  </div>
</template>
