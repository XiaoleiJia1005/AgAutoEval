export function formatDuration(s) {
  if (!s || s <= 0) return '-'
  if (s < 60) return `${s.toFixed(0)}s`
  if (s < 3600) return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
}

export function agentBadge(type) {
  if (type === 'swe_agent') return 'badge-blue'
  if (type === 'claude') return 'badge-green'
  return 'badge-gray'
}

export function fmtSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
