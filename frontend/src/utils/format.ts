export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'

  // SQLite 存的是 UTC 时间，序列化后可能不带时区标记，这里补上 Z 防止被当成本地时间。
  const normalized = /Z|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return value

  const pad = (part: number) => String(part).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`
}

export function initialOf(username: string): string {
  return username.trim().charAt(0).toUpperCase() || '?'
}

export function roleLabel(role: string): string {
  if (role === 'admin') return '管理员'
  if (role === 'moderator') return '版主'
  return '成员'
}
