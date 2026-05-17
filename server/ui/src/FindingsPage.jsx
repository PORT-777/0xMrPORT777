import { useState, useEffect } from 'react'
import { getFindingsTargets, getFindingsCredentials, getFindingsVulnerabilities, getReports } from './api'

export default function FindingsPage() {
  const [targets, setTargets] = useState([])
  const [creds, setCreds] = useState([])
  const [vulns, setVulns] = useState([])
  const [reports, setReports] = useState([])
  const [tab, setTab] = useState('targets')

  useEffect(() => {
    getFindingsTargets().then(setTargets).catch(() => {})
    getFindingsCredentials().then(setCreds).catch(() => {})
    getFindingsVulnerabilities().then(setVulns).catch(() => {})
    getReports().then(setReports).catch(() => {})
  }, [])

  const style = {
    container: { padding: 24, color: '#e6edf3' },
    tabs: { display: 'flex', gap: 4, marginBottom: 16 },
    tab: (active) => ({
      padding: '8px 16px', borderRadius: '6px 6px 0 0', border: 'none',
      background: active ? '#1e2a3a' : '#111', color: active ? '#58a6ff' : '#666',
      cursor: 'pointer', fontWeight: active ? 600 : 400,
    }),
    table: { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
    th: { textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #333', color: '#888', fontWeight: 600, fontSize: 12, textTransform: 'uppercase' },
    td: { padding: '8px 12px', borderBottom: '1px solid #222' },
  }

  return (
    <div style={style.container}>
      <h2 style={{ color: '#f44', marginBottom: 16 }}>Findings</h2>

      <div style={style.tabs}>
        {['targets', 'credentials', 'vulnerabilities', 'reports'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={style.tab(tab === t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)} {t === 'targets' ? `(${targets.length})` : t === 'credentials' ? `(${creds.length})` : t === 'vulnerabilities' ? `(${vulns.length})` : `(${reports.length})`}
          </button>
        ))}
      </div>

      {tab === 'targets' && (
        <table style={style.table}>
          <thead><tr><th style={style.th}>IP</th><th style={style.th}>Hostname</th><th style={style.th}>OS</th><th style={style.th}>Ports</th><th style={style.th}>Creds</th><th style={style.th}>Vulns</th></tr></thead>
          <tbody>
            {targets.map((t, i) => (
              <tr key={i}><td style={style.td}>{t.ip}</td><td style={style.td}>{t.hostname}</td><td style={style.td}>{t.os}</td><td style={style.td}>{t.port_count}</td><td style={style.td}>{t.cred_count}</td><td style={style.td}>{t.vuln_count}</td></tr>
            ))}
            {targets.length === 0 && <tr><td colSpan={6} style={{ ...style.td, textAlign: 'center', color: '#666' }}>No targets</td></tr>}
          </tbody>
        </table>
      )}

      {tab === 'credentials' && (
        <table style={style.table}>
          <thead><tr><th style={style.th}>Target</th><th style={style.th}>Service</th><th style={style.th}>Username</th><th style={style.th}>Password</th></tr></thead>
          <tbody>
            {creds.map((c, i) => (
              <tr key={i}><td style={style.td}>{c.ip}</td><td style={style.td}>{c.service}</td><td style={style.td}>{c.username}</td><td style={{ ...style.td, fontFamily: 'monospace' }}>{c.password}</td></tr>
            ))}
            {creds.length === 0 && <tr><td colSpan={4} style={{ ...style.td, textAlign: 'center', color: '#666' }}>No credentials</td></tr>}
          </tbody>
        </table>
      )}

      {tab === 'vulnerabilities' && (
        <table style={style.table}>
          <thead><tr><th style={style.th}>Target</th><th style={style.th}>CVE</th><th style={style.th}>Severity</th><th style={style.th}>Port</th></tr></thead>
          <tbody>
            {vulns.map((v, i) => {
              const sevColor = v.severity === 'critical' ? '#f44' : v.severity === 'high' ? '#facc15' : '#58a6ff'
              return (
                <tr key={i}>
                  <td style={style.td}>{v.ip}</td>
                  <td style={{ ...style.td, fontFamily: 'monospace' }}>{v.cve}</td>
                  <td style={{ ...style.td, color: sevColor, fontWeight: 600 }}>{v.severity}</td>
                  <td style={style.td}>{v.port || '-'}</td>
                </tr>
              )
            })}
            {vulns.length === 0 && <tr><td colSpan={4} style={{ ...style.td, textAlign: 'center', color: '#666' }}>No vulnerabilities</td></tr>}
          </tbody>
        </table>
      )}

      {tab === 'reports' && (
        <table style={style.table}>
          <thead><tr><th style={style.th}>Name</th><th style={style.th}>Size</th><th style={style.th}>Date</th></tr></thead>
          <tbody>
            {reports.map((r, i) => (
              <tr key={i}><td style={style.td}>{r.name}</td><td style={style.td}>{r.size}B</td><td style={style.td}>{r.date}</td></tr>
            ))}
            {reports.length === 0 && <tr><td colSpan={3} style={{ ...style.td, textAlign: 'center', color: '#666' }}>No reports</td></tr>}
          </tbody>
        </table>
      )}
    </div>
  )
}
