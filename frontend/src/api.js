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

export function getRawFile(runId, instanceId, filename) {
  return fetch(BASE + `/runs/${encodeURIComponent(runId)}/instances/${encodeURIComponent(instanceId)}/raw/${encodeURIComponent(filename)}`)
    .then(res => {
      if (!res.ok) throw new Error(`${res.status}`)
      return res.text()
    })
}
