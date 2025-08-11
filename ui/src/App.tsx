import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ThemeProvider, createTheme, useTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline'
import Container from '@mui/material/Container'
import Grid from '@mui/material/Grid'
import Paper from '@mui/material/Paper'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import FormControlLabel from '@mui/material/FormControlLabel'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import SessionCard from './components/SessionCard'
import EnvBadge from './components/EnvBadge'
import MetricsDashboard from './components/MetricsDashboard'

import useLocalStorage from './hooks/useLocalStorage'
import Chip from '@mui/material/Chip';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import AddIcon from '@mui/icons-material/Add';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import ClearAllIcon from '@mui/icons-material/ClearAll';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SettingsIcon from '@mui/icons-material/Settings';
import NotificationsIcon from '@mui/icons-material/Notifications';
import BugReportIcon from '@mui/icons-material/BugReport';
import { getDashboardUrl, getPrometheusBaseUrl } from './config/dashboard';
import { getMetricsPollingInterval } from './config/api';
import Tooltip from '@mui/material/Tooltip';

function useMetrics(pollMs = 5000) {
  const [metrics, setMetrics] = useState<Record<string, number>>({})
  const lastRef = useRef<{ t: number, values: Record<string, number> } | null>(null)
  const [derived, setDerived] = useState<{avgMsgsPerConn: number}>({avgMsgsPerConn: 0})
  
  const fetchMetrics = async () => {
    try {
      const res = await fetch('/metrics', { cache: 'no-cache' })
      const text = await res.text()
      const map: Record<string, number> = {}
      text.split('\n').forEach((line) => {
        if (line.startsWith('app_')) {
          const [key, val] = line.split(' ')
          const num = Number(val)
          if (!Number.isNaN(num)) map[key] = num
        }
      })
      setMetrics(map)
      // derive simple rates from counters
      const now = Date.now()
      const last = lastRef.current
      if (last) {
        const sum = map['app_connection_messages_sum'] ?? 0
        const cnt = map['app_connection_messages_count'] ?? 0
        const avg = cnt > 0 ? (sum / cnt) : 0
        setDerived({
          avgMsgsPerConn: avg,
        })
      }
      lastRef.current = { t: now, values: map }
    } catch {
      // ignore
    }
  }
  
  useEffect(() => {
    let timer: number | undefined
    const pollMetrics = () => {
      fetchMetrics()
      timer = window.setTimeout(pollMetrics, pollMs)
    }
    pollMetrics()
    return () => { if (timer) window.clearTimeout(timer) }
  }, [pollMs])
  
  return { metrics, derived, refresh: fetchMetrics }
}

function useAlertStatus(pollMs = 10000) {
  const [alertStatus, setAlertStatus] = useState<{active: number, critical: number}>({active: 0, critical: 0})
  
  useEffect(() => {
    let timer: number | undefined
    const fetchAlertStatus = async () => {
      try {
        const res = await fetch('http://localhost:9093/api/v1/alerts', { 
          cache: 'no-cache',
          mode: 'cors'
        })
        if (res.ok) {
          const alerts = await res.json()
          const active = alerts.length
          const critical = alerts.filter((alert: any) => 
            alert.labels?.severity === 'critical' && alert.status?.state === 'active'
          ).length
          setAlertStatus({ active, critical })
        }
      } catch {
        // ignore - Alertmanager might not be running
      }
      timer = window.setTimeout(fetchAlertStatus, pollMs)
    }
    fetchAlertStatus()
    return () => { if (timer) window.clearTimeout(timer) }
  }, [pollMs])
  
  return alertStatus
}

function genUUID() {
  return crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)
}

