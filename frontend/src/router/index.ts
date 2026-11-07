import { createRouter, createWebHistory } from 'vue-router'

import { getToken, setUnauthorizedHandler, TOKEN_KEY } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresAdmin?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/boards/:slug',
      name: 'board',
      component: () => import('@/views/BoardView.vue'),
      props: true,
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/SearchView.vue'),
    },
    {
      path: '/topics/new',
      name: 'new-topic',
      component: () => import('@/views/NewTopicView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/topics/:id(\\d+)',
      name: 'topic',
      component: () => import('@/views/TopicView.vue'),
      props: true,
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/403',
      name: 'forbidden',
      component: () => import('@/views/ForbiddenView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

setUnauthorizedHandler(() => {
  const auth = useAuthStore()
  auth.clearSession()
  const current = router.currentRoute.value
  if (current.name === 'login' || current.name === 'register') return
  void router.replace({
    name: 'login',
    query: { redirect: current.fullPath, notice: '登录状态已失效，请重新登录。' },
  })
})

// Logging out in another tab must also leave protected pages in this tab.
// Check the current stored value rather than event.newValue so a delayed logout
// event cannot override a newer login from another tab.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key !== TOKEN_KEY) return
    if (getToken()) return

    const auth = useAuthStore()
    auth.clearSession()
    const current = router.currentRoute.value
    if (current.meta.requiresAuth || current.meta.requiresAdmin) {
      void router.replace({
        name: 'login',
        query: { redirect: current.fullPath, notice: '您已在其他标签页退出登录。' },
      })
    }
  })
}

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin) {
    if (!auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    // On a fresh tab the token exists before /users/me has resolved. Wait for
    // the role so an admin does not get bounced from /admin during startup.
    if (!auth.user) await auth.restore()
    if (!auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (auth.user?.role !== 'admin') {
      return { name: 'forbidden' }
    }
  }

  if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) {
    return { name: 'home' }
  }
  return true
})

export default router
