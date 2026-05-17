import { useState, useEffect, useRef } from 'react'
import { getGraph, getExploitSuggestions, getBrain } from './api'

export default function GraphPage() {
  const [graph, setGraph] = useState(null)
  const [exploits, setExploits] = useState([])
  const [brain, setBrain] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
  const canvasRef = useRef(null)
  const positionsRef = useRef({})
  const redrawRef = useRef(null)

  useEffect(() => {
    getGraph().then(setGraph).catch(() => {})
    getExploitSuggestions().then(setExploits).catch(() => {})
    getBrain().then(setBrain).catch(() => {})
  }, [])

  function drawGraph(hoverId) {
    const canvas = canvasRef.current
    if (!canvas || !graph || !graph.nodes) return
    const ctx = canvas.getContext('2d')
    const w = canvas.width = canvas.offsetWidth
    const h = canvas.height = 400

    ctx.clearRect(0, 0, w, h)
    ctx.fillStyle = '#0d1117'
    ctx.fillRect(0, 0, w, h)

    const cx = w / 2, cy = h / 2
    const radius = Math.min(w, h) / 2.5
    const positions = {}
    graph.nodes.forEach((n, i) => {
      const angle = (i / graph.nodes.length) * Math.PI * 2 - Math.PI / 2
      positions[n.id] = { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) }
    })
    positionsRef.current = positions

    if (graph.edges) {
      graph.edges.forEach(e => {
        const from = positions[e.from] || positions[e.from_node]
        const to = positions[e.to] || positions[e.to_node]
        if (!from || !to) return
        const isHoveredEdge = (hoverId === e.from || hoverId === e.to)
        ctx.strokeStyle = isHoveredEdge ? '#58a6ff' : '#333'
        ctx.lineWidth = isHoveredEdge ? 2 : 1
        ctx.beginPath()
        ctx.moveTo(from.x, from.y)
        ctx.lineTo(to.x, to.y)
        ctx.stroke()
        if (e.label) {
          const midX = (from.x + to.x) / 2, midY = (from.y + to.y) / 2
          ctx.fillStyle = isHoveredEdge ? '#58a6ff' : '#666'
          ctx.font = '10px monospace'
          ctx.fillText(e.label, midX + 5, midY - 5)
        }
      })
    }

    const maxScore = Math.max(...graph.nodes.map(n => (n.ports || []).length), 1)
    graph.nodes.forEach(n => {
      const pos = positions[n.id]
      if (!pos) return
      const portCount = (n.ports || []).length
      const r = 15 + (portCount / maxScore) * 15
      const isHovered = n.id === hoverId
      const isSelected = n.id === selectedNode
      const scale = isHovered ? 1.25 : isSelected ? 1.15 : 1

      const gradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, r * scale)
      if (n.is_gateway) {
        gradient.addColorStop(0, '#facc15')
        gradient.addColorStop(1, '#92400e')
      } else if (n.credentials_found || n.vulnerabilities_found) {
        gradient.addColorStop(0, '#f44')
        gradient.addColorStop(1, '#7f1d1d')
      } else {
        gradient.addColorStop(0, '#58a6ff')
        gradient.addColorStop(1, '#1e3a5f')
      }
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, r * scale, 0, Math.PI * 2)
      ctx.fillStyle = gradient
      ctx.fill()

      if (isHovered || isSelected) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 2
        ctx.stroke()
      }

      ctx.fillStyle = '#fff'
      ctx.font = `${isHovered ? 13 : 11}px sans-serif`
      ctx.textAlign = 'center'
      ctx.fillText(n.label || n.id, pos.x, pos.y + 3)
      if (portCount > 0) {
        ctx.fillStyle = '#888'
        ctx.font = '9px monospace'
        ctx.fillText(`${portCount} ports`, pos.x, pos.y - r - 8)
      }
    })
  }

  useEffect(() => {
    drawGraph(null)
  }, [graph, selectedNode])

  function findNodeAtPos(x, y) {
    const positions = positionsRef.current
    for (const [id, pos] of Object.entries(positions)) {
      const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2)
      if (dist < 25) return id
    }
    return null
  }

  function handleMouseMove(e) {
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const nodeId = findNodeAtPos(x, y)
    if (nodeId !== hoveredNode) {
      setHoveredNode(nodeId)
      drawGraph(nodeId)
    }
    if (nodeId) {
      setTooltipPos({ x: e.clientX + 12, y: e.clientY - 10 })
    }
  }

  function handleMouseLeave() {
    setHoveredNode(null)
    drawGraph(null)
  }

  function handleClick(e) {
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const nodeId = findNodeAtPos(x, y)
    setSelectedNode(nodeId)
  }

  const hoverNodeData = hoveredNode && graph?.nodes?.find(n => n.id === hoveredNode)

  const style = {
    container: { padding: 24, color: '#e6edf3' },
    canvasWrap: { position: 'relative' },
    canvas: { width: '100%', height: 400, borderRadius: 8, border: '1px solid #333', cursor: 'pointer', display: 'block' },
    tooltip: {
      position: 'fixed',
      left: tooltipPos.x,
      top: tooltipPos.y,
      background: '#1e2a3a',
      border: '1px solid #444',
      borderRadius: 8,
      padding: '10px 14px',
      fontSize: 13,
      zIndex: 1000,
      pointerEvents: 'none',
      boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
      minWidth: 180,
    },
    panel: { background: '#161b22', borderRadius: 8, padding: 16, marginTop: 16 },
    grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 },
    card: { background: '#161b22', borderRadius: 8, padding: 16 },
  }

  return (
    <div style={style.container}>
      <h2 style={{ color: '#f44', marginBottom: 16 }}>Network Graph</h2>

      <div style={style.canvasWrap}>
        <canvas ref={canvasRef} style={style.canvas} onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave} onClick={handleClick} />
        {hoverNodeData && (
          <div style={style.tooltip}>
            <div style={{ fontWeight: 700, color: '#58a6ff', marginBottom: 4 }}>{hoverNodeData.label || hoverNodeData.id}</div>
            <div style={{ color: '#aaa', fontSize: 12 }}>IP: {hoverNodeData.ip}</div>
            <div style={{ color: '#aaa', fontSize: 12 }}>OS: {hoverNodeData.os || '-'}</div>
            <div style={{ color: '#aaa', fontSize: 12 }}>Hostname: {hoverNodeData.hostname || '-'}</div>
            <div style={{ color: '#aaa', fontSize: 12 }}>Ports: {(hoverNodeData.ports || []).join(', ') || 'none'}</div>
            {hoverNodeData.is_gateway && <div style={{ color: '#facc15', fontSize: 12, marginTop: 2 }}>🔒 Gateway</div>}
            {hoverNodeData.credentials_found && <div style={{ color: '#4ade80', fontSize: 12 }}>🔑 Credentials found</div>}
            {hoverNodeData.vulnerabilities_found && <div style={{ color: '#f44', fontSize: 12 }}>💥 Vulnerabilities found</div>}
          </div>
        )}
      </div>

      {selectedNode && (
        <div style={style.panel}>
          <h3 style={{ color: '#58a6ff' }}>Selected: {selectedNode}</h3>
          {graph?.nodes?.filter(n => n.id === selectedNode).map((n, i) => (
            <div key={i}>
              <p>OS: {n.os || '-'}</p>
              <p>Hostname: {n.hostname || '-'}</p>
              <p>Ports: {(n.ports || []).join(', ') || '-'}</p>
              <p>Gateway: {n.is_gateway ? 'Yes' : 'No'}</p>
            </div>
          ))}
        </div>
      )}

      <div style={style.grid}>
        <div style={style.card}>
          <h3 style={{ color: '#facc15', marginBottom: 8 }}>Exploit Suggestions</h3>
          {exploits.length === 0 && <p style={{ color: '#666' }}>No matches yet — scan a target first.</p>}
          {exploits.map((e, i) => (
            <div key={i} style={{ borderBottom: '1px solid #222', padding: '8px 0', fontSize: 13 }}>
              <span style={{ color: e.severity === 'critical' ? '#f44' : '#facc15', fontWeight: 600 }}>{e.cve}</span>
              <span style={{ color: '#888' }}> on {e.target}:{e.port}</span>
              <p style={{ color: '#aaa', margin: '2px 0' }}>{e.description}</p>
              {e.metasploit && <p style={{ color: '#58a6ff', fontFamily: 'monospace', fontSize: 12 }}>
                msf6 {'>'} use {e.metasploit}
              </p>}
            </div>
          ))}
        </div>

        <div style={style.card}>
          <h3 style={{ color: '#4ade80', marginBottom: 8 }}>Brain State</h3>
          {brain ? (
            <>
              <p>Phase: <b>{brain.phase}</b></p>
              <p>Objective: {brain.objective || '-'}</p>
              <p>Targets: <b>{Object.keys(brain.targets || {}).length}</b></p>
              <p>Credentials: <b>{brain.credentials}</b></p>
              <p>Vulnerabilities: <b>{brain.vulnerabilities}</b></p>
              {brain.targets && Object.entries(brain.targets).slice(0, 5).map(([ip, t]) => (
                <div key={ip} style={{ marginTop: 8, padding: 8, background: '#0d1117', borderRadius: 4 }}>
                  <b>{ip}</b> — {t.os || '?'}
                  <div style={{ color: '#888', fontSize: 12 }}>Ports: {Object.keys(t.services || {}).join(', ') || '-'}</div>
                </div>
              ))}
            </>
          ) : (
            <p style={{ color: '#666' }}>No active session.</p>
          )}
        </div>
      </div>
    </div>
  )
}
