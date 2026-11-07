<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

import AppHeader from '@/components/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useNoticeStore } from '@/stores/notice'

const auth = useAuthStore()
const notice = useNoticeStore()
const route = useRoute()

onMounted(() => {
  // The router guard may already have loaded /users/me (e.g. when opening /admin).
  if (auth.isAuthenticated && !auth.user) void auth.restore()
})
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="container page">
      <div v-if="notice.visible" class="alert alert-error global-notice">
        <span>{{ notice.message }}</span>
        <button type="button" class="btn btn-ghost btn-sm" @click="notice.dismiss">关闭</button>
      </div>
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </RouterView>
    </main>
    <footer class="site-footer">
      <div class="container footer-inner">
        <span>SSluntan · 前后端分离论坛</span>
        <span class="footer-links">
          <a href="/docs" target="_blank" rel="noreferrer">API 文档</a>
          <span>·</span>
          <span>Vue 3 + FastAPI</span>
        </span>
      </div>
    </footer>
  </div>
</template>
