import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from '@/App.vue'
import { setForbiddenHandler } from '@/api/client'
import router from '@/router'
import { useNoticeStore } from '@/stores/notice'
import '@/style.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia).use(router)

// Every 403 response is surfaced once, centrally, in addition to the page-level
// error text. This keeps "no permission" feedback consistent across views.
const notice = useNoticeStore(pinia)
setForbiddenHandler((message) => notice.show(message))

app.mount('#app')
