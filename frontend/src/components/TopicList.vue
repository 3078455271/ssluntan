<script setup lang="ts">
import type { TopicRead } from '@/api/types'
import { formatDateTime, initialOf } from '@/utils/format'

defineProps<{
  topics: TopicRead[]
  emptyText?: string
}>()
</script>

<template>
  <div v-if="topics.length === 0" class="empty-state">
    <strong>还没有主题</strong>
    <p>{{ emptyText ?? '成为第一个在这里发帖的人吧。' }}</p>
    <RouterLink to="/topics/new" class="btn btn-primary btn-sm">发布主题</RouterLink>
  </div>

  <ul v-else class="topic-list">
    <li
      v-for="(topic, index) in topics"
      :key="topic.id"
      class="topic-row"
      :style="{ animationDelay: `${index * 30}ms` }"
    >
      <span class="topic-avatar">{{ initialOf(topic.author.username) }}</span>

      <div class="topic-main">
        <div class="topic-title-line">
          <span v-if="topic.is_pinned" class="badge badge-pin">置顶</span>
          <span v-if="topic.is_locked" class="badge badge-lock">已锁定</span>
          <RouterLink
            :to="{ name: 'topic', params: { id: topic.id } }"
            class="topic-title"
            :title="topic.title"
          >
            {{ topic.title }}
          </RouterLink>
        </div>
        <div class="topic-meta">
          <span class="meta-author">{{ topic.author.username }}</span>
          <span class="dot">·</span>
          <RouterLink :to="{ name: 'board', params: { slug: topic.board.slug } }" class="meta-board">
            {{ topic.board.name }}
          </RouterLink>
          <span class="dot">·</span>
          <span>{{ formatDateTime(topic.last_reply_at ?? topic.created_at) }}</span>
        </div>
      </div>

      <div class="topic-stats">
        <span><strong>{{ topic.reply_count }}</strong> 回复</span>
        <span><strong>{{ topic.views }}</strong> 浏览</span>
      </div>
    </li>
  </ul>
</template>
