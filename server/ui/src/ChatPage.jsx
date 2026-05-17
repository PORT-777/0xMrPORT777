import { useState, useRef, useEffect } from 'react'
import { connectWebSocket, sendMessage, sendDecision } from './api'

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [pendingDecision, setPendingDecision] = useState(null)
  const [status, setStatus] = useState('disconnected')
  const listRef = useRef(null)

  useEffect(() => {
    setStatus('connecting')
    const ws = connectWebSocket((data) => {
      if (data.type === 'answer') {
        setMessages(prev => [...prev, { role: 'assistant', content: data.content }])
      } else if (data.type === 'command_pending') {
        setPendingDecision(data)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚡ ${data.reason || ''}\n\`${data.command}\``,
          cmd: data.command,
          pending: true
        }])
      } else if (data.type === 'command_start') {
        setMessages(prev => [...prev, {
          role: 'system',
          content: `> ${data.command}`
        }])
      } else if (data.type === 'command_output') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant' && !last.final) {
            const updated = [...prev]
            updated[updated.length - 1] = { ...last, content: last.content + '\n' + data.output }
            return updated
          }
          return [...prev, { role: 'assistant', content: data.output }]
        })
      } else if (data.type === 'command_done') {
        setMessages(prev => [...prev, { role: 'system', content: `✓ ${data.command}` }])
      } else if (data.type === 'done') {
        setMessages(prev => [...prev, { role: 'assistant', content: `✅ **${data.content}**`, final: true }])
        setPendingDecision(null)
      } else if (data.type === 'stream_end') {
      } else if (data.type === 'error') {
        setMessages(prev => [...prev, { role: 'system', content: `❌ ${data.content}` }])
      }
      setStatus('connected')
    }, () => setStatus('error'))

    return () => ws.close()
  }, [])

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  }, [messages])

  function handleSend() {
    const text = input.trim()
    if (!text) return
    setMessages(prev => [...prev, { role: 'user', content: text }])
    sendMessage(text)
    setInput('')
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  function handleConfirm(yes) {
    if (!pendingDecision) return
    if (yes) {
      setMessages(prev => [...prev, { role: 'system', content: '✓ Approved' }])
      sendDecision(pendingDecision.decision)
    } else {
      setMessages(prev => [...prev, { role: 'system', content: '✗ Denied' }])
      sendMessage('skip')
    }
    setPendingDecision(null)
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span>PORT-777 <span style={{ fontSize: 12, color: status === 'connected' ? '#4ade80' : '#f87171' }}>
          ● {status}
        </span></span>
      </div>

      <div ref={listRef} style={styles.messageList}>
        {messages.map((m, i) => (
          <div key={i} style={{
            ...styles.message,
            ...(m.role === 'user' ? styles.userMsg : {}),
            ...(m.role === 'system' ? styles.systemMsg : {}),
            ...(m.pending ? styles.pendingMsg : {}),
          }}>
            <div style={styles.msgLabel}>
              {m.role === 'user' ? 'You' : m.role === 'assistant' ? 'PORT-777' : 'System'}
            </div>
            <div style={{ whiteSpace: 'pre-wrap', fontFamily: m.cmd ? 'monospace' : 'inherit' }}>
              {m.content}
            </div>
            {m.pending && (
              <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                <button onClick={() => handleConfirm(true)} style={styles.yesBtn}>✓ Execute</button>
                <button onClick={() => handleConfirm(false)} style={styles.noBtn}>✗ Skip</button>
              </div>
            )}
          </div>
        ))}
        {messages.length === 0 && (
          <div style={{ color: '#666', textAlign: 'center', marginTop: 60 }}>
            <div style={{ fontSize: 40 }}>💀</div>
            <p>Type anything to start.<br/>Chat in English or Arabic.</p>
          </div>
        )}
      </div>

      <div style={styles.inputBar}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type anything..."
          style={styles.input}
          disabled={status === 'connecting'}
        />
        <button onClick={handleSend} style={styles.sendBtn} disabled={!input.trim()}>Send</button>
      </div>
    </div>
  )
}

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: 800, margin: '0 auto', borderLeft: '1px solid #222', borderRight: '1px solid #222' },
  header: { padding: '12px 16px', borderBottom: '1px solid #333', background: '#111', fontWeight: 'bold', fontSize: 18, color: '#f44' },
  messageList: { flex: 1, overflowY: 'auto', padding: 16, background: '#0d1117' },
  message: { marginBottom: 16, padding: '8px 12px', borderRadius: 8, background: '#161b22', color: '#e6edf3' },
  userMsg: { background: '#1e2a3a', borderLeft: '3px solid #58a6ff' },
  systemMsg: { background: '#111', color: '#888', fontSize: 13, fontFamily: 'monospace' },
  pendingMsg: { borderLeft: '3px solid #facc15' },
  msgLabel: { fontSize: 12, color: '#888', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 },
  inputBar: { display: 'flex', padding: 12, borderTop: '1px solid #333', background: '#111', gap: 8 },
  input: { flex: 1, padding: '10px 14px', borderRadius: 6, border: '1px solid #333', background: '#0d1117', color: '#e6edf3', fontSize: 14, outline: 'none' },
  sendBtn: { padding: '10px 20px', borderRadius: 6, border: 'none', background: '#238636', color: '#fff', fontSize: 14, cursor: 'pointer' },
  yesBtn: { padding: '6px 16px', borderRadius: 4, border: 'none', background: '#238636', color: '#fff', cursor: 'pointer' },
  noBtn: { padding: '6px 16px', borderRadius: 4, border: 'none', background: '#da3633', color: '#fff', cursor: 'pointer' },
}
