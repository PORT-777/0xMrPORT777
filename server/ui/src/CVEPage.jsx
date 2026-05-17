import { useState, useEffect } from 'react'
import { getCVEStats, fetchCVEs, getCVESchedulerStatus, startCVEScheduler, stopCVEScheduler, runCVESchedulerNow } from './api'

export default function CVEPage() {
  const [stats, setStats] = useState(null)
  const [cves, setCves] = useState([])
  const [scheduler, setScheduler] = useState(null)
  const [loading, setLoading] = useState(false)
  const [interval, setInterval] = useState(24)

  useEffect(() => {
    refreshAll()
  }, [])

  function refreshAll() {
    getCVEStats().then(setStats).catch(() => {})
    getCVESchedulerStatus().then(setScheduler).catch(() => {})
  }

  function handleFetch() {
    setLoading(true)
    fetchCVEs(30, 50).then(res => {
      setCves(res.cves || [])
      setLoading(false)
      refreshAll()
    }).catch(() => setLoading(false))
  }

  function handleStart() {
    startCVEScheduler(interval).then(() => refreshAll())
  }

  function handleStop() {
    stopCVEScheduler().then(() => refreshAll())
  }

  function handleRunNow() {
    setLoading(true)
    runCVESchedulerNow().then(() => {
      refreshAll()
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  const style = {
    container: { padding: 24, color: '#e6edf3', maxWidth: 1000, margin: '0 auto' },
    card: { background: '#161b22', borderRadius: 8, padding: 20, marginBottom: 16 },
    table: { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
    th: { textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #333', color: '#888', fontWeight: 600, fontSize: 12, textTransform: 'uppercase' },
    td: { padding: '8px 12px', borderBottom: '1px solid #222' },
    btn: { padding: '8px 16px', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13, marginRight: 8 },
    input: { padding: '8px 12px', borderRadius: 6, border: '1px solid #333', background: '#0d1117', color: '#e6edf3', fontSize: 13, width: 80 },
  }

  const sevColor = s => s === 'critical' ? '#f44' : s === 'high' ? '#facc15' : s === 'medium' ? '#58a6ff' : '#4ade80'

  return (
    <div style={style.container}>
      <h2 style={{ color: '#f44', marginBottom: 16 }}>🛡️ CVE Database</h2>

      <div style={style.card}>
        <h3 style={{ color: '#58a6ff', marginTop: 0 }}>Cache Statistics</h3>
        {stats ? (
          <>
            <p>Total CVEs: <b>{stats.total}</b></p>
            <p>Last Updated: <b>{stats.last_updated || 'never'}</b></p>
            <p>By Severity: {JSON.stringify(stats.by_severity)}</p>
          </>
        ) : <p style={{ color: '#666' }}>No data.</p>}
      </div>

      <div style={style.card}>
        <h3 style={{ color: '#4ade80', marginTop: 0 }}>Scheduler</h3>
        {scheduler && (
          <>
            <p>Status: <b style={{ color: scheduler.running ? '#4ade80' : '#f87171' }}>{scheduler.running ? 'Running' : 'Stopped'}</b></p>
            <p>Interval: <b>{scheduler.interval_hours}h</b></p>
            <p>Last Run: <b>{scheduler.last_run || 'never'}</b></p>
            <p>Total Runs: <b>{scheduler.run_count}</b></p>
          </>
        )}
        <div style={{ marginTop: 12 }}>
          <button onClick={handleStart} style={{ ...style.btn, background: '#238636', color: '#fff' }}>▶ Start</button>
          <button onClick={handleStop} style={{ ...style.btn, background: '#da3633', color: '#fff' }}>⏹ Stop</button>
          <button onClick={handleRunNow} style={{ ...style.btn, background: '#1f6feb', color: '#fff' }} disabled={loading}>⚡ Run Now</button>
          <span style={{ marginLeft: 12, color: '#888' }}>Interval (h):</span>
          <input type="number" value={interval} onChange={e => setInterval(parseInt(e.target.value) || 24)} style={style.input} min={1} max={168} />
        </div>
      </div>

      <div style={style.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ color: '#facc15', marginTop: 0 }}>Recent CVEs ({cves.length})</h3>
          <button onClick={handleFetch} style={{ ...style.btn, background: '#1f6feb', color: '#fff' }} disabled={loading}>
            {loading ? 'Fetching...' : '🔄 Fetch from NVD'}
          </button>
        </div>
        {cves.length === 0 && <p style={{ color: '#666' }}>No CVEs loaded. Click "Fetch from NVD" to get latest.</p>}
        <table style={style.table}>
          <thead><tr>
            <th style={style.th}>CVE</th><th style={style.th}>Service</th>
            <th style={style.th}>Severity</th><th style={style.th}>CVSS</th><th style={style.th}>Description</th>
          </tr></thead>
          <tbody>
            {cves.map((c, i) => (
              <tr key={i}>
                <td style={{ ...style.td, fontFamily: 'monospace', color: '#58a6ff' }}>{c.cve}</td>
                <td style={style.td}>{c.service}</td>
                <td style={{ ...style.td, color: sevColor(c.severity), fontWeight: 600 }}>{c.severity}</td>
                <td style={style.td}>{c.cvss}</td>
                <td style={{ ...style.td, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#aaa' }}>{c.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
