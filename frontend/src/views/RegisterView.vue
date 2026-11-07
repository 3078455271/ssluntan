<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirm: '',
})
const error = ref('')
const submitting = ref(false)

function validate(): string | null {
  if (!/^[A-Za-z0-9_]{3,32}$/.test(form.username.trim())) {
    return '用户名需为 3-32 位字母、数字或下划线'
  }
  if (!form.email.trim()) {
    return '请输入邮箱'
  }
  if (form.password.length < 8) {
    return '密码至少需要 8 位'
  }
  if (form.password !== form.confirm) {
    return '两次输入的密码不一致'
  }
  return null
}

async function submit(): Promise<void> {
  error.value = ''
  const message = validate()
  if (message) {
    error.value = message
    return
  }

  submitting.value = true
  try {
    await auth.register({
      username: form.username.trim(),
      email: form.email.trim(),
      password: form.password,
    })

    try {
      await auth.login(form.username.trim(), form.password)
      await router.replace('/')
    } catch {
      await router.replace({ name: 'login', query: { notice: '注册成功，请登录。' } })
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '注册失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <section class="auth-panel">
      <header class="form-head">
        <p class="section-kicker">JOIN US</p>
        <h1>创建账号</h1>
        <p>注册后即可发布主题、回复楼层，并管理个人资料。</p>
      </header>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <form class="form-grid" @submit.prevent="submit">
        <label class="form-field">
          <span>用户名</span>
          <input
            v-model="form.username"
            type="text"
            autocomplete="username"
            maxlength="32"
            placeholder="3-32 位字母、数字或下划线"
            :disabled="submitting"
            required
          />
        </label>

        <label class="form-field">
          <span>邮箱</span>
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
            placeholder="用于登录和找回账号"
            :disabled="submitting"
            required
          />
        </label>

        <div class="form-row">
          <label class="form-field">
            <span>密码</span>
            <input
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              placeholder="至少 8 位"
              :disabled="submitting"
              required
            />
          </label>
          <label class="form-field">
            <span>确认密码</span>
            <input
              v-model="form.confirm"
              type="password"
              autocomplete="new-password"
              placeholder="再次输入密码"
              :disabled="submitting"
              required
            />
          </label>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '注册中…' : '注册' }}
          </button>
        </div>
      </form>

      <p class="auth-switch">
        已经有账号？
        <RouterLink to="/login">直接登录</RouterLink>
      </p>
    </section>
  </div>
</template>
