<script setup lang="ts">
defineProps<{
  page: number
  pages: number
}>()

const emit = defineEmits<{
  (event: 'update:page', value: number): void
}>()
</script>

<template>
  <nav v-if="pages > 1" class="pagination" aria-label="分页">
    <button
      type="button"
      class="btn btn-ghost btn-sm"
      :disabled="page <= 1"
      @click="emit('update:page', page - 1)"
    >
      上一页
    </button>
    <span class="page-indicator">第 {{ page }} / {{ pages }} 页</span>
    <button
      type="button"
      class="btn btn-ghost btn-sm"
      :disabled="page >= pages"
      @click="emit('update:page', page + 1)"
    >
      下一页
    </button>
  </nav>
</template>
