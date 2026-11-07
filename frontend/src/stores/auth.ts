import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { api, getToken, setToken, TOKEN_KEY } from '@/api/client'
import type { ProfileUpdate, RegisterPayload, UserPrivate } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getToken())
  const user = ref<UserPrivate | null>(null)
  const restoring = ref(false)
  let restoreSequence = 0

  const isAuthenticated = computed(() => Boolean(token.value))
  const displayName = computed(() => user.value?.username ?? '')

  /** Invalidate any in-flight session restore before changing the token. */
  function cancelRestore(): void {
    restoreSequence += 1
    restoring.value = false
  }

  function applySession(accessToken: string, account: UserPrivate): void {
    cancelRestore()
    setToken(accessToken)
    token.value = accessToken
    user.value = account
  }

  function clearSession(): void {
    cancelRestore()
    setToken(null)
    token.value = null
    user.value = null
  }

  async function restore(): Promise<void> {
    if (!token.value) return

    const currentToken = token.value
    const sequence = ++restoreSequence
    restoring.value = true
    try {
      const account = await api.getMe({ skipAuthRedirect: true })
      if (sequence === restoreSequence) user.value = account
    } catch {
      // A background restore must not hijack anonymous browsing with a redirect,
      // but an invalid stored token should still be removed.
      if (sequence === restoreSequence && token.value === currentToken) {
        clearSession()
      }
    } finally {
      if (sequence === restoreSequence) restoring.value = false
    }
  }

  async function login(username: string, password: string): Promise<UserPrivate> {
    const session = await api.login(username, password)
    applySession(session.access_token, session.user)
    return session.user
  }

  async function register(payload: RegisterPayload): Promise<UserPrivate> {
    return api.register(payload)
  }

  async function updateProfile(payload: ProfileUpdate): Promise<UserPrivate> {
    const account = await api.updateMe(payload)
    user.value = account
    return account
  }

  function logout(): void {
    clearSession()
  }

  // Tabs of the same origin share localStorage but not Pinia state. Always
  // reconcile against the latest stored value: a delayed "logout" event must not
  // wipe a newer login performed in another tab.
  if (typeof window !== 'undefined') {
    window.addEventListener('storage', (event) => {
      if (event.key !== TOKEN_KEY) return

      const latestToken = getToken()
      if (!latestToken) {
        if (token.value !== null || user.value !== null) {
          cancelRestore()
          token.value = null
          user.value = null
        }
        return
      }

      if (latestToken !== token.value) {
        token.value = latestToken
        user.value = null
        void restore()
      }
    })
  }

  return {
    token,
    user,
    restoring,
    isAuthenticated,
    displayName,
    restore,
    login,
    register,
    updateProfile,
    logout,
    clearSession,
  }
})
