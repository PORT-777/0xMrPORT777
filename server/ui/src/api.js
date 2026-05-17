const BASE = ''

async function get(path) {
  const res = await fetch(BASE + path)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export function getStatus() { return get('/api/status') }

export function getSessions() { return get('/api/sessions') }

export function getSession(id) { return get(`/api/sessions/${id}`) }

export function getFindingsTargets() { return get('/api/findings/targets') }

export function getFindingsCredentials() { return get('/api/findings/credentials') }

export function getFindingsVulnerabilities() { return get('/api/findings/vulnerabilities') }

export function getReports() { return get('/api/reports') }

export function getExploitSuggestions(target, port) {
  let q = '/api/exploits/suggest?'
  if (target) q += 'target=' + encodeURIComponent(target) + '&'
  if (port) q += 'port=' + port
  return get(q)
}

export function getGraph() { return get('/api/graph/targets') }

export function getBrain() { return get('/api/brain') }

export function resetSession() { return post('/api/reset', {}) }

export function chat(message) { return post('/api/chat', { message }) }

export function confirmDecision(decision) {
  return post('/api/chat', { message: '', decision })
}

let ws = null
let wsCallbacks = {}

export function connectWebSocket(onMessage, onError) {
  if (ws) ws.close()
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${location.host}/ws/chat`
  ws = new WebSocket(url)

  ws.onopen = () => console.log('WS connected')

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (onMessage) onMessage(data)
    } catch (err) {
      console.error('WS parse error', err)
    }
  }

  ws.onerror = (e) => {
    console.error('WS error', e)
    if (onError) onError(e)
  }

  ws.onclose = () => {
    console.log('WS disconnected')
    setTimeout(() => connectWebSocket(onMessage, onError), 3000)
  }

  return ws
}

export function sendMessage(msg) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ message: msg }))
  }
}

export function sendDecision(decision) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ decision }))
  }
}

export function disconnectWebSocket() {
  if (ws) { ws.close(); ws = null }
}

export function getCVEStats() { return get('/api/cve/stats') }

export function fetchCVEs(days = 30, maxResults = 50) {
  return post('/api/cve/fetch', { days, max_results: maxResults })
}

export function getCVESchedulerStatus() { return get('/api/cve/scheduler/status') }

export function startCVEScheduler(intervalHours = 24) {
  return post('/api/cve/scheduler/start', { interval_hours: intervalHours })
}

export function stopCVEScheduler() { return post('/api/cve/scheduler/stop', {}) }

export function runCVESchedulerNow() { return post('/api/cve/scheduler/run', {}) }

export function getPlugins(category = '') {
  let q = '/api/plugins'
  if (category) q += '?category=' + encodeURIComponent(category)
  return get(q)
}

export function runPlugin(name, target, kwargs = {}) {
  return post(`/api/plugins/${name}/run`, { target, kwargs })
}
