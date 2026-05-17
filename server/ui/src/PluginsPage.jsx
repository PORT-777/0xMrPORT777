import { useState, useEffect } from 'react'
import { getPlugins, runPlugin } from './api'

export default function PluginsPage() {
  const [plugins, setPlugins] = useState([])
  const [filter, setFilter] = useState('')
  const [running, setRunning] = useState(null)
  const [result, setResult] = useState(null)
  const [target, setTarget] = useState('')

  useEffect(() => {
    getPlugins(filter).then(setPlugins).catch(() => {})
  }, [filter])

  function handleRun(plugin) {
    if (!target.trim()) return
    setRunning(plugin)
    setResult(null)
    const fullName = `${plugin.category}/${plugin.name}`
    runPlugin(fullName, target).then(res => {
      setResult({ plugin: fullName, result: res })
      setRunning(null)
    }).catch(err => {
      setResult({ plugin: fullName, result: { error: err.message } })
      setRunning(null)
    })
  }

  const style = {
    container: { padding: 24, color: '#e6edf3', maxWidth: 1000, margin: '0 auto' },
    card: { background: '#161b22', borderRadius: 8, padding: 20, marginBottom: 16 },
    table: { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
    th: { textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #333', color: '#888', fontWeight: 600, fontSize: 12, textTransform: 'uppercase' },
    td: { padding: '8px 12px', borderBottom: '1px solid #222' },
    btn: { padding: '6px 14px', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13 },
    input: { padding: '8px 12px', borderRadius: 6, border: '1px solid #333', background: '#0d1117', color: '#e6edf3', fontSize: 14, width: 250 },
  }

  const catColors = { scanners: '#58a6ff', exploits: '#f44', post_exploit: '#4ade80' }

  return (
    <div style={style.container}>
      <h2 style={{ color: '#f44', marginBottom: 16 }}>🔌 Plugins</h2>

      <div style={style.card}>
        <h3 style={{ color: '#58a6ff', marginTop: 0 }}>Run Plugin</h3>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <label style={{ color: '#888' }}>Target:</label>
          <input value={target} onChange={e => setTarget(e.target.value)} placeholder="192.168.1.1" style={style.input} />
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <button onClick={() => setFilter('')} style={{ ...style.btn, background: filter === '' ? '#1f6feb' : '#333', color: '#fff', marginRight: 8 }}>All ({plugins.length})</button>
        {['scanners', 'exploits', 'post_exploit'].map(cat => (
          <button key={cat} onClick={() => setFilter(cat)} style={{ ...style.btn, background: filter === cat ? catColors[cat] : '#333', color: '#fff', marginRight: 8 }}>
            {cat}
          </button>
        ))}
      </div>

      <div style={style.card}>
        <table style={style.table}>
          <thead><tr>
            <th style={style.th}>Category</th><th style={style.th}>Name</th>
            <th style={style.th}>Version</th><th style={style.th}>Description</th><th style={style.th}>Action</th>
          </tr></thead>
          <tbody>
            {plugins.map((p, i) => (
              <tr key={i}>
                <td style={{ ...style.td }}>
                  <span style={{ padding: '2px 8px', borderRadius: 4, background: catColors[p.category] || '#333', fontSize: 12, fontWeight: 600 }}>
                    {p.category}
                  </span>
                </td>
                <td style={{ ...style.td, fontFamily: 'monospace', color: '#58a6ff' }}>{p.name}</td>
                <td style={style.td}>{p.version}</td>
                <td style={{ ...style.td, color: '#aaa' }}>{p.description}</td>
                <td style={style.td}>
                  <button onClick={() => handleRun(p)} style={{ ...style.btn, background: running === p ? '#666' : '#238636', color: '#fff' }} disabled={running === p || !target.trim()}>
                    {running === p ? 'Running...' : '▶ Run'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {plugins.length === 0 && <p style={{ color: '#666', textAlign: 'center', padding: 20 }}>No plugins found.</p>}
      </div>

      {result && (
        <div style={style.card}>
          <h3 style={{ color: '#facc15', marginTop: 0 }}>Result: {result.plugin}</h3>
          <pre style={{ background: '#0d1117', padding: 16, borderRadius: 6, overflow: 'auto', fontSize: 13, color: '#e6edf3' }}>
            {typeof result.result === 'object' ? JSON.stringify(result.result, null, 2) : String(result.result)}
          </pre>
        </div>
      )}
    </div>
  )
}
