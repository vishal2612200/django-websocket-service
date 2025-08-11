import React, { useEffect, useState } from 'react'
import Paper from '@mui/material/Paper'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import Tooltip from '@mui/material/Tooltip'
import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'

import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import RefreshIcon from '@mui/icons-material/Refresh'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import SendIcon from '@mui/icons-material/Send'
import ChatIcon from '@mui/icons-material/Chat'
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart'
import ClearIcon from '@mui/icons-material/Clear'
import { useTheme } from '@mui/material/styles'
import useWebSocket from '../hooks/useWebSocket'
import HeartbeatMonitor from './HeartbeatMonitor'

export type SessionCardProps = { 
  id: string; 
  autoReconnect: boolean; 
  persistMessages: boolean; 
  sessionPersistenceType: 'localStorage' | 'redis' | 'none'; 
  onRemove: (id: string) => void;
}

export default function SessionCard({ id, autoReconnect, persistMessages, sessionPersistenceType, onRemove }: SessionCardProps) {
  const [text, setText] = useState('')
  const [activeTab, setActiveTab] = useState(0)
  const [messagesLoaded, setMessagesLoaded] = useState(false)
  const { status, messages, heartbeats, count, send, reconnect, lastHeartbeatAt, nextRetryMs, clearPersistedMessages, refreshMessages } = useWebSocket('/ws/chat/', autoReconnect, id, persistMessages, sessionPersistenceType)
  const theme = useTheme()
  const stateColor = status === 'open' ? theme.palette.success.main : status === 'connecting' ? theme.palette.warning.main : theme.palette.error.main
  const [pulse, setPulse] = useState(false)
  
  useEffect(() => {
    if (lastHeartbeatAt) {
      setPulse(true)
      const t = setTimeout(() => setPulse(false), 600)
      return () => clearTimeout(t)
    }
  }, [lastHeartbeatAt])

  // Track when messages are loaded from persistence
  useEffect(() => {
    if (messages.length > 0 && !messagesLoaded) {
      setMessagesLoaded(true)
      console.log(`Messages loaded for session ${id}: ${messages.length} messages`)
    }
  }, [messages, messagesLoaded, id])
  
  const short = id.length > 50 ? `${id.slice(0, 8)}…${id.slice(-4)}` : id

  return (
    <Paper 
      elevation={0}
      sx={{
        p: 3,
        borderRadius: 3,
        border: '1px solid',
        borderColor: status === 'open' ? 'success.main' : status === 'connecting' ? 'warning.main' : 'error.main',
        background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${theme.palette.background.default} 100%)`,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.1)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 8px 30px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.15)',
        },
        position: 'relative',
        overflow: 'visible', // Changed from 'hidden' to allow notifications to show
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: `linear-gradient(90deg, ${stateColor} 0%, ${stateColor}80 100%)`,
        }
      }}
    >
      {/* Enhanced Header Section */}
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          mb: 3,
          pb: 2,
          borderBottom: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Box display="flex" alignItems="center" gap={2}>
          <Box 
            sx={{ 
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 40,
              height: 40,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
              color: 'white',
            }}
          >
            <ChatIcon sx={{ fontSize: 20 }} />
          </Box>
          <Box>
            <Typography 
              variant="h6" 
              fontWeight={600}
              sx={{ 
                color: 'text.primary',
                fontSize: { xs: '1rem', sm: '1.125rem' },
                mb: 0.5,
              }}
            >
              WebSocket Session
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ 
                fontSize: '0.75rem',
                fontWeight: 500,
              }}
            >
              Real-time messaging connection
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" alignItems="center" gap={1}>
          <Chip
            size="small"
            label={`${count} messages`}
            variant="outlined"
            sx={{
              borderColor: 'divider',
              color: 'text.secondary',
              fontSize: '0.75rem',
              height: 24,
              fontWeight: 600,
              '& .MuiChip-label': {
                px: 1.5,
              }
            }}
          />
          <Tooltip title="Copy Session ID">
            <IconButton 
              size="small" 
              onClick={() => navigator.clipboard.writeText(id)}
              sx={{
                borderRadius: 2,
                width: 32,
                height: 32,
                color: 'text.secondary',
                '&:hover': {
                  bgcolor: 'action.hover',
                  color: 'text.primary',
                }
              }}
            >
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Reconnect">
            <IconButton 
              size="small" 
              onClick={() => reconnect()}
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
          <Tooltip title="Remove Session">
            <IconButton 
              size="small" 
              onClick={() => onRemove(id)}
              sx={{
                borderRadius: 2,
                width: 32,
                height: 32,
                color: 'text.secondary',
                '&:hover': {
                  bgcolor: 'error.main',
                  color: 'error.contrastText',
                }
              }}
            >
              <DeleteOutlineIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Session Info Section */}
      <Box sx={{ mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <Chip 
            size="large" 
            label={short} 
            title={id}
            sx={{
              borderRadius: 2,
              fontWeight: 600,
              fontSize: '0.75rem',
              height: 24,
              bgcolor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid',
              borderColor: 'divider',
              '& .MuiChip-label': {
                px: 1.5,
              }
            }}
          />
          <Box 
            component="span" 
            sx={{ 
              width: 12, 
              height: 12, 
              borderRadius: '50%', 
              bgcolor: stateColor,
              boxShadow: `0 0 0 2px ${stateColor}20`,
              animation: pulse ? 'pulse 0.6s ease-in-out' : 'none',
              '@keyframes pulse': {
                '0%': { transform: 'scale(1)', opacity: 1 },
                '50%': { transform: 'scale(1.2)', opacity: 0.7 },
                '100%': { transform: 'scale(1)', opacity: 1 },
              }
            }} 
            aria-label={`status: ${status}`} 
          />
          <Chip
            size="small"
            label={status}
            sx={{
              borderRadius: 2,
              fontSize: '0.75rem',
              height: 20,
              bgcolor: `${stateColor}20`,
              color: stateColor,
              fontWeight: 600,
              '& .MuiChip-label': {
                px: 1,
              }
            }}
          />
          {sessionPersistenceType === 'redis' && (
            <>
              <Chip
                size="small"
                label="Redis"
                sx={{
                  borderRadius: 2,
                  fontSize: '0.65rem',
                  height: 18,
                  bgcolor: 'warning.main',
                  color: 'warning.contrastText',
                  fontWeight: 600,
                  '& .MuiChip-label': {
                    px: 0.5,
                  }
                }}
              />
              {/* <Tooltip title="Refresh Redis Messages">
                <IconButton 
                  size="small" 
                  onClick={refreshMessages}
                  sx={{
                    borderRadius: 2,
                    width: 24,
                    height: 24,
                    color: 'warning.main',
                    '&:hover': {
                      bgcolor: 'warning.main',
                      color: 'warning.contrastText',
                    }
                  }}
                >
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Tooltip> */}
            </>
          )}
          {sessionPersistenceType === 'localStorage' && (
            <Chip
              size="small"
              label="localStorage"
              sx={{
                borderRadius: 2,
                fontSize: '0.65rem',
                height: 18,
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                fontWeight: 600,
                '& .MuiChip-label': {
                  px: 0.5,
                }
              }}
            />
          )}
        </Stack>
      </Box>

      {/* Tab Navigation */}
      <Box sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{
            '& .MuiTab-root': {
              minHeight: 40,
              fontSize: '0.875rem',
              fontWeight: 600,
              textTransform: 'none',
              color: 'text.secondary',
              '&.Mui-selected': {
                color: 'primary.main',
              }
            },
            '& .MuiTabs-indicator': {
              backgroundColor: 'primary.main',
              height: 3,
              borderRadius: '3px 3px 0 0',
            }
          }}
        >
          <Tab 
            label="Chat" 
            icon={<ChatIcon sx={{ fontSize: 16 }} />} 
            iconPosition="start"
          />
          <Tab 
            label="Heartbeat" 
            icon={<MonitorHeartIcon sx={{ fontSize: 16 }} />} 
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {activeTab === 0 && (
        <>
          {/* Enhanced Message Input Section */}
          <Box sx={{ mb: 3 }}>
            <Typography 
              variant="subtitle2" 
              fontWeight={600}
              sx={{ mb: 2, color: 'text.primary' }}
            >
              Send Message
            </Typography>
            <Stack 
              direction={{ xs: 'column', sm: 'row' }} 
              spacing={2} 
              alignItems={{ xs: 'stretch', sm: 'flex-end' }}
            >
              <TextField 
                fullWidth 
                multiline 
                minRows={1} 
                maxRows={3} 
                placeholder="Type your message…" 
                size="medium" 
                value={text} 
                onChange={(e) => setText(e.target.value)}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    fontSize: '0.875rem',
                    '&:hover .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'primary.main',
                    },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'primary.main',
                      borderWidth: 2,
                    }
                  }
                }}
              />
              <Stack direction="row" spacing={1} justifyContent="flex-end">
                <Button 
                  variant="contained" 
                  endIcon={<SendIcon />} 
                  disabled={!text.trim() || status !== 'open'} 
                  onClick={() => { if (text.trim()) { send(text); setText('') } }}
                  sx={{
                    background: 'linear-gradient(135deg, #4ea8ff 0%, #3ddc97 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #3d97ff 0%, #2dc687 100%)',
                    },
                    '&:disabled': {
                      background: 'rgba(255, 255, 255, 0.12)',
                      color: 'text.disabled',
                    }
                  }}
                >
                  Send
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => setText('')}
                  sx={{
                    borderColor: 'divider',
                    color: 'text.secondary',
                    '&:hover': {
                      borderColor: 'text.primary',
                      bgcolor: 'action.hover',
                    }
                  }}
                >
                  Clear
                </Button>
              </Stack>
            </Stack>
          </Box>

          {/* Enhanced Messages Section */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography 
                  variant="subtitle2" 
                  fontWeight={600}
                  sx={{ color: 'text.primary' }}
                >
                  Message History
                </Typography>
                {messagesLoaded && messages.length > 0 && (
                  <Chip 
                    label={`${messages.length} loaded`}
                    size="small"
                    variant="outlined"
                    sx={{
                      fontSize: '0.75rem',
                      height: 20,
                      bgcolor: 'success.main',
                      color: 'success.contrastText',
                      borderColor: 'success.main',
                      '& .MuiChip-label': {
                        px: 1,
                      }
                    }}
                  />
                )}
              </Box>
              {messages.length > 0 && (
                <Tooltip title="Clear all messages">
                  <IconButton 
                    size="small" 
                    onClick={clearPersistedMessages}
                    sx={{
                      borderRadius: 2,
                      width: 32,
                      height: 32,
                      color: 'text.secondary',
                      '&:hover': {
                        bgcolor: 'error.main',
                        color: 'error.contrastText',
                      }
                    }}
                  >
                    <ClearIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
            <Box 
              component="ul" 
              sx={{ 
                listStyle: 'none', 
                p: 0, 
                m: 0, 
                display: 'grid', 
                gap: 1, 
                maxHeight: 200, 
                overflow: 'auto', 
                '&::-webkit-scrollbar': {
                  width: 6,
                },
                '&::-webkit-scrollbar-track': {
                  background: 'transparent',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: 3,
                },
                '&::-webkit-scrollbar-thumb:hover': {
                  background: 'rgba(255, 255, 255, 0.2)',
                }
              }}
            >
              {messages.length === 0 ? (
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
                  No messages yet
                </Box>
              ) : (
                messages.map((m: any, idx: number) => {
                  // Determine styling based on message type
                  const isBroadcast = m.isBroadcast
                  const broadcastLevel = m.broadcastLevel
                  
                  // Get colors based on broadcast level
                  const getBroadcastColors = (level: string) => {
                    switch (level) {
                      case 'info': return { bg: 'primary.main', border: 'primary.main', text: 'primary.contrastText' }
                      case 'warning': return { bg: 'warning.main', border: 'warning.main', text: 'warning.contrastText' }
                      case 'error': return { bg: 'error.main', border: 'error.main', text: 'error.contrastText' }
                      case 'success': return { bg: 'success.main', border: 'success.main', text: 'success.contrastText' }
                      default: return { bg: 'primary.main', border: 'primary.main', text: 'primary.contrastText' }
                    }
                  }
                  
                  const colors = isBroadcast ? getBroadcastColors(broadcastLevel) : {
                    bg: m.isSent ? 'primary.main' : 'action.hover',
                    border: m.isSent ? 'primary.main' : 'divider',
                    text: m.isSent ? 'primary.contrastText' : 'text.primary'
                  }
                  
                  return (
                    <Box 
                      component="li" 
                      key={m.id || idx} 
                      sx={{ 
                        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', 
                        fontSize: 13, 
                        bgcolor: colors.bg,
                        color: colors.text,
                        border: '1px solid', 
                        borderColor: colors.border, 
                        px: 2, 
                        py: 1.5, 
                        borderRadius: 2,
                        transition: 'all 0.2s ease',
                        position: 'relative',
                        fontWeight: isBroadcast ? 600 : 400,
                        '&:hover': {
                          bgcolor: isBroadcast ? colors.bg : (m.isSent ? 'primary.dark' : 'action.selected'),
                          borderColor: isBroadcast ? colors.border : (m.isSent ? 'primary.dark' : 'primary.main'),
                        },
                        '&::before': m.isSent ? {
                          content: '"→"',
                          position: 'absolute',
                          left: -8,
                          top: '50%',
                          transform: 'translateY(-50%)',
                          fontSize: '0.75rem',
                          color: 'primary.main',
                          fontWeight: 'bold',
                        } : (isBroadcast ? {
                          content: '"📢"',
                          position: 'absolute',
                          left: -8,
                          top: '50%',
                          transform: 'translateY(-50%)',
                          fontSize: '0.75rem',
                          color: colors.text,
                          fontWeight: 'bold',
                        } : {})
                      }}
                    >
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          fontSize: '0.65rem', 
                          opacity: 0.7,
                          color: m.isSent ? 'primary.contrastText' : 'text.secondary'
                        }}
                      >
                        {m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : ''}
                      </Typography>
                      <Box sx={{ fontSize: 'inherit' }}>
                        {m.content || m}
                      </Box>
                    </Box>
                  </Box>
                )
              })
            )}
            </Box>
          </Box>
        </>
      )}

      {activeTab === 1 && (
        <HeartbeatMonitor
          heartbeats={heartbeats}
          lastHeartbeatAt={lastHeartbeatAt}
          status={status}
          onRefresh={reconnect}
        />
      )}

      {/* Enhanced Footer Section */}
      <Box 
        sx={{ 
          pt: 2,
          borderTop: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 1
        }}
      >
        <Typography 
          variant="caption" 
          color="text.secondary" 
          sx={{ 
            fontSize: '0.75rem',
            display: 'flex',
            gap: 2,
            flexWrap: 'wrap',
            fontWeight: 500,
          }}
        >
          <span>Last heartbeat: {lastHeartbeatAt ? `${Math.max(0, Math.floor((Date.now() - lastHeartbeatAt) / 1000))}s` : '—'}</span>
          <span>Next retry: {status !== 'open' ? (nextRetryMs ? `${Math.round(nextRetryMs / 100) / 10}s` : '—') : '—'}</span>
        </Typography>
      </Box>
      

    </Paper>
  )
}


