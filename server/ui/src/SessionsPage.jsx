import { useState, useEffect } from 'react'
import { getSessions, getSession } from './api'

export default function SessionsPage() {
  const [sessions, setSessions] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)

  useEffect(() => { getSessions().then(setSessions).catch(() => {}) }, [])

  function openSession(id) {
    setSelected(id)
    getSession(id).then(setDetail).catch(() => setDetail(null))
  }

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ color: '#f44' }}>Sessions</h2>
      <table style={styles.table}>
        <thead><tr><th>ID</th><th>Objective</th><th>Status</th><th>Date</th></tr></thead>
        <tbody>
          {sessions.map(s => (
            <tr key={s.id} onClick={() => openSession(s.id)}
                style={{ cursor: 'pointer', background: selected === s.id ? '#1e2a3a' : 'transparent' }}>
              <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{s.id?.slice(0, 12)}</td>
              <td>{s.objective}</td>
              <td>{s.status}</td>
              <td>{s.timestamp}</td>
            </tr>
          ))}
          {sessions.length === 0 && <tr><td colSpan={4} style={{ color: '#666', textAlign: 'center' }}>No sessions</td></tr>}
        </tbody>
      </table>

      {detail && (
        <div style={{ marginTop: 24, background: '#161b22', padding: 16, borderRadius: 8 }}>
          <h3 style={{ color: '#58a6ff' }}>{detail.objective}</h3>
          <p style={{ color: '#888' }}>{detail.summary}</p>
          {detail.commands && (
            <table style={{ ...styles.table, marginTop: 12 }}>
              <thead><tr><th>#</th><th>Tool</th><th>Command</th></tr></thead>
              <tbody>
                {detail.commands.map((c, i) => (
                  <tr key={i}>
                    <td>{c.step}</td>
                    <td>{c.tool}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{c.command}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

const styles = {
  table: { width: '100%', borderCollapse: 'collapse', color: '#e6edf3' },
  th: { textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #333', color: '#888', fontWeight: 600, fontSize: 12, textTransform: 'uppercase' },
  td: { padding: '8px 12px', borderBottom: '1px solid #222' },
}
const th = { textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #333', color: '#888', fontWeight: 600, fontSize: 12, textTransform: 'uppercase' }
styles.table = { width: '100%', borderCollapse: 'collapse', color: '#e6edf3' }
