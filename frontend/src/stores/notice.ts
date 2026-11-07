import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useNoticeStore = defineStore('notice', () => {
  const message = ref('')
  const visible = ref(false)
  let timer: ReturnType<typeof setTimeout> | undefined

  function show(text: string): void {
    message.value = text || '没有权限执行该操作'
    visible.value = true
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      visible.value = false
    }, 6000)
  }

  function dismiss(): void {
    visible.value = false
    if (timer) {
      clearTimeout(timer)
      timer = undefined
    }
  }

  return { message, visible, show, dismiss }
})
