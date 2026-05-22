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

// ── SVG Provider Icons ──
const PROVIDER_SVG = {
  anthropic: `<svg viewBox="0 0 24 24" fill="none" width="18" height="18"><rect width="24" height="24" rx="6" fill="rgba(212,150,111,0.15)"/><text x="12" y="17" text-anchor="middle" font-size="14" font-weight="700" fill="#d4966f">A</text></svg>`,
  openai: `<svg viewBox="0 0 24 24" fill="none" width="18" height="18"><rect width="24" height="24" rx="6" fill="rgba(116,167,127,0.15)"/><text x="12" y="17" text-anchor="middle" font-size="14" font-weight="700" fill="#74a77f">O</text></svg>`,
  deepseek: `<svg viewBox="0 0 24 24" fill="none" width="18" height="18"><rect width="24" height="24" rx="6" fill="rgba(88,166,255,0.15)"/><text x="12" y="17" text-anchor="middle" font-size="13" font-weight="700" fill="#58a6ff">D</text></svg>`,
  google: `<svg viewBox="0 0 24 24" fill="none" width="18" height="18"><rect width="24" height="24" rx="6" fill="rgba(234,179,61,0.15)"/><text x="12" y="17" text-anchor="middle" font-size="13" font-weight="700" fill="#eab33d">G</text></svg>`,
  meta: `<svg viewBox="0 0 24 24" fill="none" width="18" height="18"><rect width="24" height="24" rx="6" fill="rgba(88,166,255,0.15)"/><text x="12" y="17" text-anchor="middle" font-size="13" font-weight="700" fill="#58a6ff">M</text></svg>`,
  mistral: `<svg viewBox="0 0 24 24" fill="none" width="18" height="18"><rect width="24" height="24" rx="6" fill="rgba(167,139,250,0.15)"/><text x="12" y="17" text-anchor="middle" font-size="12" font-weight="700" fill="#a78bfa">Mi</text></svg>`,
}

export function providerSvg(provider) {
  const key = provider?.toLowerCase()
  return PROVIDER_SVG[key] || `<svg viewBox="0 0 24 24" fill="none" width="18" height="18"><rect width="24" height="24" rx="6" fill="rgba(139,148,158,0.1)"/><text x="12" y="17" text-anchor="middle" font-size="13" font-weight="700" fill="#8b949e">${(provider?.charAt(0) || '?').toUpperCase()}</text></svg>`
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

// ── Dimension icons ──
export function dimIcon(type) {
  const icons = {
    agent: `<svg viewBox="0 0 20 20" fill="none" width="16" height="16"><rect x="2" y="3" width="16" height="13" rx="3" stroke="currentColor" stroke-width="1.5"/><circle cx="8" cy="8.5" r="2" stroke="currentColor" stroke-width="1.2"/><rect x="4" y="12" width="12" height="2" rx="1" fill="currentColor" opacity="0.4"/></svg>`,
    model: `<svg viewBox="0 0 20 20" fill="none" width="16" height="16"><circle cx="10" cy="8" r="5" stroke="currentColor" stroke-width="1.5"/><path d="M6 13c-1.5 1.5-2.5 3.5-2 5h12c.5-1.5-.5-3.5-2-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    dataset: `<svg viewBox="0 0 20 20" fill="none" width="16" height="16"><rect x="3" y="2" width="14" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="2" x2="8" y2="18" stroke="currentColor" stroke-width="1.2"/><line x1="3" y1="6" x2="17" y2="6" stroke="currentColor" stroke-width="1"/><line x1="3" y1="14" x2="17" y2="14" stroke="currentColor" stroke-width="1"/></svg>`,
    compare: `<svg viewBox="0 0 20 20" fill="none" width="16" height="16"><rect x="1" y="2" width="8" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="2" width="8" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/></svg>`,
  }
  return icons[type] || ''
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

// ── Status system ──
const STATUS_DEFS = {
  queued:       { label: 'Queued',       cls: 'status-queued',       color: '#8b949e' },
  provisioning: { label: 'Provisioning', cls: 'status-provisioning', color: '#58a6ff' },
  running:      { label: 'Running',      cls: 'status-running',      color: '#3fb950' },
  evaluating:   { label: 'Evaluating',   cls: 'status-evaluating',   color: '#d29922' },
  completed:    { label: 'Completed',    cls: 'status-done',         color: '#3fb950' },
  failed:       { label: 'Failed',       cls: 'status-failed',       color: '#f85149' },
  timeout:      { label: 'Timeout',      cls: 'status-timeout',      color: '#db6d28' },
  cancelled:    { label: 'Cancelled',    cls: 'status-cancelled',    color: '#484f58' },
}

export function statusInfo(run) {
  if (run.status) return STATUS_DEFS[run.status] || STATUS_DEFS.queued
  if (run.accuracy != null && run.total > 0) return STATUS_DEFS.completed
  if (run.error_count > 0 && (run.total === 0 || run.total == null)) return STATUS_DEFS.failed
  if (run.instance_count > 0 && run.total == null) return STATUS_DEFS.running
  return STATUS_DEFS.queued
}

export function instanceStatusInfo(inst) {
  if (!inst.evaluation) return STATUS_DEFS.failed
  if (inst.evaluation.resolved) return STATUS_DEFS.completed
  return STATUS_DEFS.failed
}

// ── Benchmark definitions ──
export const BENCHMARKS = [
  { id: 'swebench-verified', label: 'SWE-bench Verified', tasks: 500, lang: 'Python', difficulty: 'Hard' },
  { id: 'swebench-lite', label: 'SWE-bench Lite', tasks: 300, lang: 'Python', difficulty: 'Medium' },
  { id: 'humaneval', label: 'HumanEval', tasks: 164, lang: 'Python', difficulty: 'Easy' },
  { id: 'gaia', label: 'GAIA', tasks: 466, lang: 'Multi', difficulty: 'Medium' },
  { id: 'browser-arena', label: 'BrowserArena', tasks: 200, lang: 'Web', difficulty: 'Hard' },
]

export const AGENT_TYPES = [
  { id: 'opencode', label: 'OpenCode', desc: 'Tool-use agent with shell access', capabilities: ['tool-use', 'shell', 'sandboxed'] },
  { id: 'claude', label: 'Claude Agent', desc: 'Native AI agent with tool calling', capabilities: ['tool-use', 'native-agent'] },
  { id: 'swe_agent', label: 'SWE Agent', desc: 'Research-grade software engineering agent', capabilities: ['tool-use', 'shell', 'multi-agent'] },
]

export const PROVIDERS = [
  { id: 'anthropic', label: 'Anthropic', models: ['Claude Opus 4.7', 'Claude Sonnet 4.6', 'Claude Haiku 4.5'] },
  { id: 'openai', label: 'OpenAI', models: ['GPT-4.1', 'GPT-4.1 Mini', 'o4-mini'] },
  { id: 'deepseek', label: 'DeepSeek', models: ['DeepSeek-V4', 'DeepSeek-V3'] },
  { id: 'google', label: 'Google', models: ['Gemini 2.5 Pro', 'Gemini 2.5 Flash'] },
]
