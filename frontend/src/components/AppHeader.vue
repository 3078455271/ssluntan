<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { initialOf, roleLabel } from '@/utils/format'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const search = ref(typeof route.query.q === 'string' ? route.query.q : '')

watch(
  () => route.query.q,
  (value) => {
    if (typeof value === 'string') search.value = value
  },
)

function submitSearch(): void {
  const q = search.value.trim()
  void router.push({ name: 'search', query: q ? { q } : {} })
}

function logout(): void {
  auth.logout()
  void router.push({ name: 'home' })
}
</script>

<template>
  <header class="app-header">
    <div class="container header-inner">
      <RouterLink to="/" class="brand">
        <span class="brand-mark">S</span>
        <span class="brand-text">
          <strong>SSluntan</strong>
          <small>社区论坛</small>
        </span>
      </RouterLink>

      <nav class="nav-links">
        <RouterLink to="/" class="nav-link">首页</RouterLink>
        <RouterLink to="/topics/new" class="nav-link">发布主题</RouterLink>
        <RouterLink v-if="auth.user?.role === 'admin'" to="/admin" class="nav-link">管理</RouterLink>
      </nav>

      <form class="search-form" @submit.prevent="submitSearch">
        <input v-model="search" type="search" placeholder="搜索标题与楼层…" aria-label="搜索标题与楼层" />
        <button type="submit" class="search-button" aria-label="搜索">搜索</button>
      </form>

      <div class="user-area">
        <template v-if="auth.isAuthenticated">
          <RouterLink to="/profile" class="user-chip">
            <img
              v-if="auth.user?.avatar_url"
              :src="auth.user.avatar_url"
              :alt="auth.displayName"
              class="chip-avatar"
            />
            <span v-else class="chip-avatar chip-fallback">{{ initialOf(auth.displayName) }}</span>
            <span class="user-meta">
              <strong>{{ auth.restoring ? '加载中…' : auth.displayName }}</strong>
              <small>{{ roleLabel(auth.user?.role ?? 'member') }}</small>
            </span>
          </RouterLink>
          <button type="button" class="btn btn-ghost btn-sm" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn-ghost btn-sm">登录</RouterLink>
          <RouterLink to="/register" class="btn btn-primary btn-sm">注册</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>
