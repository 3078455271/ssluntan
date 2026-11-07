<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api/client'
import type { BoardRead } from '@/api/types'

const route = useRoute()
const router = useRouter()

const boards = ref<BoardRead[]>([])
const loadingBoards = ref(true)
const error = ref('')
const submitting = ref(false)

const form = reactive({
  board_id: '',
  title: '',
  content: '',
})

onMounted(async () => {
  try {
    boards.value = await api.getBoards()
    const preselected = Number(route.query.board_id)
    const matched = boards.value.find((board) => board.id === preselected)
    form.board_id = String(matched?.id ?? boards.value[0]?.id ?? '')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '版块加载失败'
  } finally {
    loadingBoards.value = false
  }
})

async function submit(): Promise<void> {
  error.value = ''
  const boardId = Number(form.board_id)
  if (!boardId) {
    error.value = '请选择版块'
    return
  }
  if (form.title.trim().length < 2) {
    error.value = '标题至少需要 2 个字符'
    return
  }
  if (!form.content.trim()) {
    error.value = '正文不能为空'
    return
  }

  submitting.value = true
  try {
    const topic = await api.createTopic({
      board_id: boardId,
      title: form.title.trim(),
      content: form.content.trim(),
    })
    await router.push({ name: 'topic', params: { id: topic.id } })
  } catch (err) {
    error.value = err instanceof Error ? err.message : '发布失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="narrow-page">
    <nav class="breadcrumb">
      <RouterLink to="/">首页</RouterLink>
      <span>/</span>
      <span>发布主题</span>
    </nav>

    <section class="form-panel">
      <header class="form-head">
        <p class="section-kicker">NEW TOPIC</p>
        <h1>发布新主题</h1>
        <p>选一个合适的版块，把问题或想法写清楚，更容易得到回复。</p>
      </header>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <form class="form-grid" @submit.prevent="submit">
        <label class="form-field">
          <span>版块</span>
          <select v-model="form.board_id" :disabled="loadingBoards || submitting" required>
            <option v-if="loadingBoards" value="">正在加载版块…</option>
            <option v-for="board in boards" :key="board.id" :value="String(board.id)">
              {{ board.name }}
            </option>
          </select>
        </label>

        <label class="form-field">
          <span>标题</span>
          <input
            v-model="form.title"
            type="text"
            maxlength="200"
            minlength="2"
            placeholder="一句话说清楚你想聊什么"
            :disabled="submitting"
            required
          />
          <small>{{ form.title.length }} / 200</small>
        </label>

        <label class="form-field">
          <span>正文</span>
          <textarea
            v-model="form.content"
            rows="10"
            maxlength="20000"
            placeholder="补充背景、已经尝试过什么、希望得到什么帮助…"
            :disabled="submitting"
            required
          ></textarea>
          <small>{{ form.content.length }} / 20000</small>
        </label>

        <div class="form-actions">
          <RouterLink to="/" class="btn btn-ghost">取消</RouterLink>
          <button type="submit" class="btn btn-primary" :disabled="submitting || loadingBoards">
            {{ submitting ? '发布中…' : '发布主题' }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
