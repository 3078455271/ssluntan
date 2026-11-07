<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { formatDateTime, initialOf, roleLabel } from '@/utils/format'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  avatar_url: '',
  bio: '',
})
const error = ref('')
const success = ref('')
const saving = ref(false)

watch(
  () => auth.user,
  (user) => {
    form.avatar_url = user?.avatar_url ?? ''
    form.bio = user?.bio ?? ''
  },
  { immediate: true },
)

async function save(): Promise<void> {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    await auth.updateProfile({
      avatar_url: form.avatar_url.trim() || null,
      bio: form.bio.trim() || null,
    })
    success.value = '资料已保存'
  } catch (err) {
    error.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    saving.value = false
  }
}

function logout(): void {
  auth.logout()
  void router.push('/')
}
</script>

<template>
  <div class="narrow-page">
    <section v-if="auth.user" class="panel profile-panel">
      <div class="profile-head">
        <img
          v-if="auth.user.avatar_url"
          :src="auth.user.avatar_url"
          :alt="auth.user.username"
          class="profile-avatar"
        />
        <span v-else class="profile-avatar profile-fallback">
          {{ initialOf(auth.user.username) }}
        </span>
        <div>
          <p class="section-kicker">MY ACCOUNT</p>
          <h1>{{ auth.user.username }}</h1>
          <p class="profile-sub">
            {{ roleLabel(auth.user.role) }}
            <span class="dot">·</span>
            {{ auth.user.email }}
            <span class="dot">·</span>
            加入于 {{ formatDateTime(auth.user.created_at) }}
          </p>
        </div>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <form class="form-grid" @submit.prevent="save">
        <label class="form-field">
          <span>头像链接</span>
          <input
            v-model="form.avatar_url"
            type="url"
            maxlength="500"
            placeholder="https://example.com/avatar.png"
            :disabled="saving"
          />
          <small>留空则使用用户名首字母头像。</small>
        </label>

        <label class="form-field">
          <span>个人简介</span>
          <textarea
            v-model="form.bio"
            rows="4"
            maxlength="500"
            placeholder="介绍一下你自己…"
            :disabled="saving"
          ></textarea>
          <small>{{ form.bio.length }} / 500</small>
        </label>

        <div class="form-actions">
          <button type="button" class="btn btn-ghost" :disabled="saving" @click="logout">
            退出登录
          </button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? '保存中…' : '保存资料' }}
          </button>
        </div>
      </form>
    </section>

    <div v-else-if="auth.restoring" class="skeleton-block">正在加载账号信息…</div>
  </div>
</template>
