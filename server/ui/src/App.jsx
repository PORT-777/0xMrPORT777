import { useState } from 'react'
import ChatPage from './ChatPage'
import SessionsPage from './SessionsPage'
import FindingsPage from './FindingsPage'
import GraphPage from './GraphPage'

const navStyle = {
  container: {
    display: 'flex', flexDirection: 'column', height: '100vh',
    background: '#0d1117', color: '#e6edf3', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  sidebar: {
    display: 'flex', background: '#010409', borderBottom: '1px solid #333',
    padding: '0 16px', gap: 4, overflowX: 'auto',
  },
  tab: (active) => ({
    padding: '12px 20px', border: 'none', background: 'none',
    color: active ? '#f44' : '#666', fontWeight: active ? 700 : 400,
    fontSize: 14, cursor: 'pointer', borderBottom: active ? '2px solid #f44' : '2px solid transparent',
    whiteSpace: 'nowrap',
  }),
  content: { flex: 1, overflow: 'auto' },
}

export default function App() {
  const [tab, setTab] = useState('chat')

  return (
    <div style={navStyle.container}>
      <div style={navStyle.sidebar}>
        {[
          { id: 'chat', label: '💬 Chat' },
          { id: 'sessions', label: '📋 Sessions' },
          { id: 'findings', label: '🔍 Findings' },
          { id: 'graph', label: '🕸️ Graph' },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={navStyle.tab(tab === t.id)}>
            {t.label}
          </button>
        ))}
      </div>
      <div style={navStyle.content}>
        {tab === 'chat' && <ChatPage />}
        {tab === 'sessions' && <SessionsPage />}
        {tab === 'findings' && <FindingsPage />}
        {tab === 'graph' && <GraphPage />}
      </div>
    </div>
  )
}
