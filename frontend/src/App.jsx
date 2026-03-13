import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'

const SUGGESTIONS = [
  'What are the billing rates?',
  'Explain the ethics rules',
  'What is the leave policy?',
  'Describe the partner track',
]

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const chatEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text) => {
    const query = text || input.trim()
    if (!query || loading) return

    setInput('')
    setError(null)

    const userMsg = { role: 'user', content: query }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const history = messages.map(m => ({
        role: m.role,
        content: m.content,
      }))

      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query, history }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Server error (${res.status})`)
      }

      const data = await res.json()
      const botMsg = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
      }
      setMessages(prev => [...prev, botMsg])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-logo">LC</div>
        <div className="header-info">
          <h1>LexCorp Legal Assistant</h1>
          <p>AI-powered legal document Q&amp;A</p>
        </div>
        <div className="header-status">
          <span className="status-dot"></span>
          Online
        </div>
      </header>

      {/* Chat Area */}
      <main className="chat-area">
        {messages.length === 0 && !loading && (
          <div className="welcome">
            <div className="welcome-icon">⚖️</div>
            <h2>Welcome to LexCorp Legal Assistant</h2>
            <p>
              Ask questions about LexCorp's policies, billing rates, ethics rules,
              and internal procedures. All answers are sourced from official documents.
            </p>
            <div className="welcome-suggestions">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="suggestion-chip"
                  onClick={() => sendMessage(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role === 'user' ? 'user' : 'bot'}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '⚖️'}
            </div>
            <div className="message-content">
              <div className="message-bubble">{msg.content}</div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <div className="sources-label">Sources</div>
                  {msg.sources.map((src, j) => (
                    <div key={j} className="source-card">
                      <div className="source-citation">
                        📄 {src.citation}
                        <span className="source-score">{src.score}</span>
                      </div>
                      <div className="source-text">{src.text}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="typing-indicator">
            <div className="message-avatar" style={{
              background: 'linear-gradient(135deg, var(--accent-soft), var(--accent-glow))',
              border: '1px solid var(--border-accent)',
              color: 'var(--accent)',
              width: 32, height: 32, borderRadius: 8,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 14,
            }}>
              ⚖️
            </div>
            <div className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        {error && <div className="error-banner">⚠️ {error}</div>}

        <div ref={chatEndRef} />
      </main>

      {/* Input */}
      <footer className="input-area">
        <div className="input-wrapper">
          <input
            ref={inputRef}
            id="chat-input"
            type="text"
            placeholder="Ask a legal question…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            autoComplete="off"
          />
          <button
            className="send-btn"
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            aria-label="Send message"
          >
            ↑
          </button>
        </div>
        <div className="input-hint">
          Responses are based on LexCorp internal documents only
        </div>
      </footer>
    </div>
  )
}

export default App
