import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [vitals, setVitals] = useState(null)
  const [modules, setModules] = useState({})
  const [metrics, setMetrics] = useState(null)
  const [history, setHistory] = useState([])
  const [focusMode, setFocusMode] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Training Center State
  const [trainingData, setTrainingData] = useState({ preferences: {}, custom_instructions: [], voice_macros: {} })
  const [activeTab, setActiveTab] = useState('preference')
  const [prefKey, setPrefKey] = useState('')
  const [prefVal, setPrefVal] = useState('')
  const [instrText, setInstrText] = useState('')
  const [macroTrigger, setMacroTrigger] = useState('')
  const [macroCmd, setMacroCmd] = useState('')
  const [trainStatus, setTrainStatus] = useState({ message: '', type: '' })

  const API_URL = 'http://127.0.0.1:5001/api'

  const fetchDashboardData = async () => {
    try {
      const vitalsRes = await fetch(`${API_URL}/vitals`)
      if (vitalsRes.ok) {
        const vitalsData = await vitalsRes.json()
        setVitals(vitalsData)
      }

      const modulesRes = await fetch(`${API_URL}/modules`)
      if (modulesRes.ok) {
        const modulesData = await modulesRes.json()
        setModules(modulesData)
      }

      const metricsRes = await fetch(`${API_URL}/metrics`)
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json()
        setMetrics(metricsData)
        setFocusMode(metricsData.focus_mode_active || false)
      }

      const historyRes = await fetch(`${API_URL}/history`)
      if (historyRes.ok) {
        const historyData = await historyRes.json()
        setHistory(historyData)
      }

      setLoading(false)
      setError(null)
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err)
      setError("Cannot connect to Ultron Core API")
      setLoading(false)
    }
  }

  const fetchTrainingData = async () => {
    try {
      const res = await fetch(`${API_URL}/training`)
      if (res.ok) {
        const data = await res.json()
        setTrainingData(data)
      }
    } catch (err) {
      console.error("Failed to fetch training data:", err)
    }
  }

  useEffect(() => {
    fetchDashboardData()
    fetchTrainingData()

    const interval = setInterval(fetchDashboardData, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleFocusModeToggle = async (e) => {
    const isEnabled = e.target.checked
    setFocusMode(isEnabled)
    
    try {
      const res = await fetch(`${API_URL}/focus/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enable: isEnabled })
      })
      const data = await res.json()
      if (data.success) {
        setFocusMode(data.focus_active)
      } else {
        setFocusMode(!isEnabled)
        alert("Failed to toggle focus mode. Ensure you are running with Administrator privileges.")
      }
    } catch (err) {
      setFocusMode(!isEnabled)
      console.error(err)
    }
  }

  const showStatus = (message, type = 'success') => {
    setTrainStatus({ message, type })
    setTimeout(() => setTrainStatus({ message: '', type: '' }), 4000)
  }

  const handleTrainSubmit = async (e) => {
    e.preventDefault()
    let payload = { type: activeTab }
    
    if (activeTab === 'preference') {
      if (!prefKey || !prefVal) return
      payload.key = prefKey
      payload.value = prefVal
    } else if (activeTab === 'instruction') {
      if (!instrText) return
      payload.text = instrText
    } else if (activeTab === 'voice_macro') {
      if (!macroTrigger || !macroCmd) return
      payload.trigger = macroTrigger
      payload.command = macroCmd
    }

    try {
      const res = await fetch(`${API_URL}/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      if (data.success) {
        showStatus(data.message, 'success')
        setPrefKey('')
        setPrefVal('')
        setInstrText('')
        setMacroTrigger('')
        setMacroCmd('')
        fetchTrainingData() // Refresh list
      } else {
        showStatus(data.error || "Training failed", 'error')
      }
    } catch (err) {
      showStatus("Server connection failed", 'error')
      console.error(err)
    }
  }

  const handleDeleteItem = async (type, keyOrIndex) => {
    let payload = {}
    if (type === 'preference') {
      payload = { type: 'delete_preference', key: keyOrIndex }
    } else if (type === 'instruction') {
      payload = { type: 'delete_instruction', index: keyOrIndex }
    } else if (type === 'voice_macro') {
      payload = { type: 'delete_voice_macro', trigger: keyOrIndex }
    }

    try {
      const res = await fetch(`${API_URL}/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      if (data.success) {
        showStatus(data.message, 'success')
        fetchTrainingData() // Refresh list
      } else {
        showStatus(data.error || "Forget action failed", 'error')
      }
    } catch (err) {
      showStatus("Server connection failed", 'error')
      console.error(err)
    }
  }

  if (loading && !vitals) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'var(--accent-blue)', fontFamily: 'var(--mono)' }}>
        <h2>INITIALIZING ULTRON HUD...</h2>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      {/* SIDEBAR */}
      <div className="sidebar">
        <div className="brand-section">
          <div className="brand-logo">U</div>
          <div className="brand-title">
            <span className="brand-name">ULTRON</span>
            <span className="brand-tagline">Super OS</span>
          </div>
        </div>

        {vitals && (
          <div className="system-vitals-sidebar">
            <div className="sidebar-title">System Vitals</div>
            
            <div className="vital-bar-card">
              <div className="vital-info">
                <span className="vital-label">CPU Usage</span>
                <span className="vital-value">{vitals.cpu.usage_percent}%</span>
              </div>
              <div className="progress-track">
                <div 
                  className={`progress-fill ${vitals.cpu.usage_percent > 85 ? 'danger' : vitals.cpu.usage_percent > 60 ? 'warning' : ''}`}
                  style={{ width: `${vitals.cpu.usage_percent}%` }}
                ></div>
              </div>
            </div>

            <div className="vital-bar-card">
              <div className="vital-info">
                <span className="vital-label">Memory</span>
                <span className="vital-value">{vitals.memory.used_gb} / {vitals.memory.total_gb} GB</span>
              </div>
              <div className="progress-track">
                <div 
                  className={`progress-fill ${vitals.memory.percent > 85 ? 'danger' : vitals.memory.percent > 70 ? 'warning' : ''}`}
                  style={{ width: `${vitals.memory.percent}%` }}
                ></div>
              </div>
            </div>
            
            <div className="vital-bar-card">
              <div className="vital-info">
                <span className="vital-label">Storage</span>
                <span className="vital-value">{vitals.disk.percent}%</span>
              </div>
              <div className="progress-track">
                <div 
                  className={`progress-fill ${vitals.disk.percent > 90 ? 'danger' : ''}`}
                  style={{ width: `${vitals.disk.percent}%` }}
                ></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* MAIN PANEL */}
      <div className="main-panel">
        <div className="header-status">
          <div className="header-info">
            <h1>Control Center</h1>
            <div className="header-meta">
              <div className="meta-item">
                Host: <span>{vitals?.hostname || 'Unknown'}</span>
              </div>
              <div className="meta-item">
                Uptime: <span>{vitals?.uptime || '00:00:00'}</span>
              </div>
            </div>
          </div>
          
          <div className={`connection-status ${error ? 'offline' : ''}`}>
            <div className="status-dot"></div>
            {error ? 'API OFFLINE' : 'SYSTEM ONLINE'}
          </div>
        </div>

        <div className="grid-container">
          
          {/* Metrics Row */}
          {metrics && (
            <div className="glass-card grid-full-width">
              <div className="card-title">Intelligence Metrics</div>
              <div className="metrics-grid">
                <div className="metric-box">
                  <span className="metric-value">{metrics.total_commands}</span>
                  <span className="metric-label">Commands Processed</span>
                </div>
                <div className="metric-box">
                  <span className="metric-value">{metrics.websites_opened}</span>
                  <span className="metric-label">Websites Launched</span>
                </div>
                <div className="metric-box">
                  <span className="metric-value">{metrics.clipboard_items_captured}</span>
                  <span className="metric-label">Clipboard Logs</span>
                </div>
              </div>
            </div>
          )}

          {/* TRAINING & COGNITIVE CENTER */}
          <div className="glass-card grid-full-width training-card-layout">
            <div className="card-title">🧠 Cognitive & Behavior Training Center</div>
            
            <div className="training-panel-grid">
              
              {/* Form block */}
              <div className="training-form-section">
                <div className="tab-menu">
                  <button 
                    className={`tab-btn ${activeTab === 'preference' ? 'active' : ''}`} 
                    onClick={() => setActiveTab('preference')}
                  >
                    Preferences
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'instruction' ? 'active' : ''}`} 
                    onClick={() => setActiveTab('instruction')}
                  >
                    Rules / Behavior
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'voice_macro' ? 'active' : ''}`} 
                    onClick={() => setActiveTab('voice_macro')}
                  >
                    Voice Macros
                  </button>
                </div>

                <form onSubmit={handleTrainSubmit} className="cyber-form">
                  {activeTab === 'preference' && (
                    <div className="input-group-row">
                      <div className="input-field-block">
                        <label>Preference Concept (e.g. favorite_language)</label>
                        <input 
                          type="text" 
                          placeholder="Concept name..." 
                          value={prefKey} 
                          onChange={(e) => setPrefKey(e.target.value)} 
                          required 
                        />
                      </div>
                      <div className="input-field-block">
                        <label>Value (e.g. Python)</label>
                        <input 
                          type="text" 
                          placeholder="Value..." 
                          value={prefVal} 
                          onChange={(e) => setPrefVal(e.target.value)} 
                          required 
                        />
                      </div>
                    </div>
                  )}

                  {activeTab === 'instruction' && (
                    <div className="input-field-block">
                      <label>System Behavior Rule (e.g. "Always address me as Sir")</label>
                      <textarea 
                        placeholder="Teach Ultron how to act..." 
                        value={instrText} 
                        onChange={(e) => setInstrText(e.target.value)} 
                        rows={3}
                        required 
                      />
                    </div>
                  )}

                  {activeTab === 'voice_macro' && (
                    <div className="input-group-row">
                      <div className="input-field-block">
                        <label>Spoken Phrase (e.g. "deploy my site")</label>
                        <input 
                          type="text" 
                          placeholder="Spoken trigger..." 
                          value={macroTrigger} 
                          onChange={(e) => setMacroTrigger(e.target.value)} 
                          required 
                        />
                      </div>
                      <div className="input-field-block">
                        <label>System Command (e.g. "npm run deploy")</label>
                        <input 
                          type="text" 
                          placeholder="Command execution..." 
                          value={macroCmd} 
                          onChange={(e) => setMacroCmd(e.target.value)} 
                          required 
                        />
                      </div>
                    </div>
                  )}

                  <button type="submit" className="cyber-btn-submit">
                    EXECUTE SYSTEM TRAINING
                  </button>
                </form>

                {trainStatus.message && (
                  <div className={`form-status-alert ${trainStatus.type}`}>
                    {trainStatus.message}
                  </div>
                )}
              </div>

              {/* Cognitive Database Viewer */}
              <div className="training-viewer-section">
                <div className="viewer-title">Trained Knowledge Base</div>
                <div className="database-view-terminal">
                  
                  {activeTab === 'preference' && (
                    <div className="pref-list-container">
                      {Object.keys(trainingData.preferences).length > 0 ? (
                        Object.entries(trainingData.preferences).map(([key, val]) => (
                          <div className="db-entry-row" key={key}>
                            <span className="entry-key">{key}:</span>
                            <span className="entry-value">{val}</span>
                            <button className="entry-forget-btn" onClick={() => handleDeleteItem('preference', key)}>Forget</button>
                          </div>
                        ))
                      ) : (
                        <div className="empty-db-msg">No preferences stored.</div>
                      )}
                    </div>
                  )}

                  {activeTab === 'instruction' && (
                    <div className="instructions-list-container">
                      {trainingData.custom_instructions && trainingData.custom_instructions.length > 0 ? (
                        trainingData.custom_instructions.map((instr, idx) => (
                          <div className="db-entry-row-vertical" key={idx}>
                            <span className="entry-value-full">"{instr}"</span>
                            <button className="entry-forget-btn-small" onClick={() => handleDeleteItem('instruction', idx)}>Remove Rule</button>
                          </div>
                        ))
                      ) : (
                        <div className="empty-db-msg">No behavioral instructions stored.</div>
                      )}
                    </div>
                  )}

                  {activeTab === 'voice_macro' && (
                    <div className="macros-list-container">
                      {Object.keys(trainingData.voice_macros).length > 0 ? (
                        Object.entries(trainingData.voice_macros).map(([trig, cmd]) => (
                          <div className="db-entry-row" key={trig}>
                            <span className="entry-key">"{trig}":</span>
                            <span className="entry-value-cmd">{cmd}</span>
                            <button className="entry-forget-btn" onClick={() => handleDeleteItem('voice_macro', trig)}>Forget</button>
                          </div>
                        ))
                      ) : (
                        <div className="empty-db-msg">No voice macros registered.</div>
                      )}
                    </div>
                  )}

                </div>
              </div>

            </div>
          </div>

          {/* Module Statuses */}
          <div className="glass-card">
            <div className="card-title">Core Subsystems</div>
            <div className="module-grid">
              
              <div className={`module-pill ${modules.ultron_core ? 'active' : 'inactive'}`}>
                <span className="module-name">Core Brain</span>
                <span className="module-status">{modules.ultron_core ? 'ONLINE' : 'OFFLINE'}</span>
              </div>
              
              <div className={`module-pill ${modules.ultron_vision ? 'active' : 'inactive'}`}>
                <span className="module-name">Vision Engine</span>
                <span className="module-status">{modules.ultron_vision ? 'ONLINE' : 'OFFLINE'}</span>
              </div>
              
              <div className={`module-pill ${modules.wake_word ? 'active' : 'inactive'}`}>
                <span className="module-name">Wake Word</span>
                <span className="module-status">{modules.wake_word ? 'ONLINE' : 'OFFLINE'}</span>
              </div>
              
              <div className={`module-pill ${modules.ghostwriter ? 'active' : 'inactive'}`}>
                <span className="module-name">Ghostwriter</span>
                <span className="module-status">{modules.ghostwriter ? 'ONLINE' : 'OFFLINE'}</span>
              </div>

            </div>
          </div>

          {/* Focus Mode & Controls */}
          <div className="glass-card">
            <div className="card-title">System Controls</div>
            <div className="focus-card-body">
              <div className="focus-info">
                <div className="focus-headline">Focus Guard Mode</div>
                <div className="focus-desc">Blocks distracting websites system-wide</div>
              </div>
              
              <label className="switch-label">
                <input 
                  type="checkbox" 
                  className="switch-input" 
                  checked={focusMode}
                  onChange={handleFocusModeToggle}
                />
                <div className="switch-track">
                  <div className="switch-thumb"></div>
                </div>
              </label>
            </div>
          </div>
          
          {/* History Terminal */}
          <div className="glass-card grid-full-width terminal-card">
            <div className="card-title">Activity Stream</div>
            <div className="terminal-screen">
              {history && history.length > 0 ? (
                history.map((log, idx) => (
                  <div key={idx} className="log-line">
                    <span className="log-time">[{log.time.split(' ')[1].split('.')[0]}]</span>
                    <span className="log-action">Event:</span>
                    <span className="log-status">{log.action}</span>
                  </div>
                ))
              ) : (
                <div className="empty-log">Awaiting events...</div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

export default App
