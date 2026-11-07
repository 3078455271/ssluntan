<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = reactive({
  username: '',
  password: '',
})
const error = ref('')
const submitting = ref(false)
const notice = ref(typeof route.query.notice === 'string' ? route.query.notice : '')

function safeRedirect(): string {
  const value = route.query.redirect
  if (typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')) {
    return value
  }
  return '/'
}

async function submit(): Promise<void> {
  error.value = ''
  notice.value = ''
  if (!form.username.trim() || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }

  submitting.value = true
  try {
    await auth.login(form.username.trim(), form.password)
    await router.replace(safeRedirect())
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <section class="auth-panel">
      <header class="form-head">
        <p class="section-kicker">WELCOME BACK</p>
        <h1>登录 SSluntan</h1>
        <p>用用户名或邮箱登录，继续参与讨论。</p>
      </header>

      <div v-if="notice" class="alert alert-info">{{ notice }}</div>
      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <form class="form-grid" @submit.prevent="submit">
        <label class="form-field">
          <span>用户名 / 邮箱</span>
          <input
            v-model="form.username"
            type="text"
            autocomplete="username"
            placeholder="例如 alice 或 alice@example.com"
            :disabled="submitting"
            required
          />
        </label>

        <label class="form-field">
          <span>密码</span>
          <input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            placeholder="输入密码"
            :disabled="submitting"
            required
          />
        </label>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '登录中…' : '登录' }}
          </button>
        </div>
      </form>

      <p class="auth-switch">
        还没有账号？
        <RouterLink to="/register">立即注册</RouterLink>
      </p>
    </section>
  </div>
</template>
