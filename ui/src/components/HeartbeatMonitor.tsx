import React, { useEffect, useState, useMemo } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import Chip from '@mui/material/Chip'
import Stack from '@mui/material/Stack'
import LinearProgress from '@mui/material/LinearProgress'
import Tooltip from '@mui/material/Tooltip'
import IconButton from '@mui/material/IconButton'
import RefreshIcon from '@mui/icons-material/Refresh'
import TimelineIcon from '@mui/icons-material/Timeline'
import SignalCellularAltIcon from '@mui/icons-material/SignalCellularAlt'
import WarningIcon from '@mui/icons-material/Warning'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import { useTheme } from '@mui/material/styles'
import Grid from '@mui/material/Grid'

export interface HeartbeatData {
  timestamp: string
  receivedAt: number
  latency?: number
}

interface HeartbeatMonitorProps {
  heartbeats: string[]
  lastHeartbeatAt: number | null
  status: 'connecting' | 'open' | 'closed'
  onRefresh?: () => void
}

export default function HeartbeatMonitor({ 
  heartbeats, 
  lastHeartbeatAt, 
  status, 
  onRefresh 
}: HeartbeatMonitorProps) {
  const theme = useTheme()
  const [currentTime, setCurrentTime] = useState(Date.now())
  
  // Update current time every second for real-time calculations
  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(Date.now()), 1000)
    return () => clearInterval(interval)
  }, [])

  // Process heartbeat data with latency calculations
  const heartbeatData = useMemo(() => {
    return heartbeats.map((heartbeatStr, index) => {
      try {
        const heartbeat = JSON.parse(heartbeatStr)
        const timeSinceReceived = currentTime - heartbeat.receivedAt
        
        return {
          timestamp: heartbeat.timestamp,
          receivedAt: heartbeat.receivedAt,
          latency: heartbeat.latency || 0,
          isRecent: timeSinceReceived < 35000, // Consider heartbeats within 35s as recent
          isStale: timeSinceReceived > 60000, // Consider heartbeats older than 60s as stale
        }
      } catch (error) {
        // Fallback for old format
        const timestamp = parseInt(heartbeatStr)
        const receivedAt = timestamp
        const latency = currentTime - receivedAt
        
        return {
          timestamp: heartbeatStr,
          receivedAt,
          latency: Math.max(0, latency),
          isRecent: latency < 35000,
          isStale: latency > 60000,
        }
      }
    }).slice(0, 10) // Show last 10 heartbeats
  }, [heartbeats, currentTime])

  // Calculate heartbeat statistics
  const stats = useMemo(() => {
    if (heartbeatData.length === 0) return null
    
    const recentHeartbeats = heartbeatData.filter(h => h.isRecent)
    const avgLatency = heartbeatData.reduce((sum, h) => sum + (h.latency || 0), 0) / heartbeatData.length
    const missedHeartbeats = Math.max(0, Math.floor((currentTime - (lastHeartbeatAt || currentTime)) / 30000) - 1)
    
    return {
      total: heartbeatData.length,
      recent: recentHeartbeats.length,
      avgLatency: Math.round(avgLatency), // Keep in milliseconds
      missed: missedHeartbeats,
      health: recentHeartbeats.length > 0 ? 'healthy' : 'warning' as const,
      nextExpected: lastHeartbeatAt ? lastHeartbeatAt + 30000 : null,
      timeUntilNext: lastHeartbeatAt ? Math.max(0, (lastHeartbeatAt + 30000) - currentTime) : null,
    }
  }, [heartbeatData, lastHeartbeatAt, currentTime])

  // Calculate progress for next heartbeat
  const heartbeatProgress = useMemo(() => {
    if (!stats?.nextExpected || !lastHeartbeatAt) return 0
    const totalInterval = 30000 // 30 seconds
    const elapsed = currentTime - lastHeartbeatAt
    return Math.min(100, (elapsed / totalInterval) * 100)
  }, [stats?.nextExpected, lastHeartbeatAt, currentTime])

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return theme.palette.success.main
      case 'warning': return theme.palette.warning.main
      default: return theme.palette.error.main
    }
  }

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy': return <CheckCircleIcon fontSize="small" />
      case 'warning': return <WarningIcon fontSize="small" />
      default: return <WarningIcon fontSize="small" />
    }
  }

  return (
    <Paper 
      elevation={0}
      sx={{
        p: 3,
        borderRadius: 3,
        border: '1px solid',
        borderColor: 'divider',
        background: 'rgba(255, 255, 255, 0.02)',
        backdropFilter: 'blur(10px)',
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box 
            sx={{ 
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 40,
              height: 40,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #3ddc97 0%, #4ea8ff 100%)',
              color: 'white',
            }}
          >
            <SignalCellularAltIcon sx={{ fontSize: 20 }} />
          </Box>
          <Box>
            <Typography 
              variant="h6" 
              fontWeight={600}
              sx={{ color: 'text.primary', mb: 0.5 }}
            >
              Heartbeat Monitor
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ fontSize: '0.75rem', fontWeight: 500 }}
            >
              Real-time connection health tracking
            </Typography>
          </Box>
        </Box>
        
        {onRefresh && (
          <Tooltip title="Refresh heartbeat data">
            <IconButton 
              size="small" 
              onClick={onRefresh}
              sx={{
                borderRadius: 2,
                width: 32,
                height: 32,
                color: 'text.secondary',
                '&:hover': {
                  bgcolor: 'action.hover',
                  color: 'primary.main',
                }
              }}
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Health Status */}
      {stats && (
        <Box sx={{ mb: 3 }}>
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
            <Chip
              size="small"
              icon={getHealthIcon(stats.health)}
              label={stats.health === 'healthy' ? 'Healthy' : 'Warning'}
              sx={{
                borderRadius: 2,
                fontSize: '0.75rem',
                height: 24,
                bgcolor: `${getHealthColor(stats.health)}20`,
                color: getHealthColor(stats.health),
                fontWeight: 600,
                '& .MuiChip-label': { px: 1.5 },
              }}
            />
            <Chip
              size="small"
              label={`${stats.recent}/${stats.total} recent`}
              variant="outlined"
              sx={{
                borderRadius: 2,
                fontSize: '0.75rem',
                height: 24,
                borderColor: 'divider',
                color: 'text.secondary',
                fontWeight: 600,
                '& .MuiChip-label': { px: 1.5 },
              }}
            />
            {stats.missed > 0 && (
              <Chip
                size="small"
                label={`${stats.missed} missed`}
                sx={{
                  borderRadius: 2,
                  fontSize: '0.75rem',
                  height: 24,
                  bgcolor: 'error.main',
                  color: 'error.contrastText',
                  fontWeight: 600,
                  '& .MuiChip-label': { px: 1.5 },
                }}
              />
            )}
          </Stack>

          {/* Next Heartbeat Progress */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                Next heartbeat
              </Typography>
              <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.75rem' }}>
                {stats.timeUntilNext ? `${Math.round(stats.timeUntilNext / 1000)}s` : '—'}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={heartbeatProgress}
              sx={{
                height: 6,
                borderRadius: 3,
                bgcolor: 'rgba(255, 255, 255, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 3,
                  background: 'linear-gradient(90deg, #3ddc97 0%, #4ea8ff 100%)',
                }
              }}
            />
          </Box>

          {/* Statistics Grid */}
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: 'rgba(255, 255, 255, 0.05)' }}>
                <Typography variant="h6" fontWeight={700} sx={{ color: 'text.primary', mb: 0.5 }}>
                  {stats.avgLatency ? Math.round(stats.avgLatency) : 0}ms
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                  Avg Latency (ms)
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: 'rgba(255, 255, 255, 0.05)' }}>
                <Typography variant="h6" fontWeight={700} sx={{ color: 'text.primary', mb: 0.5 }}>
                  {stats.total}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                  Total Received
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Recent Heartbeats Timeline */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <TimelineIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="subtitle2" fontWeight={600} sx={{ color: 'text.primary' }}>
            Recent Heartbeats
          </Typography>
        </Box>
        
        {heartbeatData.length === 0 ? (
          <Box 
            sx={{ 
              textAlign: 'center', 
              py: 4,
              color: 'text.secondary',
              fontSize: '0.875rem',
              bgcolor: 'rgba(255, 255, 255, 0.02)',
              borderRadius: 2,
              border: '1px dashed',
              borderColor: 'divider',
            }}
          >
            No heartbeats received yet
          </Box>
        ) : (
          <Box 
            sx={{ 
              maxHeight: 200, 
              overflow: 'auto',
              '&::-webkit-scrollbar': {
                width: 6,
              },
              '&::-webkit-scrollbar-track': {
                background: 'transparent',
              },
              '&::-webkit-scrollbar-thumb': {
                background: 'rgba(255, 255, 255, 0.8)',
                borderRadius: 3,
              },
              '&::-webkit-scrollbar-thumb:hover': {
                background: 'rgba(255, 255, 255, 1)',
              }
            }}
          >
            <Stack spacing={1}>
              {heartbeatData.map((heartbeat, index) => (
              <Box 
                key={index}
                sx={{ 
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: heartbeat.isStale ? 'error.main' : 'success.main',
                  opacity: heartbeat.isStale ? 0.7 : 0.8,
                  border: '1px solid',
                  borderColor: heartbeat.isStale ? 'error.main' : 'success.main',
                  borderOpacity: 0.8,
                  backdropFilter: 'blur(4px)',
                }}
              >
                <Box>
                                                    <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.75rem', color: 'white', textShadow: '0 0 2px rgba(0,0,0,0.8)' }}>
                    {new Date(parseInt(heartbeat.timestamp)).toLocaleTimeString()}
                  </Typography>
                                  <Typography variant="caption" sx={{ fontSize: '0.65rem', color: 'white', opacity: 0.9, textShadow: '0 0 2px rgba(0,0,0,0.8)' }}>
                    {Math.round(heartbeat.latency)}ms latency
                  </Typography>
                </Box>
                <Chip
                  size="small"
                  label={heartbeat.isStale ? 'Stale' : heartbeat.isRecent ? 'Recent' : 'Old'}
                  sx={{
                    borderRadius: 1,
                    fontSize: '0.65rem',
                    height: 18,
                    bgcolor: heartbeat.isStale ? 'error.main' : heartbeat.isRecent ? 'success.main' : 'warning.main',
                    color: 'white',
                    fontWeight: 600,
                    '& .MuiChip-label': { px: 1 },
                  }}
                />
              </Box>
            ))}
            </Stack>
          </Box>
        )}
      </Box>

      {/* Connection Status */}
      <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
          Connection: {status} • Last heartbeat: {lastHeartbeatAt ? `${Math.max(0, Math.floor((currentTime - lastHeartbeatAt) / 1000))}s ago` : 'Never'}
        </Typography>
      </Box>
    </Paper>
  )
}
