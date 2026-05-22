const BASE = '/api'

async function fetchJSON(url) {
  const res = await fetch(BASE + url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export function getRuns() {
  return fetchJSON('/runs')
}

export function getRun(runId) {
  return fetchJSON(`/runs/${encodeURIComponent(runId)}`)
}

export function getInstance(runId, instanceId) {
  return fetchJSON(`/runs/${encodeURIComponent(runId)}/instances/${encodeURIComponent(instanceId)}`)
}

export function getMessages(runId, instanceId) {
  return fetchJSON(`/runs/${encodeURIComponent(runId)}/instances/${encodeURIComponent(instanceId)}/messages`)
}

export async function getRawFile(runId, instanceId, filename) {
  const res = await fetch(BASE + `/runs/${encodeURIComponent(runId)}/instances/${encodeURIComponent(instanceId)}/raw/${encodeURIComponent(filename)}`)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.text()
}

// ── Agent CRUD ──────────────────────────────────────────────

export function getAgents() {
  return fetchJSON('/agents')
}

export async function createAgent(agentDef) {
  const res = await fetch(BASE + '/agents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(agentDef),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))

    throw new Error(err.detail || `${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function deleteAgent(agentType) {
  const res = await fetch(BASE + `/agents/${encodeURIComponent(agentType)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `${res.status} ${res.statusText}`)
  }
  return res.json()
}
