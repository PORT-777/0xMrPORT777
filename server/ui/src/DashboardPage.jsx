import { useState, useEffect } from 'react'
import { getStatus, getBrain, getFindingsTargets, getFindingsCredentials, getFindingsVulnerabilities, getReports } from './api'

export default function DashboardPage() {
  const [status, setStatus] = useState(null)
  const [brain, setBrain] = useState(null)
  const [targets, setTargets] = useState([])
  const [creds, setCreds] = useState([])
  const [vulns, setVulns] = useState([])
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getStatus().catch(() => null),
      getBrain().catch(() => null),
      getFindingsTargets().catch(() => []),
      getFindingsCredentials().catch(() => []),
      getFindingsVulnerabilities().catch(() => []),
      getReports().catch(() => []),
    ]).then(([s, b, t, c, v, r]) => {
      setStatus(s)
      setBrain(b)
      setTargets(t)
      setCreds(c)
      setVulns(v)
      setReports(r)
      setLoading(false)
    })
  }, [])

  if (loading) return <div style={styles.loading}>Loading dashboard...</div>

  const sevCounts = { critical: 0, high: 0, medium: 0, low: 0 }
  vulns.forEach(v => { const s = v.severity?.toLowerCase(); if (sevCounts[s] !== undefined) sevCounts[s]++ })

  const statCards = [
    { label: 'Targets', value: targets.length, icon: '🎯', color: '#58a6ff' },
    { label: 'Open Ports', value: targets.reduce((s, t) => s + (t.port_count || 0), 0), icon: '🔓', color: '#4ade80' },
    { label: 'Credentials', value: creds.length, icon: '🔑', color: '#facc15' },
    { label: 'Vulnerabilities', value: vulns.length, icon: '💥', color: '#f44' },
    { label: 'Reports', value: reports.length, icon: '📄', color: '#a78bfa' },
    { label: 'Phase', value: brain?.phase || 'N/A', icon: '🧠', color: '#fb923c' },
  ]

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={{ margin: 0, color: '#f44' }}>📊 PORT-777 Dashboard</h2>
        <span style={{ color: '#888', fontSize: 13 }}>
          {status?.version || 'v5'} — {status?.status === 'online' ? '🟢 Online' : '⚫ Offline'}
        </span>
      </div>

      <div style={styles.grid}>
        {statCards.map((card, i) => (
          <div key={i} style={{ ...styles.card, borderTop: `3px solid ${card.color}` }}>
            <div style={{ fontSize: 28 }}>{card.icon}</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: card.color }}>{card.value}</div>
            <div style={{ fontSize: 13, color: '#888', textTransform: 'uppercase', letterSpacing: 1 }}>{card.label}</div>
          </div>
        ))}
      </div>

      <div style={styles.grid2}>
        <div style={styles.panel}>
          <h3 style={{ color: '#f44', marginTop: 0 }}>Severity Breakdown</h3>
          <div style={styles.sevBar}>
            {Object.entries(sevCounts).map(([sev, count]) => (
              <div key={sev} style={{
                flex: Math.max(count, 1),
                background: sev === 'critical' ? '#f44' : sev === 'high' ? '#facc15' : sev === 'medium' ? '#58a6ff' : '#4ade80',
                height: 24,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, fontWeight: 600, color: sev === 'high' ? '#000' : '#fff',
                borderRadius: 4, minWidth: 40,
              }}>
                {sev.toUpperCase()}: {count}
              </div>
            ))}
          </div>
        </div>

        <div style={styles.panel}>
          <h3 style={{ color: '#58a6ff', marginTop: 0 }}>Session Info</h3>
          {brain ? (
            <>
              <p style={{ color: '#aaa' }}>Phase: <b style={{ color: '#e6edf3' }}>{brain.phase}</b></p>
              <p style={{ color: '#aaa' }}>Objective: <b style={{ color: '#e6edf3' }}>{brain.objective || 'N/A'}</b></p>
              <p style={{ color: '#aaa' }}>Targets: <b style={{ color: '#e6edf3' }}>{Object.keys(brain.targets || {}).length}</b></p>
            </>
          ) : (
            <p style={{ color: '#666' }}>No active session.</p>
          )}
        </div>
      </div>

      {targets.length > 0 && (
        <div style={styles.panel}>
          <h3 style={{ color: '#4ade80', marginTop: 0 }}>Recent Targets</h3>
          <table style={styles.table}>
            <thead><tr>
              <th style={styles.th}>IP</th><th style={styles.th}>OS</th>
              <th style={styles.th}>Ports</th><th style={styles.th}>Creds</th><th style={styles.th}>Vulns</th>
            </tr></thead>
            <tbody>
              {targets.slice(0, 5).map((t, i) => (
                <tr key={i}>
                  <td style={{ ...styles.td, fontFamily: 'monospace' }}>{t.ip}</td>
                  <td style={styles.td}>{t.os || '-'}</td>
                  <td style={styles.td}>{t.port_count || 0}</td>
                  <td style={styles.td}>{t.cred_count || 0}</td>
                  <td style={styles.td}>{t.vuln_count || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

const styles = {
  container: { padding: 24, color: '#e6edf3', maxWidth: 1200, margin: '0 auto' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  loading: { padding: 40, textAlign: 'center', color: '#666' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 },
  grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 },
  card: { background: '#161b22', borderRadius: 8, padding: 20, textAlign: 'center' },
  panel: { background: '#161b22', borderRadius: 8, padding: 20 },
  sevBar: { display: 'flex', gap: 8, alignItems: 'center' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
  th: { textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #333', color: '#888', fontWeight: 600, fontSize: 12, textTransform: 'uppercase' },
  td: { padding: '8px 12px', borderBottom: '1px solid #222' },
}
