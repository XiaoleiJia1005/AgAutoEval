export function formatDuration(s) {
  if (!s || s <= 0) return '-'
  if (s < 60) return `${s.toFixed(0)}s`
  if (s < 3600) return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
}

export function agentBadge(type) {
  if (type === 'swe_agent') return 'badge-blue'
  if (type === 'claude') return 'badge-green'
  if (type === 'opencode') return 'badge-green'
  return 'badge-gray'
}

export function providerBadge(provider) {
  if (provider === 'deepseek') return 'badge-blue'
  if (provider === 'anthropic') return 'badge-green'
  if (provider === 'openai') return 'badge-green'
  return 'badge-gray'
}

export function fmtSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function accuracyColor(accuracy) {
  if (accuracy == null) return 'gray'
  const pct = accuracy * 100
  if (pct >= 60) return 'green'
  if (pct >= 40) return 'yellow'
  return 'red'
}

export function providerIcon(provider) {
  const map = {
    anthropic: 'A',
    openai: 'O',
    deepseek: 'D',
    google: 'G',
    meta: 'M',
    mistral: 'Mi',
  }
  return map[provider?.toLowerCase()] || provider?.charAt(0)?.toUpperCase() || '?'
}

export function agentLabel(type) {
  const map = {
    opencode: 'Tool-use Agent',
    claude: 'Native Agent',
    swe_agent: 'Research Agent',
    mock: 'Mock Agent',
  }
  return map[type] || type || 'Unknown'
}

export function statusInfo(run) {
  if (run.accuracy != null && run.total > 0) return { label: 'Completed', cls: 'status-done' }
  if (run.instance_count > 0 && run.total == null) return { label: 'Running', cls: 'status-running' }
  if (run.error_count > 0 && run.total === 0) return { label: 'Failed', cls: 'status-failed' }
  return { label: 'Pending', cls: 'status-pending' }
}