export default function App() {
  const [autoReconnect, setAutoReconnect] = useLocalStorage<boolean>('ui:autoReconnect', true)
  const [persistSession, setPersistSession] = useLocalStorage<boolean>('ui:persistSession', true)
  const [persistMessages, setPersistMessages] = useLocalStorage<boolean>('ui:persistMessages', true)
  const [sessionPersistenceType, setSessionPersistenceType] = useLocalStorage<'localStorage' | 'redis' | 'none'>('ui:sessionPersistenceType', 'localStorage')
  const [sessions, setSessions] = useLocalStorage<string[]>('ui:sessions', [])
  const [sessionPreferences, setSessionPreferences] = useLocalStorage<Record<string, 'localStorage' | 'redis' | 'none'>>('ui:sessionPreferences', {})
  const [newSessionId, setNewSessionId] = useState<string>('')
  const [existingSessionId, setExistingSessionId] = useState<string>('')
  const { metrics, derived, refresh: refreshMetrics } = useMetrics(getMetricsPollingInterval())
  const alertStatus = useAlertStatus(10000)
  const color = (window as any).import_meta_env?.VITE_COLOR ?? (import.meta as any).env?.VITE_COLOR ?? 'unknown'

  


  useEffect(() => {
    if (sessionPersistenceType === 'none') {
      try { localStorage.removeItem('ui:sessions') } catch {}
    }
  }, [sessionPersistenceType])

  useEffect(() => {
    if (!persistMessages) {
      // Clear all persisted messages when persistence is disabled
      try {
        const keys = Object.keys(localStorage)
        keys.forEach(key => {
          if (key.startsWith('ui:messages:')) {
            localStorage.removeItem(key)
          }
        })
      } catch {}
    }
  }, [persistMessages])

  // Helper function to get session persistence type
  const getSessionPersistenceType = (sessionId: string): 'localStorage' | 'redis' | 'none' => {
    return sessionPreferences[sessionId] || sessionPersistenceType
  }

  // Helper function to set session persistence type
  const setSessionPersistenceTypeForSession = (sessionId: string, type: 'localStorage' | 'redis' | 'none') => {
    setSessionPreferences(prev => ({
      ...prev,
      [sessionId]: type
    }))
  }

  function addSession(id?: string) {
    const finalId = (id && id.trim()) || genUUID()
    if (!sessions.includes(finalId)) {
      setSessions([...sessions, finalId])
      // Set default persistence type for new session
      setSessionPersistenceTypeForSession(finalId, sessionPersistenceType)
    }
    setNewSessionId('')
  }
  function removeSession(id: string) {
    // Clear persisted messages for this session
    if (persistMessages) {
      try {
        localStorage.removeItem(`ui:messages:${id}`)
      } catch (error) {
        console.warn('Failed to clear messages for session:', id, error)
      }
    }
    
    // Clear session from localStorage if using localStorage persistence
    const sessionPersistenceType = getSessionPersistenceType(id)
    if (sessionPersistenceType === 'localStorage') {
      try {
        localStorage.removeItem(`ui:session:${id}`)
      } catch (error) {
        console.warn('Failed to clear session from localStorage:', id, error)
      }
    }
    
    // Remove session from sessions list and preferences
    setSessions(sessions.filter((s: string) => s !== id))
    setSessionPreferences(prev => {
      const newPrefs = { ...prev }
      delete newPrefs[id]
      return newPrefs
    })
  }
  function clearSessions() {
    setSessions([])
    setSessionPreferences({})
  }

  // Get all available sessions from localStorage and Redis
  function getAvailableSessions() {
    const availableSessions: Array<{id: string, type: string, lastActivity?: number}> = []
    
    try {
      // Get all localStorage keys
      const keys = Object.keys(localStorage)
      
      // Find session keys
      const sessionKeys = keys.filter(key => key.startsWith('ui:session:'))
      const messageKeys = keys.filter(key => key.startsWith('ui:messages:'))
      
      // Process session data
      sessionKeys.forEach(key => {
        try {
          const sessionId = key.replace('ui:session:', '')
          const sessionData = JSON.parse(localStorage.getItem(key) || '{}')
          availableSessions.push({
            id: sessionId,
            type: 'localStorage',
            lastActivity: sessionData.lastActivity
          })
        } catch (error) {
          console.warn('Failed to parse session data:', key, error)
        }
      })
      
      // Process message-only sessions (no session data but has messages)
      messageKeys.forEach(key => {
        try {
          const sessionId = key.replace('ui:messages:', '')
          if (!availableSessions.find(s => s.id === sessionId)) {
            availableSessions.push({
              id: sessionId,
              type: 'messages-only'
            })
          }
        } catch (error) {
          console.warn('Failed to process message key:', key, error)
        }
      })
      
      // Sort by last activity (most recent first)
      return availableSessions.sort((a, b) => {
        if (!a.lastActivity && !b.lastActivity) return 0
        if (!a.lastActivity) return 1
        if (!b.lastActivity) return -1
        return b.lastActivity - a.lastActivity
      })
    } catch (error) {
      console.warn('Failed to get available sessions:', error)
      return []
    }
  }

  // Function to get Redis sessions (this would need to be called separately)
  async function getRedisSessions() {
    // Note: This would require a new API endpoint to list all Redis sessions
    // For now, we'll rely on the session reconnection feature
    return []
  }

  function connectToExistingSession(id: string) {
    const trimmedId = id.trim()
    if (!trimmedId) return

    // Check if session already exists in current sessions
    if (sessions.includes(trimmedId)) {
      setExistingSessionId('')
      return // Session already exists
    }

    // Check localStorage for session data
    const localStorageSession = localStorage.getItem(`ui:session:${trimmedId}`)
    const localStorageMessages = localStorage.getItem(`ui:messages:${trimmedId}`)
    
    // Check if session exists in any persistence type
    if (localStorageSession || localStorageMessages) {
      // Session exists, add it to the list
      addSession(trimmedId)
      setExistingSessionId('')
      
      // Provide feedback about what was found
      let feedback = `Connected to existing session: ${trimmedId}`
      if (localStorageSession) {
        try {
          const sessionData = JSON.parse(localStorageSession)
          feedback += ` (Session data: ${sessionData.count || 0} messages)`
        } catch (e) {
          feedback += ' (Session data found)'
        }
      }
      if (localStorageMessages) {
        try {
          const messages = JSON.parse(localStorageMessages)
          feedback += ` (${messages.length} persisted messages)`
        } catch (e) {
          feedback += ' (Messages found)'
        }
      }
      console.log(feedback)
    } else {
      // Check if session exists in Redis by trying to fetch session info
      checkRedisSession(trimmedId)
    }
  }

  // Function to check if session exists in Redis
  async function checkRedisSession(sessionId: string) {
    try {
      console.log(`Checking Redis for session: ${sessionId}`)
      const response = await fetch(`/chat/api/sessions/${sessionId}/`)
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          // Session exists in Redis, add it to the list
          addSession(sessionId)
          setExistingSessionId('')
          console.log(`Connected to Redis session: ${sessionId} (count: ${data.data?.count || 0})`)
        } else {
          // Session not found in Redis either
          addSession(sessionId)
          setExistingSessionId('')
          console.log(`Session not found in any persistence, creating new: ${sessionId}`)
        }
      } else {
        // Session not found in Redis, but still try to connect
        addSession(sessionId)
        setExistingSessionId('')
        console.log(`Session not found in Redis, attempting to connect: ${sessionId}`)
      }
    } catch (error) {
      console.error(`Error checking Redis session ${sessionId}:`, error)
      // Still try to connect even if Redis check fails
      addSession(sessionId)
      setExistingSessionId('')
      console.log(`Redis check failed, attempting to connect: ${sessionId}`)
    }
  }

  const theme = createTheme({ 
    palette: { 
      mode: 'dark', 
      primary: { 
        main: '#4ea8ff',
        light: '#7bc4ff',
        dark: '#2d7dd2',
        contrastText: '#ffffff'
      }, 
      secondary: {
        main: '#3ddc97',
        light: '#6ee7b7',
        dark: '#2bb673',
        contrastText: '#ffffff'
      },
      success: { 
        main: '#3ddc97',
        light: '#6ee7b7',
        dark: '#2bb673'
      },
      warning: {
        main: '#ffb74d',
        light: '#ffcc80',
        dark: '#f57c00'
      },
      error: {
        main: '#f44336',
        light: '#e57373',
        dark: '#d32f2f'
      },
      background: {
        default: '#0a0a0a',
        paper: '#1a1a1a',
      },
      text: {
        primary: '#ffffff',
        secondary: '#b0b0b0',
      },
      divider: 'rgba(255, 255, 255, 0.12)',
    }, 
    typography: { 
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      h4: {
        fontWeight: 700,
        letterSpacing: '-0.02em',
      },
      h5: {
        fontWeight: 700,
        letterSpacing: '-0.01em',
      },
      h6: {
        fontWeight: 600,
        letterSpacing: '-0.01em',
      },
      subtitle1: {
        fontWeight: 500,
        letterSpacing: '0.01em',
      },
      subtitle2: {
        fontWeight: 600,
        letterSpacing: '0.01em',
      },
      body1: {
        fontWeight: 400,
        lineHeight: 1.6,
      },
      body2: {
        fontWeight: 400,
        lineHeight: 1.5,
      },
      button: {
        fontWeight: 600,
        textTransform: 'none',
        letterSpacing: '0.02em',
      },
    }, 
    shape: { 
      borderRadius: 16 
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            padding: '10px 24px',
            fontWeight: 600,
            textTransform: 'none',
            boxShadow: 'none',
            '&:hover': {
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            },
          },
          contained: {
            '&:hover': {
              boxShadow: '0 6px 20px rgba(78, 168, 255, 0.3)',
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 12,
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: '#4ea8ff',
              },
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                borderColor: '#4ea8ff',
                borderWidth: 2,
              },
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            fontWeight: 500,
          },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          root: {
            '& .MuiSwitch-switchBase.Mui-checked': {
              color: '#4ea8ff',
            },
            '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
              backgroundColor: '#4ea8ff',
            },
          },
        },
      },
    },
  })

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box 
        sx={{ 
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%)',
          py: { xs: 3, md: 4 }
        }}
      >
        <Container maxWidth="xl" sx={{ px: { xs: 2, md: 3 } }}>
          {/* Enhanced Header */}
          <Paper 
            elevation={0} 
            sx={{ 
              p: { xs: 3, md: 4 }, 
              mb: { xs: 3, md: 4 }, 
              border: '1px solid', 
              borderColor: 'divider', 
              position: 'sticky', 
              top: 0, 
              backdropFilter: 'blur(20px)',
              background: 'rgba(26, 26, 26, 0.9)',
              borderRadius: 3,
              zIndex: 1000,
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            }}
          >
            <Box display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={3}>
              <Box display="flex" alignItems="center" gap={2}>
                <Box 
                  sx={{ 
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
                    color: 'white',
                  }}
                >
                  <DashboardIcon sx={{ fontSize: 24 }} />
                </Box>
                <Box>
                  <Typography 
                    variant="h4" 
                    fontWeight={700}
                    sx={{ 
                      background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      fontSize: { xs: '1.5rem', md: '2rem' },
                      mb: 0.5,
                    }}
                  >
                    Django WebSocket Chat
                  </Typography>
                  <Typography 
                    variant="body2" 
                    color="text.secondary"
                    sx={{ 
                      fontSize: { xs: '0.875rem', md: '1rem' },
                      fontWeight: 500,
                    }}
                  >
                    Real-time messaging platform
                  </Typography>
                </Box>
                <EnvBadge color={color} />
              </Box>
              
              <Stack direction="row" spacing={2} alignItems="center">
                <Chip
                  size="medium"
                  label={`${sessions.length} active sessions`}
                  variant="outlined"
                  sx={{
                    borderColor: 'divider',
                    color: 'text.secondary',
                    fontWeight: 600,
                    fontSize: '0.875rem',
                  }}
                />
                {alertStatus.critical > 0 && (
                  <Chip
                    size="medium"
                    label={`${alertStatus.critical} critical alerts`}
                    color="error"
                    variant="filled"
                    startIcon={<NotificationsIcon />}
                    sx={{
                      fontWeight: 600,
                      fontSize: '0.875rem',
                      animation: 'pulse 2s infinite',
                      '@keyframes pulse': {
                        '0%': { opacity: 1 },
                        '50%': { opacity: 0.7 },
                        '100%': { opacity: 1 },
                      },
                    }}
                  />
                )}
                {alertStatus.active > 0 && alertStatus.critical === 0 && (
                  <Chip
                    size="medium"
                    label={`${alertStatus.active} active alerts`}
                    color="warning"
                    variant="filled"
                    startIcon={<NotificationsIcon />}
                    sx={{
                      fontWeight: 600,
                      fontSize: '0.875rem',
                    }}
                  />
                )}
                <Button 
                  variant="outlined" 
                  size="small"
                  href={getDashboardUrl('grafana')}
                  target="_blank" 
                  rel="noreferrer"
                  startIcon={<DashboardIcon />}
                  sx={{
                    borderColor: 'primary.main',
                    color: 'primary.main',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    px: 2,
                    py: 0.5,
                    '&:hover': {
                      bgcolor: 'primary.main',
                      color: 'primary.contrastText',
                    }
                  }}
                >
                  Grafana
                </Button>
                <Button 
                  variant="outlined" 
                  size="small"
                  href={getPrometheusBaseUrl()}
                  target="_blank" 
                  rel="noreferrer"
                  sx={{
                    borderColor: 'warning.main',
                    color: 'warning.main',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    px: 2,
                    py: 0.5,
                    '&:hover': {
                      bgcolor: 'warning.main',
                      color: 'warning.contrastText',
                    }
                  }}
                >
                  Prometheus
                </Button>
              </Stack>
            </Box>
          </Paper>

          <Grid container spacing={4} alignItems="flex-start">
            {/* Main Content - Sessions */}
            <Grid item xs={12} lg={8}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: { xs: 3, md: 4 }, 
                  border: '1px solid', 
                  borderColor: 'divider',
                  borderRadius: 3,
                  background: 'rgba(26, 26, 26, 0.6)',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                }}
              >
                <Box sx={{ mb: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                    <Box 
                      sx={{ 
                        width: 40,
                        height: 40,
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                      }}
                    >
                      <AcUnitIcon sx={{ fontSize: 20 }} />
                    </Box>
                    <Box>
                      <Typography 
                        variant="h5" 
                        fontWeight={600}
                        sx={{ 
                          color: 'text.primary',
                          mb: 0.5,
                        }}
                      >
                        WebSocket Sessions
                      </Typography>
                      <Typography 
                        variant="body2" 
                        color="text.secondary"
                        sx={{ fontWeight: 500 }}
                      >
                        Manage your real-time connections
                      </Typography>
                    </Box>
                  </Box>
                  
                  {/* Enhanced Session Controls */}
                  <Stack spacing={3}>
                    <Paper 
                      variant="outlined" 
                      sx={{ 
                        p: 3, 
                        borderRadius: 2,
                        borderColor: 'divider',
                        background: 'rgba(255, 255, 255, 0.02)',
                      }}
                    >
                      <Typography 
                        variant="subtitle1" 
                        fontWeight={600}
                        sx={{ mb: 2, color: 'text.primary' }}
                      >
                        Create New Session
                      </Typography>
                      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ xs: 'stretch', sm: 'flex-end' }}>
                        <TextField 
                          fullWidth 
                          placeholder="Enter session UUID (optional)" 
                          size="medium" 
                          value={newSessionId} 
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewSessionId(e.target.value)}
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              height: 48,
                              fontSize: '1rem',
                              fontWeight: 500,
                            }
                          }}
                        />
                        <Button 
                          variant="outlined" 
                          onClick={() => setNewSessionId(genUUID())}
                          sx={{
                            borderColor: 'divider',
                            color: 'text.secondary',
                            fontSize: '1rem',
                            fontWeight: 600,
                            minWidth: 140,
                            height: 48,
                            '&:hover': {
                              borderColor: 'primary.main',
                              color: 'primary.main',
                            }
                          }}
                        >
                          Generate
                        </Button>
                        <Button 
                          variant="contained" 
                          startIcon={<AddIcon />}
                          onClick={() => addSession(newSessionId)}
                          sx={{
                            background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
                            fontSize: '1rem',
                            fontWeight: 600,
                            minWidth: 140,
                            height: 48,
                            '&:hover': {
                              background: 'linear-gradient(135deg, #3d97ff 0%, #2dc687 100%)',
                            }
                          }}
                        >
                          Session
                        </Button>
                      </Stack>
                    </Paper>

                    <Paper 
                      variant="outlined" 
                      sx={{ 
                        p: 3, 
                        borderRadius: 2,
                        borderColor: 'divider',
                        background: 'rgba(255, 255, 255, 0.02)',
                      }}
                    >
                      <Typography 
                        variant="subtitle1" 
                        fontWeight={600}
                        sx={{ mb: 2, color: 'text.primary' }}
                      >
                        Connect to Existing Session
                      </Typography>
                      <Typography 
                        variant="body2" 
                        color="text.secondary"
                        sx={{ mb: 2, fontSize: '0.875rem' }}
                      >
                        Enter a session ID to reconnect to an existing session. Works with any persistence type.
                      </Typography>
                      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ xs: 'stretch', sm: 'flex-end' }}>
                        <TextField 
                          fullWidth 
                          placeholder="Enter existing session ID" 
                          size="medium" 
                          value={existingSessionId} 
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setExistingSessionId(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && existingSessionId.trim()) {
                              connectToExistingSession(existingSessionId)
                            }
                          }}
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              height: 48,
                              fontSize: '1rem',
                              fontWeight: 500,
                            }
                          }}
                        />
                        <FormControl size="medium" sx={{ minWidth: 200 }}>
                          <InputLabel id="available-sessions-label">Available Sessions</InputLabel>
                          <Select
                            labelId="available-sessions-label"
                            label="Available Sessions"
                            onChange={(e) => {
                              const selectedId = e.target.value as string
                              if (selectedId) {
                                setExistingSessionId(selectedId)
                              }
                            }}
                            value=""
                            sx={{
                              '& .MuiSelect-select': {
                                fontSize: '0.875rem',
                                fontWeight: 500,
                              }
                            }}
                          >
                            {getAvailableSessions()
                              .filter(session => !sessions.includes(session.id))
                              .slice(0, 10)
                              .map((session) => (
                                <MenuItem key={session.id} value={session.id}>
                                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                      {session.id.length > 20 ? `${session.id.slice(0, 8)}...${session.id.slice(-4)}` : session.id}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      {session.type} • {session.lastActivity ? `${Math.floor((Date.now() - session.lastActivity) / 1000 / 60)}m ago` : 'Unknown'}
                                    </Typography>
                                  </Box>
                                </MenuItem>
                              ))}
                            {getAvailableSessions().filter(session => !sessions.includes(session.id)).length === 0 && (
                              <MenuItem disabled>
                                <Typography variant="body2" color="text.secondary">
                                  No available sessions
                                </Typography>
                              </MenuItem>
                            )}
                          </Select>
                        </FormControl>
                        <Button 
                          variant="contained" 
                          startIcon={<AddIcon />}
                          onClick={() => connectToExistingSession(existingSessionId)}
                          disabled={!existingSessionId.trim()}
                          sx={{
                            background: 'linear-gradient(135deg, #3ddc97 0%, #4ea8ff 100%)',
                            fontSize: '1rem',
                            fontWeight: 600,
                            minWidth: 140,
                            height: 48,
                            '&:hover': {
                              background: 'linear-gradient(135deg, #2dc687 0%, #3d97ff 100%)',
                            },
                            '&:disabled': {
                              background: 'rgba(255, 255, 255, 0.12)',
                              color: 'text.disabled',
                            }
                          }}
                        >
                          Connect
                        </Button>
                      </Stack>
                    </Paper>
                    
                    <Box 
                      sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: 2,
                        p: 2,
                        borderRadius: 2,
                        bgcolor: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Stack direction="row" spacing={3} alignItems="center" flexWrap="wrap">
                        <FormControlLabel 
                          control={
                            <Switch 
                              checked={persistMessages} 
                              onChange={(_, checked) => setPersistMessages(checked)}
                            />
                          } 
                          label={
                            <Typography variant="body2" fontWeight={500}>
                              Persist messages
                            </Typography>
                          }
                        />
                        <FormControlLabel 
                          control={
                            <Switch 
                              checked={autoReconnect} 
                              onChange={(_, checked) => setAutoReconnect(checked)}
                            />
                          } 
                          label={
                            <Typography variant="body2" fontWeight={500}>
                              Auto-reconnect
                            </Typography>
                          }
                        />
                      </Stack>
                      
                      <Stack direction="row" spacing={3} alignItems="flex-start" sx={{ mt: 2 }}>
                        <FormControl size="small" sx={{ minWidth: 200, flexShrink: 0 }}>
                          <InputLabel id="session-persistence-label">Default Persistence</InputLabel>
                          <Select
                            labelId="session-persistence-label"
                            value={sessionPersistenceType}
                            label="Session Persistence"
                            onChange={(e) => setSessionPersistenceType(e.target.value as 'localStorage' | 'redis' | 'none')}
                            sx={{
                              '& .MuiSelect-select': {
                                fontSize: '0.875rem',
                                fontWeight: 500,
                              }
                            }}
                          >
                            <MenuItem value="localStorage">
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'primary.main' }} />
                                <Typography variant="body2">localStorage</Typography>
                              </Box>
                            </MenuItem>
                            <MenuItem value="redis">
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'warning.main' }} />
                                <Typography variant="body2">Redis</Typography>
                              </Box>
                            </MenuItem>
                            <MenuItem value="none">
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'text.disabled' }} />
                                <Typography variant="body2">None</Typography>
                              </Box>
                            </MenuItem>
                          </Select>
                        </FormControl>
                        
                        <Box sx={{ flex: 1, minHeight: 40, display: 'flex', alignItems: 'center' }}>
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                            {sessionPersistenceType === 'localStorage' && 'Default: New sessions use localStorage (immutable after creation)'}
                            {sessionPersistenceType === 'redis' && 'Default: New sessions use Redis with TTL (immutable after creation)'}
                            {sessionPersistenceType === 'none' && 'Default: New sessions have no persistence (immutable after creation)'}
                          </Typography>
                        </Box>
                      </Stack>
                      
                      <Button 
                        variant="outlined" 
                        startIcon={<ClearAllIcon />}
                        onClick={clearSessions} 
                        disabled={!sessions.length}
                        sx={{
                          borderColor: 'error.main',
                          color: 'error.main',
                          '&:hover': {
                            borderColor: 'error.main',
                            bgcolor: 'error.main',
                            color: 'error.contrastText',
                          }
                        }}
                      >
                        Clear All
                      </Button>
                    </Box>
                  </Stack>
                </Box>

                {/* Enhanced Sessions Grid */}
                {sessions.length === 0 ? (
                  <Paper 
                    variant="outlined" 
                    sx={{ 
                      p: 8, 
                      textAlign: 'center',
                      borderRadius: 3,
                      borderColor: 'divider',
                      background: 'rgba(255, 255, 255, 0.02)',
                    }}
                  >
                    <Box 
                      sx={{ 
                        width: 80,
                        height: 80,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 2rem',
                        color: 'white',
                      }}
                    >
                      <AddIcon sx={{ fontSize: 32 }} />
                    </Box>
                    <Typography 
                      variant="h6" 
                      color="text.secondary" 
                      sx={{ mb: 2, fontWeight: 600 }}
                    >
                      No sessions yet
                    </Typography>
                    <Typography 
                      variant="body2" 
                      color="text.secondary" 
                      sx={{ mb: 4, maxWidth: 400, mx: 'auto' }}
                    >
                      Create your first WebSocket session to start chatting and testing real-time communication
                    </Typography>
                    <Button 
                      variant="contained" 
                      startIcon={<AddIcon />}
                      onClick={() => addSession()}
                      sx={{
                        background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
                        fontSize: '1rem',
                        fontWeight: 600,
                        minWidth: 200,
                        height: 48,
                        px: 4,
                        '&:hover': {
                          background: 'linear-gradient(135deg, #3d97ff 0%, #2dc687 100%)',
                        }
                      }}
                    >
                      Generate & Add Session
                    </Button>
                  </Paper>
                ) : (
                  <Grid container spacing={3}>
                    {sessions.map((id: string) => (
                      <Grid item xs={12} md={6} xl={4} key={id}>
                        <SessionCard 
                  id={id} 
                  autoReconnect={autoReconnect} 
                  persistMessages={persistMessages} 
                  sessionPersistenceType={getSessionPersistenceType(id)} 
                  onRemove={removeSession}
                />
                      </Grid>
                    ))}
                  </Grid>
                )}
              </Paper>
            </Grid>

            {/* Enhanced Sidebar - Service Status */}
            <Grid item xs={12} lg={4}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: { xs: 3, md: 4 }, 
                  border: '1px solid', 
                  borderColor: 'divider',
                  borderRadius: 3,
                  background: 'rgba(26, 26, 26, 0.6)',
                  backdropFilter: 'blur(10px)',
                  position: 'sticky',
                  top: 140,
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                }}
              >
                <MetricsDashboard 
                  metrics={metrics}
                  derived={derived}
                  onRefresh={refreshMetrics}
                />
                
                <Stack direction={{ xs: 'column', sm: 'row', lg: 'column' }} spacing={2}>
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    href="/metrics" 
                    target="_blank" 
                    rel="noreferrer"
                    sx={{
                      borderColor: 'divider',
                      color: 'text.secondary',
                      py: 1.5,
                      '&:hover': {
                        borderColor: 'primary.main',
                        bgcolor: 'primary.main',
                        color: 'primary.contrastText',
                      }
                    }}
                  >
                    Open /metrics
                  </Button>
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    href="/healthz" 
                    target="_blank" 
                    rel="noreferrer"
                    sx={{
                      borderColor: 'divider',
                      color: 'text.secondary',
                      py: 1.5,
                      '&:hover': {
                        borderColor: 'success.main',
                        bgcolor: 'success.main',
                        color: 'success.contrastText',
                      }
                    }}
                  >
                    Open /healthz
                  </Button>
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    href="/readyz" 
                    target="_blank" 
                    rel="noreferrer"
                    sx={{
                      borderColor: 'divider',
                      color: 'text.secondary',
                      py: 1.5,
                      '&:hover': {
                        borderColor: 'warning.main',
                        bgcolor: 'warning.main',
                        color: 'warning.contrastText',
                      }
                    }}
                  >
                    Open /readyz
                  </Button>
                </Stack>

                {/* Monitoring Tools Section */}
                <Box sx={{ mt: 4 }}>
                  <Typography 
                    variant="subtitle2" 
                    fontWeight={600}
                    sx={{ 
                      mb: 2, 
                      color: 'text.primary',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    <DashboardIcon sx={{ fontSize: 16 }} />
                    Monitoring Tools
                  </Typography>
                  
                  <Stack direction={{ xs: 'column', sm: 'row', lg: 'column' }} spacing={2}>
                    <Button 
                      variant="contained" 
                      fullWidth 
                      href={getDashboardUrl('grafana')}
                      target="_blank" 
                      rel="noreferrer"
                      sx={{
                        background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
                        py: 1.5,
                        fontWeight: 600,
                        '&:hover': {
                          background: 'linear-gradient(135deg, #3d97ff 0%, #2dc687 100%)',
                          transform: 'translateY(-1px)',
                          boxShadow: '0 4px 12px rgba(78, 168, 255, 0.3)',
                        }
                      }}
                    >
                      📊 Grafana Dashboard
                    </Button>
                    <Button 
                      variant="contained" 
                      fullWidth 
                      href={getPrometheusBaseUrl()}
                      target="_blank" 
                      rel="noreferrer"
                      sx={{
                        background: 'linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%)',
                        py: 1.5,
                        fontWeight: 600,
                        '&:hover': {
                          background: 'linear-gradient(135deg, #ff5252 0%, #ff9800 100%)',
                          transform: 'translateY(-1px)',
                          boxShadow: '0 4px 12px rgba(255, 107, 107, 0.3)',
                        }
                      }}
                    >
                      📈 Prometheus Metrics
                    </Button>
                    <Button 
                      variant="contained" 
                      fullWidth 
                      href={`${getPrometheusBaseUrl()}/alerts`}
                      target="_blank" 
                      rel="noreferrer"
                      startIcon={<NotificationsIcon />}
                      sx={{
                        background: 'linear-gradient(135deg, #ff9800 0%, #ff5722 100%)',
                        py: 1.5,
                        fontWeight: 600,
                        '&:hover': {
                          background: 'linear-gradient(135deg, #f57c00 0%, #e64a19 100%)',
                          transform: 'translateY(-1px)',
                          boxShadow: '0 4px 12px rgba(255, 152, 0, 0.3)',
                        }
                      }}
                    >
                      🚨 Active Alerts
                    </Button>

                  </Stack>
                  
                  <Box 
                    sx={{ 
                      mt: 2,
                      p: 2,
                      borderRadius: 2,
                      bgcolor: 'rgba(78, 168, 255, 0.1)',
                      border: '1px solid',
                      borderColor: 'primary.main',
                    }}
                  >
                    <Typography 
                      variant="body2" 
                      color="primary.main" 
                      sx={{ 
                        fontSize: '0.75rem',
                        lineHeight: 1.5,
                        fontWeight: 500,
                      }}
                    >
                      🔍 Monitor your WebSocket application in real-time with Grafana dashboards and Prometheus metrics
                    </Typography>
                  </Box>
                  
                  {/* Advanced Monitoring Tools */}
                  <Box sx={{ mt: 3 }}>
                    <Typography 
                      variant="subtitle2" 
                      fontWeight={600}
                      sx={{ 
                        mb: 2, 
                        color: 'text.primary',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                      }}
                    >
                      <BugReportIcon sx={{ fontSize: 16 }} />
                      Advanced Monitoring
                    </Typography>
                    
                    <Stack direction={{ xs: 'column', sm: 'row', lg: 'column' }} spacing={2}>
                      <Button 
                        variant="outlined" 
                        fullWidth 
                        href="http://localhost:9093"
                        target="_blank" 
                        rel="noreferrer"
                        startIcon={<NotificationsIcon />}
                        sx={{
                          borderColor: 'warning.main',
                          color: 'warning.main',
                          py: 1.5,
                          fontWeight: 600,
                          '&:hover': {
                            borderColor: 'warning.main',
                            bgcolor: 'warning.main',
                            color: 'warning.contrastText',
                          }
                        }}
                      >
                        🔔 Alertmanager
                      </Button>
                      <Button 
                        variant="outlined" 
                        fullWidth 
                        href="http://localhost:9090/targets"
                        target="_blank" 
                        rel="noreferrer"
                        sx={{
                          borderColor: 'info.main',
                          color: 'info.main',
                          py: 1.5,
                          fontWeight: 600,
                          '&:hover': {
                            borderColor: 'info.main',
                            bgcolor: 'info.main',
                            color: 'info.contrastText',
                          }
                        }}
                      >
                        🎯 Prometheus Targets
                      </Button>
                      <Button 
                        variant="outlined" 
                        fullWidth 
                        href="http://localhost:9090/rules"
                        target="_blank" 
                        rel="noreferrer"
                        sx={{
                          borderColor: 'secondary.main',
                          color: 'secondary.main',
                          py: 1.5,
                          fontWeight: 600,
                          '&:hover': {
                            borderColor: 'secondary.main',
                            bgcolor: 'secondary.main',
                            color: 'secondary.contrastText',
                          }
                        }}
                      >
                        📋 Alert Rules
                      </Button>
                    </Stack>
                  </Box>
                </Box>
                
                <Box 
                  sx={{ 
                    mt: 3,
                    p: 2,
                    borderRadius: 2,
                    bgcolor: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ 
                      fontSize: '0.75rem',
                      lineHeight: 1.5,
                      fontWeight: 500,
                    }}
                  >
                    💡 Tip: Run blue/green deployments with "make promote" command for zero-downtime updates
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Container>
        

      </Box>
    </ThemeProvider>
  )
}
