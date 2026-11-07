<template>
  <div class="empty-state forbidden-page">
    <strong>403 · 没有访问权限</strong>
    <p>该页面仅对管理员开放。如需管理权限，请先使用管理员账号登录。</p>
    <div class="forbidden-actions">
      <RouterLink to="/" class="btn btn-primary btn-sm">返回首页</RouterLink>
      <RouterLink to="/login" class="btn btn-ghost btn-sm">切换账号</RouterLink>
    </div>
  </div>
</template>
